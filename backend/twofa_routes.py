from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
from cassandra_client import CassandraClient
from two_factor_auth import setup_2fa, verify_2fa, is_2fa_enabled, disable_2fa
import io
import base64
import jwt
import os
import json
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
security = HTTPBearer(auto_error=False)  # Make it non-auto-error to handle token extraction manually
cassandra = CassandraClient()

class TwoFactorSetupResponse(BaseModel):
    secret: str
    qr_code_base64: str
    
class TwoFactorVerifyRequest(BaseModel):
    code: str
    user_id: Optional[str] = None

class TwoFactorVerifyResponse(BaseModel):
    is_valid: bool
    token: Optional[str] = None

class TwoFactorLoginRequest(BaseModel):
    email: str
    code: str

class TwoFactorCheckResponse(BaseModel):
    is_enabled: bool

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Get user from token, with non-auto-error for cleaner handling"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    try:
        payload = jwt.decode(
            credentials.credentials,
            os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key'),
            algorithms=['HS256']
        )
        return payload
    except jwt.exceptions.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.exceptions.DecodeError:
        raise HTTPException(status_code=401, detail="Invalid token format")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

async def extract_token(request: Request) -> Optional[Dict[str, Any]]:
    """Extract token from request in various formats and return decoded payload"""
    token = None
    
    # Try Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    
    # Try query params
    if not token:
        token = request.query_params.get("token")
    
    # Try form data or JSON body
    if not token:
        try:
            body = await request.json()
            token = body.get("token")
        except:
            try:
                form = await request.form()
                token = form.get("token")
            except:
                pass
    
    if not token:
        return None
        
    try:
        payload = jwt.decode(
            token,
            os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key'),
            algorithms=['HS256']
        )
        return payload
    except:
        return None

@router.post("/2fa/setup")
async def setup_two_factor(request: Request):
    """Set up two-factor authentication for a user"""
    # Get user from token
    user = await extract_token(request)
    if not user:
        body = None
        try:
            body = await request.json()
        except:
            pass
            
        user_id = body.get("user_id") if body else None
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")
    else:
        user_id = user.get("sub")
        
    # Check if 2FA is already enabled
    if await is_2fa_enabled(user_id, cassandra):
        raise HTTPException(status_code=400, detail="Two-factor authentication is already enabled")
    
    # Set up 2FA
    secret, qr_code = await setup_2fa(user_id, cassandra)
    
    # Return the secret and QR code
    qr_code_base64 = base64.b64encode(qr_code).decode('utf-8')
    return TwoFactorSetupResponse(secret=secret, qr_code_base64=qr_code_base64)

@router.get("/2fa/qrcode")
async def get_qr_code(request: Request):
    """Get the QR code for two-factor authentication"""
    # Get user from token
    user = await extract_token(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
        
    user_id = user.get("sub")
    
    # Check if 2FA is enabled
    if not await is_2fa_enabled(user_id, cassandra):
        raise HTTPException(status_code=400, detail="Two-factor authentication is not enabled")
    
    # Set up 2FA (this will return the existing secret if already set up)
    secret, qr_code = await setup_2fa(user_id, cassandra)
    
    # Return the QR code as an image
    return StreamingResponse(io.BytesIO(qr_code), media_type="image/png")

@router.post("/2fa/verify")
async def verify_two_factor(request: TwoFactorVerifyRequest, req: Request):
    """Verify a two-factor authentication code"""
    # Try to get user ID from request
    user_id = request.user_id
    
    if not user_id:
        # Try to get from token
        user = await extract_token(req)
        if user:
            user_id = user.get("sub")
    
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    
    # Check if 2FA is enabled
    if not await is_2fa_enabled(user_id, cassandra):
        raise HTTPException(status_code=400, detail="Two-factor authentication is not enabled")
    
    # Verify the code
    is_valid = await verify_2fa(user_id, request.code, cassandra)
    
    # Return the result
    return TwoFactorVerifyResponse(is_valid=is_valid)

@router.post("/2fa/login")
async def login_with_2fa(request: TwoFactorLoginRequest):
    """Login with a two-factor authentication code"""
    # Verify the code
    user_id = request.email
    is_valid = await verify_2fa(user_id, request.code, cassandra)
    
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid 2FA code")
    
    # Generate a new token
    token = cassandra._create_access_token({"sub": user_id})
    
    # Return the token
    return TwoFactorVerifyResponse(is_valid=True, token=token)

@router.post("/2fa/disable")
async def disable_two_factor(request: Request):
    """Disable two-factor authentication for a user"""
    # Get user from token
    user = await extract_token(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
        
    user_id = user.get("sub")
    
    # Check if 2FA is enabled
    if not await is_2fa_enabled(user_id, cassandra):
        raise HTTPException(status_code=400, detail="Two-factor authentication is not enabled")
    
    # Disable 2FA
    success = await disable_2fa(user_id, cassandra)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to disable two-factor authentication")
    
    return {"message": "Two-factor authentication disabled successfully"}

@router.get("/2fa/check")
async def check_two_factor(request: Request):
    """Check if two-factor authentication is enabled for a user"""
    # First try the query param
    user_id = request.query_params.get("user_id")
    
    # If not in query param, try to extract from token
    if not user_id:
        user = await extract_token(request)
        if user:
            user_id = user.get("sub")
    
    # If still no user_id, return not enabled
    if not user_id:
        return TwoFactorCheckResponse(is_enabled=False)
    
    # Check if 2FA is enabled
    is_enabled = await is_2fa_enabled(user_id, cassandra)
    
    return TwoFactorCheckResponse(is_enabled=is_enabled)
