from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from cassandra_client import CassandraClient
import os
import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
security = HTTPBearer()
cassandra = CassandraClient()

class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class PasswordReset(BaseModel):
    email: str

class PasswordUpdate(BaseModel):
    token: str
    new_password: str

@router.post("/signup")
async def signup(user: UserCreate):
    try:
        user_id = await cassandra.create_user(user.email, user.password)
        # After successful creation, immediately log them in
        auth_data = await cassandra.verify_user(user.email, user.password)
        return {
            "message": "User created successfully",
            "user_id": str(user_id),
            "token": auth_data["token"],
            "user": {
                "email": user.email
            }
        }
    except ValueError as e:
        if "User already exists" in str(e):
            raise HTTPException(status_code=409, detail="User already exists")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/login")
async def login(user: UserLogin):
    try:
        auth_data = await cassandra.verify_user(user.email, user.password)
        # Include user information in response
        return {
            **auth_data,
            "user": {
                "email": user.email
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/forgot-password")
async def forgot_password(reset_request: PasswordReset):
    try:
        token = await cassandra.create_password_reset_token(reset_request.email)
        # In a real application, you would send this token via email
        return {"message": "Password reset token created", "token": token}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/reset-password")
async def reset_password(password_update: PasswordUpdate):
    try:
        success = await cassandra.reset_password(password_update.token, password_update.new_password)
        return {"message": "Password reset successful"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials,
            os.getenv('JWT_SECRET', 'your-secret-key'),
            algorithms=['HS256']
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
