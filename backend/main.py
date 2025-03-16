from fastapi import FastAPI, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
import json

from auth_routes import router as auth_router
from twofa_routes import router as twofa_router
from routes.dashboard import router as dashboard_router
from routes.profiles import router as profile_router
from routes.integrations import router as integrations_router
from integrations.google_auth import google_auth_url, google_auth_callback, get_google_user_info

app = FastAPI()

# Enable CORS for development
origins = [
    "http://localhost:3000",  # Frontend
    "http://localhost:3001",  # Frontend alternative port
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Include routers with correct prefixes
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(twofa_router, prefix="/api/auth", tags=["two-factor-authentication"])
app.include_router(dashboard_router, prefix="/api", tags=["dashboard"])
app.include_router(profile_router, prefix="/api", tags=["profiles"])
app.include_router(integrations_router, prefix="/api/integrations", tags=["integrations"])

# Global error handler
@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    print(f"Error handling request {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": str(exc)},
    )

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
    try:
        result = await google_auth_callback(request)
        if isinstance(result, dict) and 'frontend_redirect' in result:
            return RedirectResponse(url=result['frontend_redirect'])
        return result
    except Exception as e:
        print(f"Google callback error: {e}")
        return RedirectResponse(url="http://localhost:3000/login?error=auth_failed")

@app.get('/api/auth/google/user')
async def get_user_info(token: str):
    return await get_google_user_info(token)

# For debugging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"\nRequest: {request.method} {request.url}")
    response = await call_next(request)
    print(f"Response: {response.status_code}")
    return response
