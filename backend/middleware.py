from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
import jwt
from redis_client import get_value_redis
import os

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        exclude_paths=None
    ):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/auth/google/callback",
            "/auth/login",
            "/auth/signup",
            "/auth/google/url",
            "/api/integrations/notion/oauth2callback",
            "/api/integrations/airtable/oauth2callback",
            "/api/integrations/slack/oauth2callback",
            "/api/integrations/hubspot/oauth2callback",
            "/integrations/notion/oauth2callback",
            "/integrations/airtable/oauth2callback",
            "/integrations/slack/oauth2callback",
            "/integrations/hubspot/oauth2callback",
            "/",
        ]

    async def dispatch(self, request: Request, call_next):
        # Skip auth for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            response = await call_next(request)
            return response

        # Check for token
        try:
            auth = request.headers.get('Authorization')
            if not auth or not auth.startswith('Bearer '):
                raise HTTPException(
                    status_code=401,
                    detail="Missing authentication token",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            token = auth.split(' ')[1]
            user_data = await get_value_redis(f"user_token:{token}")

            if not user_data:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid or expired token",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Add user data to request state
            request.state.user = user_data
            
            response = await call_next(request)
            return response

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=401,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=401,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

def add_cors_middleware(app):
    """Add CORS middleware with configuration"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",  # Next.js frontend default port
            "http://localhost:3001",  # Next.js frontend alternate port
            "http://localhost:8000",  # Backend
            "https://api.notion.com",  # Notion API
            "http://127.0.0.1:3000",  # Local frontend alternative
            "http://127.0.0.1:3001",  # Local frontend alternative
            "null",  # Allow requests from popup windows
        ],
        allow_credentials=True,
        allow_methods=["*"],  # Allow all methods
        allow_headers=[
            "Content-Type",
            "Authorization",
            "Accept",
            "Origin",
            "X-Requested-With",
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Credentials",
        ],
        expose_headers=["*"],
        max_age=3600,
    )

def setup_middleware(app):
    """Setup all middleware"""
    # Add CORS middleware first
    add_cors_middleware(app)
    # Then add authentication middleware
    app.add_middleware(AuthMiddleware)
