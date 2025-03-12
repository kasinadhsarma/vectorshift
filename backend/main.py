from fastapi import FastAPI, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json

from auth_routes import router as auth_router
from routes.dashboard import router as dashboard_router
from routes.profiles import router as profile_router
from routes.integrations import router as integrations_router
from integrations.google_auth import google_auth_url, google_auth_callback, get_google_user_info

app = FastAPI()

origins = [
    "http://localhost:3000",  # Next.js frontend
    "http://localhost:8000",  # Backend
    "https://accounts.google.com",  # Google OAuth
    "null",  # Allow requests from popup windows
]

# Enable CORS with specific configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With"
    ],
    expose_headers=["*"],
    max_age=3600,
)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["authentication"])
app.include_router(dashboard_router, tags=["dashboard"])
app.include_router(profile_router, tags=["profiles"])
app.include_router(integrations_router, tags=["integrations"])

@app.get('/')
def read_root():
    return {'Ping': 'Pong'}


# Google Authentication
@app.get('/auth/google/url')
async def get_google_auth_url():
    auth_url = await google_auth_url()
    return {"url": auth_url}

@app.get('/auth/google/callback')
async def google_callback(request: Request):
    return await google_auth_callback(request)

@app.get('/auth/google/user')
async def get_user_info(token: str):
    return await get_google_user_info(token)
