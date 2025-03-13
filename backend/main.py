"""Main FastAPI application module."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.integrations import router as integrations_router
from backend.integrations.google_auth import google_auth_url

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(integrations_router)

@app.get("/auth/google/url")
async def get_google_auth_url():
    """Endpoint to get Google auth URL."""
    return {"url": await google_auth_url()}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
