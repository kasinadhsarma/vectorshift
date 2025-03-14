from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
import redis
import json
from typing import Optional

router = APIRouter()
redis_client = redis.Redis(host='localhost', port=6379, db=0)

@router.get("/status")
async def get_notion_status(userId: str, orgId: str):
    print("\n=== Getting notion credentials ===")
    try:
        redis_key = f"notion_credentials:{orgId}:{userId}"
        print(f"User ID: {userId}")
        print(f"Org ID: {orgId}")
        print(f"Redis key: {redis_key}")
        
        credentials = redis_client.get(redis_key)
        if credentials:
            print("Found credentials in Redis")
            creds_dict = json.loads(credentials)
            return {
                "isConnected": True,
                "status": "active",
                "credentials": creds_dict
            }
        
        print("No credentials found in Redis")
        return {
            "isConnected": False,
            "status": "inactive",
            "credentials": None
        }
    except Exception as e:
        print(f"Error getting credentials: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        print("=== Credentials lookup complete ===\n")

@router.post("/authorize")
async def authorize_notion(request: Request):
    try:
        data = await request.json()
        user_id = data.get("userId")
        org_id = data.get("orgId")
        
        if not user_id or not org_id:
            raise HTTPException(status_code=400, detail="Missing required parameters")
            
        from integrations.notion import authorize_notion as notion_authorize
        response = await notion_authorize(user_id, org_id)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/credentials")
async def store_notion_credentials(request: Request):
    try:
        form = await request.form()
        user_id = form.get("user_id")
        org_id = form.get("org_id")
        
        if not user_id or not org_id:
            raise HTTPException(status_code=400, detail="Missing required parameters")
            
        redis_key = f"notion_credentials:{org_id}:{user_id}"
        credentials = redis_client.get(redis_key)
        
        if not credentials:
            raise HTTPException(status_code=404, detail="No credentials found")
            
        return JSONResponse(content=json.loads(credentials))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/data")
async def get_notion_data(request: Request):
    try:
        data = await request.json()
        user_id = data.get("userId")
        org_id = data.get("orgId")
        credentials = data.get("credentials")

        if not all([user_id, org_id, credentials]):
            raise HTTPException(status_code=400, detail="Missing required parameters")

        # Validate credentials
        redis_key = f"notion_credentials:{org_id}:{user_id}"
        stored_credentials = redis_client.get(redis_key)
        
        if not stored_credentials:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        from integrations.notion import get_notion_data as notion_get_data
        response = await notion_get_data(json.loads(stored_credentials))
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/oauth2callback")
async def notion_oauth_callback(request: Request):
    try:
        from integrations.notion import oauth2callback_notion
        return await oauth2callback_notion(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
