import httpx
from fastapi import APIRouter, HTTPException, Depends, FastAPI
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from google.oauth2 import id_token
from google.auth.transport import requests
import os
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv
from cassandra_client import CassandraClient
import logging
from fastapi import Form

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8000/auth/google/callback')

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
cassandra_client = CassandraClient()

@router.get("/google/url")
async def google_auth_url():
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google Client ID not configured")
    
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={GOOGLE_REDIRECT_URI}&"
        "response_type=code&"
        "scope=openid email profile"
    )
    return {"url": auth_url}

# Models
class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    email: str
    auth_provider: str
    google_id: Optional[str] = None

class UserCreate(BaseModel):
    email: str
    password: str

class GoogleAuthRequest(BaseModel):
    code: str

async def connect_to_cassandra():
    """Connect to Cassandra on app startup."""
    try:
        logger.info("Connecting to Cassandra...")
        await cassandra_client.connect()
        logger.info("Connected to Cassandra successfully.")
    except Exception as e:
        logger.error(f"Failed to connect to Cassandra: {e}")
        raise


async def disconnect_from_cassandra():
    """Disconnect from Cassandra on app shutdown."""
    logger.info("Disconnecting from Cassandra...")
    await cassandra_client.close()
    logger.info("Disconnected from Cassandra.")

def add_cassandra_connection(app: FastAPI):
    app.add_event_handler("startup", connect_to_cassandra)
    app.add_event_handler("shutdown", disconnect_from_cassandra)

@router.get("/google/callback")
async def google_auth_callback(code: str):
    logger.info(f"Google OAuth callback initiated with code: {code}")
    if not cassandra_client.session:
        raise HTTPException(status_code=500, detail="Cassandra session not initialized")
    try:
        # 1. Exchange code for token
        token_endpoint = "https://oauth2.googleapis.com/token"
        logger.info(f"Attempting to exchange code for token at: {token_endpoint}")
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                token_endpoint,
                data={
                    "code": code,
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uri": GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code"
                }
            )
        logger.info(f"Token exchange response status: {token_response.status_code}")
        if token_response.status_code != 200:
            logger.error(f"Token exchange failed: {token_response.text}")
            raise HTTPException(status_code=400, detail="Failed to get token from Google")
        token_data = token_response.json()

        # 2. Verify ID token
        logger.info("Verifying ID token...")
        try:
            idinfo = id_token.verify_oauth2_token(
                token_data['id_token'],
                requests.Request(),
                GOOGLE_CLIENT_ID
            )
        except ValueError as e:
            logger.error(f"ID token verification failed: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid ID token: {e}")
        logger.info("ID token verified successfully.")

        # 3. Get user info
        email = idinfo['email']
        google_id = idinfo['sub']
        logger.info(f"User email: {email}, Google ID: {google_id}")

        # 4. Check if user exists
        logger.info(f"Checking if user {email} exists...")
        query = "SELECT email, auth_provider FROM users WHERE email = %s ALLOW FILTERING"
        user_rows = await cassandra_client.session.execute_async(query, [email])
        rows = await user_rows.all()
        user = next(iter(rows), None)

        if not user:
            logger.info(f"User {email} does not exist. Creating new user...")
            # 5. Create new user
            insert_future = await cassandra_client.session.execute_async("""
                INSERT INTO users (email, auth_provider, google_id, created_at, last_login)
                VALUES (%s, %s, %s, %s, %s)
            """, [email, 'google', google_id, datetime.now(), datetime.now()])
            await insert_future.result()
            
            # Create initial profile
            await cassandra_client.create_user_profile(
                email,
                {
                    "fullName": idinfo.get('name', ''),
                    "displayName": idinfo.get('given_name', email.split('@')[0]),
                    "avatarUrl": idinfo.get('picture', '')
                }
            )
        else:
            logger.info(f"User {email} exists. Updating last login...")
            # 6. Update last login
            update_future = await cassandra_client.session.execute_async(
                "UPDATE users SET last_login = %s WHERE email = %s",
                [datetime.now(), email]
            )
            await update_future.result()

        # 7. Generate JWT token
        logger.info("Generating JWT token...")
        token_data = {
            "access_token": cassandra_client._create_access_token({"sub": email}),
            "token_type": "bearer"
        }
        logger.info("JWT token generated successfully.")

        # 8. Return HTML that posts the token to parent window
        logger.info("Creating HTML response...")
        html_content = f"""
        <html>
            <script>
                window.onload = function() {{
                    window.opener.postMessage({{"type": "google-oauth-callback", "success": true, "token": "{token_data['access_token']}"}}, "*");
                    window.close();
                }};
            </script>
            <body>
                Authentication successful! You can close this window.
            </body>
        </html>
        """
        logger.info("Returning HTML response.")
        return HTMLResponse(content=html_content)

    except HTTPException as e:
        logger.error(f"HTTPException caught: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/signup")
async def signup(email: str = Form(...), password: str = Form(...)):
    # Basic validation
    if not email or not '@' in email:
        raise HTTPException(status_code=422, detail="Invalid email format")
    if not password or len(password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters long")
    try:
        await cassandra_client.create_user(email, password)
        return {"message": "User created successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error signing up user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    # Basic validation
    if not email or not '@' in email:
        raise HTTPException(status_code=422, detail="Invalid email format")
    if not password:
        raise HTTPException(status_code=422, detail="Password is required")
    try:
        return await cassandra_client.verify_user(email, password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Error logging in user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
