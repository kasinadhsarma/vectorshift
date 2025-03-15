# MIT License
# Copyright (c) 2023 VectorShift
# This file is part of the VectorShift project and is licensed under the MIT License.

from datetime import datetime, timedelta
import logging
import httpx
import os
import json
from fastapi import Depends, HTTPException, status, Request, APIRouter, Form, FastAPI
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer
from google.oauth2 import id_token
from google.auth.transport import requests
from cassandra.concurrent import execute_concurrent_with_args
from cassandra.cqlengine.query import BatchQuery
from cassandra.query import dict_factory
from cassandra_client import CassandraClient
from models.users import User, UserProfile, PasswordResetToken # Add other models as needed
from config import settings
from dotenv import load_dotenv

# Explicitly import PyJWT
import jwt

load_dotenv()

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auth")

# OAuth2 Setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
router = APIRouter()

async def add_cassandra_connection(app: FastAPI):
    """Add Cassandra connection to FastAPI app"""
    app.state.cassandra_client = CassandraClient()
    await app.state.cassandra_client.connect()
    
    @app.on_event("shutdown")
    async def shutdown_event():
        await app.state.cassandra_client.close()

# Get cassandra client from app state
def get_cassandra_client(request: Request) -> CassandraClient:
    return request.app.state.cassandra_client

# Google Auth Configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8000/auth/google/callback')

async def create_user_profile(request: Request, user_id: str, email: str, google_id: str, username: str):
    cassandra_client = get_cassandra_client(request)
    session = cassandra_client.session
    """Creates a user profile in Cassandra."""
    try:
        query = "INSERT INTO user_profiles (user_id, email, google_id, username) VALUES (%s, %s, %s, %s)"
        parameters = [(user_id, email, google_id, username)]
        execute_concurrent_with_args(session, query, parameters, concurrency=10)
        return True
    except Exception as e:
        logger.error(f"Error creating user profile: {e}")
        raise

async def get_user_by_email(request: Request, email: str):
    cassandra_client = get_cassandra_client(request)
    session = cassandra_client.session
    # Set the row factory to dict_factory to convert Row to dict
    session.row_factory = dict_factory
    """Retrieves a user by email."""
    try:
        query = "SELECT * FROM users WHERE email = %s ALLOW FILTERING"
        result = session.execute(query, [email])
        row = result.one()
        if row:
            # Now row is a dict that can be unpacked into User
            return User(**row)
        return None
    except Exception as e:
        logger.error(f"Error retrieving user: {e}")
        raise

async def update_last_login(request: Request, user_id: str):
    cassandra_client = get_cassandra_client(request)
    session = cassandra_client.session
    """Updates last login timestamp."""
    try:
        query = "UPDATE users SET last_login = %s WHERE email = %s"
        session.execute(query, [datetime.now(), user_id])
    except Exception as e:
        logger.error(f"Error updating last login: {e}")
        raise

async def get_current_user(request: Request, token: str = Depends(oauth2_scheme)):
    """Retrieves the current user from JWT token."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        user_id = payload.get("sub")
        cassandra_client = get_cassandra_client(request)
        return await get_user_by_email(request, user_id)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/google/url")
async def google_auth_url():
    """Returns Google OAuth URL."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google Client ID not configured")
    auth_url = (f"https://accounts.google.com/o/oauth2/v2/auth?client_id={GOOGLE_CLIENT_ID}&"
                f"redirect_uri={GOOGLE_REDIRECT_URI}&response_type=code&scope=openid email profile")
    return {"url": auth_url}

@router.get("/google/callback", response_class=HTMLResponse)
async def google_auth_callback(request: Request, code: str):
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

        user = await get_user_by_email(request, email)
        if not user:
            # Create user if not exists
            # First, create the user in the users table
            cassandra_client = get_cassandra_client(request)
            session = cassandra_client.session
            # Using datetime.now() for the timestamps
            current_time = datetime.now()
            query = """
            INSERT INTO users (email, auth_provider, google_id, created_at, last_login) 
            VALUES (%s, %s, %s, %s, %s)
            """
            session.execute(query, [email, 'google', google_id, current_time, current_time])
            
            # Then create the user profile
            await create_user_profile(request, google_id, email, google_id, idinfo.get('name', ''))
        else:
            await update_last_login(request, email)

        # Use JWT directly
        token = jwt.encode(
            {"sub": email, "exp": datetime.utcnow() + timedelta(hours=24)},
            settings.jwt_secret_key,
            algorithm="HS256"
        )
        
        # Ensure token is a string - PyJWT 2.0+ returns bytes
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        
        # Return HTML that posts a message to the parent window
        return f"""
        <html>
            <body>
                <script>
                    window.opener.postMessage({{
                        token: "{token}",
                        user: {{
                            name: "{idinfo.get('name', '')}",
                            email: "{email}",
                            picture: "{idinfo.get('picture', '')}"
                        }}
                    }}, "*");
                    window.close();
                </script>
            </body>
        </html>
        """
    except Exception as e:
        logger.error(f"OAuth error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/signup")
async def signup(request: Request, email: str = Form(...), password: str = Form(...)):
    if '@' not in email:
        raise HTTPException(status_code=422, detail="Invalid email format")
    if len(password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters long")
    try:
        cassandra_client = get_cassandra_client(request)
        session = cassandra_client.session
        # Changed to use password_hash field instead of password
        session.execute("INSERT INTO users (email, password_hash, auth_provider, created_at) VALUES (%s, %s, %s, %s)",
                        (email, password, 'email', datetime.now()))  # Store plaintext for now, should be hashed in real app
        return {"message": "User created successfully"}
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    if '@' not in email:
        raise HTTPException(status_code=422, detail="Invalid email format")
    try:
        user = await get_user_by_email(request, email)
        if not user or user.password_hash != password:  # Changed from password to password_hash
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Update last login time
        await update_last_login(request, email)
        
        # Use JWT directly
        token = jwt.encode(
            {"sub": email, "exp": datetime.utcnow() + timedelta(hours=24)},
            settings.jwt_secret_key,
            algorithm="HS256"
        )
        
        # Ensure token is a string - PyJWT 2.0+ returns bytes
        if isinstance(token, bytes):
            token = token.decode('utf-8')
            
        # Return with redirect URL
        return {
            "access_token": token, 
            "token_type": "bearer",
            "redirect_url": "/dashboard"  # Add redirect URL to dashboard
        }
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
