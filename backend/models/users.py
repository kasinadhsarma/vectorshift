# backend/models/users.py

from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional, Dict

class User(BaseModel):
    email: EmailStr = Field(..., description="User's email, used as primary key")
    password_hash: Optional[str] = Field(None, description="Hashed password")
    auth_provider: Optional[str] = Field(None, description="Authentication provider (e.g., google)")
    google_id: Optional[str] = Field(None, description="Google ID if user signed up with Google")
    created_at: Optional[datetime] = Field(None, description="Timestamp when the user was created")
    last_login: Optional[datetime] = Field(None, description="Timestamp of the user's last login")

class PasswordResetToken(BaseModel):
    user_email: EmailStr = Field(..., description="User's email")
    reset_token: str = Field(..., description="The password reset token")
    created_at: Optional[datetime] = Field(None, description="Timestamp when the token was created")

class UserCredential(BaseModel):
    user_id: str = Field(..., description="User ID")
    provider: str = Field(..., description="Credential provider (e.g., google, airtable)")
    access_token: str = Field(..., description="Access token for the provider")
    refresh_token: Optional[str] = Field(None, description="Refresh token for the provider")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp of the access token")
    created_at: Optional[datetime] = Field(None, description="Timestamp when credentials were created")
    metadata: Optional[Dict[str, str]] = Field(None, description="Additional metadata for the credentials")

class UserIntegration(BaseModel):
    user_id: str = Field(..., description="User ID")
    provider: str = Field(..., description="Integration provider (e.g., notion, hubspot, airtable)")
    org_id: str = Field(..., description="Integration org ID")
    status: str = Field(..., description="Status of the integration (e.g., active, inactive)")
    last_sync: Optional[datetime] = Field(None, description="Timestamp of the last sync")
    settings: Optional[Dict[str, str]] = Field(None, description="Settings for the integration")
    
class IntegrationItem(BaseModel):
    user_id: str = Field(..., description="User ID")
    provider: str = Field(..., description="Integration provider (e.g., notion, hubspot, airtable)")
    item_id: str = Field(..., description="Item ID within the provider's system")
    name: str = Field(..., description="Name of the item")
    item_type: str = Field(..., description="Type of the item (e.g., page, contact, base, table)")
    url: Optional[str] = Field(None, description="URL of the item")
    creation_time: Optional[datetime] = Field(None, description="Creation timestamp of the item")
    last_modified_time: Optional[datetime] = Field(None, description="Last modified timestamp of the item")
    parent_id: Optional[str] = Field(None, description="ID of the parent item")
    metadata: Optional[Dict[str, str]] = Field(None, description="Additional metadata for the item")

class UserProfile(BaseModel):
    email: EmailStr = Field(..., description="User's email")
    full_name: Optional[str] = Field(None, description="User's full name")
    display_name: Optional[str] = Field(None, description="User's display name")
    avatar_url: Optional[str] = Field(None, description="URL of the user's avatar")
    company: Optional[str] = Field(None, description="User's company")
    job_title: Optional[str] = Field(None, description="User's job title")
    timezone: Optional[str] = Field(None, description="User's timezone")
    preferences: Optional[Dict[str, str]] = Field(None, description="User's preferences")
    updated_at: Optional[datetime] = Field(None, description="Timestamp of the last profile update")
