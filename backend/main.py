from fastapi import FastAPI, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import logging

from auth_routes import router as auth_router
from routes.dashboard import router as dashboard_router
from routes.profiles import router as profile_router
from routes.integrations import router as integrations_router
from routes.users import router as users_router
from integrations.google_auth import google_auth_url, google_auth_callback, get_google_user_info

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="VectorShift API")

# Enable CORS for development
origins = [
    "http://localhost:3000",  # Next.js frontend
    "http://localhost:8000",  # Backend
    "https://api.notion.com",  # Notion API
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with correct prefixes
app.include_router(auth_router, prefix="/auth", tags=["authentication"])
app.include_router(dashboard_router, prefix="/api", tags=["dashboard"])
app.include_router(profile_router, prefix="/api", tags=["profiles"])
app.include_router(integrations_router, tags=["integrations"])  # No prefix since it's included in the router
app.include_router(users_router, prefix="/api/users", tags=["users"])

@app.get('/')
async def root():
    return {"status": "healthy", "message": "VectorShift API is running"}

@app.get('/auth/google/url')
async def get_google_auth_url():
    auth_url = await google_auth_url()
    return {"url": auth_url}

@app.get('/auth/google/callback')
async def google_callback(request: Request):
    return await google_auth_callback(request)

@app.get('/api/auth/google/user')
async def get_user_info(token: str):
    return await get_google_user_info(token)