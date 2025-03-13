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

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Include routers with correct prefixes
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(dashboard_router, prefix="/api", tags=["dashboard"])
app.include_router(profile_router, prefix="/api", tags=["profiles"])
# Since integration routes already include /integrations in their paths, we just need /api prefix
app.include_router(integrations_router, prefix="/api", tags=["integrations"])

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

@app.get('/api/auth/google/user')
async def get_user_info(token: str):
    return await get_google_user_info(token)