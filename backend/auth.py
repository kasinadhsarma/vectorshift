# MIT License
# Copyright (c) 2023 VectorShift
# This file is part of the VectorShift project and is licensed under the MIT License.


from datetime import datetime, timedelta
import jwt
import logging
import httpx
import os
import json
from fastapi import Depends, HTTPException, status, Request, APIRouter, Form
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer
from google.oauth2 import id_token
from google.auth.transport import requests
from cassandra.concurrent import execute_concurrent_with_args
from cassandra.cqlengine.query import BatchQuery
from cassandra_client import CassandraClient
from models import User
from config import settings
from dotenv import load_dotenv

load_dotenv()

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auth")

# OAuth2 Setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
router = APIRouter()
cassandra_client = CassandraClient()

# Google Auth Configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8000/auth/google/callback')

async def create_user_profile(session, user_id, email, google_id, username):
    """Creates a user profile in Cassandra."""
    try:
        query = "INSERT INTO user_profiles (user_id, email, google_id, username) VALUES (?, ?, ?, ?)"
        parameters = [(user_id, email, google_id, username)]
        execute_concurrent_with_args(session, query, parameters, concurrency=10)
        return True
    except Exception as e:
        logger.error(f"Error creating user profile: {e}")
        raise

async def get_user_by_email(session, email: str):
    """Retrieves a user by email."""
    try:
        query = "SELECT * FROM users WHERE email = ?"
        result = session.execute(query, [email])
        return User(**result.one()) if result else None
    except Exception as e:
        logger.error(f"Error retrieving user: {e}")
        raise

async def update_last_login(session, user_id):
    """Updates last login timestamp."""
    try:
        query = "UPDATE users SET last_login = toTimestamp(now()) WHERE user_id = ?"
        session.execute(query, [user_id])
    except Exception as e:
        logger.error(f"Error updating last login: {e}")
        raise

async def get_current_user(request: Request, token: str = Depends(oauth2_scheme)):
    """Retrieves the current user from JWT token."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        user_id = payload.get("sub")
        return await get_user_by_user_id(request.app.session, user_id)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/google/url")
async def google_auth_url():
    """Returns Google OAuth URL."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google Client ID not configured")
    auth_url = (f"https://accounts.google.com/o/oauth2/v2/auth?client_id={GOOGLE_CLIENT_ID}&"
                f"redirect_uri={GOOGLE_REDIRECT_URI}&response_type=code&scope=openid email profile")
    return {"url": auth_url}

@router.get("/google/callback")
async def google_auth_callback(code: str):
    """Handles Google OAuth callback."""
    try:
        token_endpoint = "https://oauth2.googleapis.com/token"
        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_endpoint, data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code"
            })
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to retrieve token")
        token_data = token_response.json()
        idinfo = id_token.verify_oauth2_token(token_data['id_token'], requests.Request(), GOOGLE_CLIENT_ID)
        email, google_id = idinfo['email'], idinfo['sub']

        session = cassandra_client.session
        user = await get_user_by_email(session, email)
        if not user:
            await create_user_profile(session, google_id, email, google_id, idinfo.get('name', ''))
        else:
            await update_last_login(session, user.user_id)

        token = jwt.encode({"sub": email, "exp": datetime.utcnow() + timedelta(hours=24)},
                           settings.jwt_secret_key, algorithm="HS256")
        return {"access_token": token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"OAuth error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/signup")
async def signup(email: str = Form(...), password: str = Form(...)):
    if '@' not in email:
        raise HTTPException(status_code=422, detail="Invalid email format")
    if len(password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters long")
    try:
        session = cassandra_client.session
        session.execute("INSERT INTO users (email, password, created_at) VALUES (%s, %s, %s)",
                        (email, password, datetime.utcnow()))
        return {"message": "User created successfully"}
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    if '@' not in email:
        raise HTTPException(status_code=422, detail="Invalid email format")
    try:
        session = cassandra_client.session
        result = session.execute("SELECT * FROM users WHERE email = %s", [email]).one()
        if not result or result['password'] != password:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = jwt.encode({"sub": email, "exp": datetime.utcnow() + timedelta(hours=24)},
                           settings.jwt_secret_key, algorithm="HS256")
        return {"access_token": token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
