from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
from cassandra_client import CassandraClient

router = APIRouter()
security = HTTPBearer()
cassandra = CassandraClient()

class ProfileUpdate(BaseModel):
    fullName: Optional[str] = None
    displayName: Optional[str] = None
    avatarUrl: Optional[str] = None
    company: Optional[str] = None
    jobTitle: Optional[str] = None
    timezone: Optional[str] = None
    preferences: Optional[Dict[str, str]] = None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        # Verify token and get user data
        user_data = await cassandra.verify_token(token)
        if not user_data:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_data
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.get("/api/users/{email}/profile")
async def get_profile(email: str, current_user: Dict = Depends(get_current_user)):
    """Get user profile information"""
    # Verify user is accessing their own profile
    if email != current_user.get("email"):
        raise HTTPException(status_code=403, detail="Not authorized to access this profile")

    profile = await cassandra.get_user_profile(email)
    if not profile:
        # Create default profile if it doesn't exist
        await cassandra.create_user_profile(email)
        profile = await cassandra.get_user_profile(email)

    return profile

@router.put("/api/users/{email}/profile")
async def update_profile(
    email: str,
    profile_update: ProfileUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """Update user profile information"""
    # Verify user is updating their own profile
    if email != current_user.get("email"):
        raise HTTPException(status_code=403, detail="Not authorized to update this profile")

    # Update profile
    success = await cassandra.update_user_profile(email, profile_update.dict(exclude_unset=True))
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update profile")

    # Return updated profile
    updated_profile = await cassandra.get_user_profile(email)
    return updated_profile
