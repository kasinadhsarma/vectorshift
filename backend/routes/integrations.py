from fastapi import Request, APIRouter, HTTPException, Depends, Form
from fastapi.security import HTTPBearer
from typing import Dict
from cassandra_client import CassandraClient
from integrations.notion import (
    authorize_notion, oauth2callback_notion,
    get_notion_credentials, get_items_notion
)
from integrations.airtable import (
    authorize_airtable, oauth2callback_airtable,
    get_airtable_credentials, get_items_airtable
)
from integrations.slack import (
    authorize_slack, oauth2callback_slack,
    get_slack_credentials, get_items_slack
)
from integrations.hubspot import (
    authorize_hubspot, oauth2callback_hubspot,
    get_hubspot_credentials, get_items_hubspot
)
from redis_client import get_value_redis

router = APIRouter()
security = HTTPBearer()
cassandra = CassandraClient()

async def get_current_user(token: str = Depends(security)):
    user_data = await get_value_redis(f"user_token:{token}")
    if not user_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_data

@router.post("/api/integrations/{provider}/authorize")
async def authorize_integration(
    provider: str,
    request: Request,
    current_user: Dict = Depends(get_current_user)
):
    """Authorize an integration"""
    try:
        form = await request.form()
        user_id = form.get("userId")
        org_id = form.get("orgId")

        if not user_id or not org_id:
            raise HTTPException(status_code=400, detail="Missing userId or orgId")

        if provider == "notion":
            auth_url = await authorize_notion(user_id, org_id)
        elif provider == "airtable":
            auth_url = await authorize_airtable(user_id, org_id)
        elif provider == "slack":
            auth_url = await authorize_slack(user_id, org_id)
        elif provider == "hubspot":
            auth_url = await authorize_hubspot(user_id, org_id)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

        return {"url": auth_url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/integrations/{provider}/status")
async def get_integration_status(
    provider: str,
    user_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get integration status and workspace info"""
    try:
        # Get integration details from database
        integration = await cassandra.get_user_integration(user_id, provider)
        
        if not integration:
            return {
                "isConnected": False,
                "status": "inactive",
            }
        
        # Get workspace details based on provider
        if provider == "notion":
            credentials = await get_notion_credentials(user_id, integration.get("org_id", ""))
            items = await get_items_notion(credentials)
            return {
                "isConnected": True,
                "status": "active",
                "lastSync": integration.get("last_sync"),
                "workspace": {
                    "id": credentials.get("workspace_id"),
                    "name": credentials.get("workspace_name", "Notion Workspace"),
                    "icon": credentials.get("workspace_icon"),
                    "pages": [
                        {
                            "id": item.id,
                            "title": item.name,
                            "lastEdited": item.last_modified_time.isoformat() if item.last_modified_time else None
                        }
                        for item in items
                    ]
                }
            }
        
        elif provider == "airtable":
            credentials = await get_airtable_credentials(user_id, integration.get("org_id", ""))
            items = await get_items_airtable(credentials)
            return {
                "isConnected": True,
                "status": "active",
                "lastSync": integration.get("last_sync"),
                "workspace": {
                    "id": credentials.get("workspace_id"),
                    "name": "Airtable Workspace",
                    "bases": [
                        {
                            "id": item.id,
                            "name": item.name,
                            "lastModified": item.last_modified_time.isoformat() if item.last_modified_time else None
                        }
                        for item in items
                    ]
                }
            }
        
        elif provider == "slack":
            credentials = await get_slack_credentials(user_id, integration.get("org_id", ""))
            items = await get_items_slack(credentials)
            return {
                "isConnected": True,
                "status": "active",
                "lastSync": integration.get("last_sync"),
                "workspace": {
                    "id": credentials.get("workspace_id"),
                    "name": credentials.get("team_name", "Slack Workspace"),
                    "icon": credentials.get("team_icon"),
                    "channels": [
                        {
                            "id": item.id,
                            "name": item.name,
                            "visibility": item.visibility,
                            "creation_time": item.creation_time
                        }
                        for item in items
                    ]
                }
            }

        elif provider == "hubspot":
            credentials = await get_hubspot_credentials(user_id, integration.get("org_id", ""))
            items = await get_items_hubspot(credentials)
            return {
                "isConnected": True,
                "status": "active",
                "lastSync": integration.get("last_sync"),
                "workspace": {
                    "id": credentials.get("hub_id"),
                    "name": "HubSpot Account",
                    "contacts": [
                        {
                            "id": item.id,
                            "name": item.name,
                            "email": getattr(item, 'email', None),
                            "company": getattr(item, 'company', None),
                            "last_modified_time": item.last_modified_time
                        }
                        for item in items
                    ]
                }
            }

        # Default response for unsupported provider
        return {
            "isConnected": True,
            "status": integration.get("status", "active"),
            "lastSync": integration.get("last_sync")
        }

    except Exception as e:
        return {
            "isConnected": False,
            "status": "error",
            "error": str(e)
        }

@router.post("/api/integrations/{provider}/sync")
async def sync_integration(
    provider: str,
    user_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Sync integration data"""
    try:
        integration = await cassandra.get_user_integration(user_id, provider)
        if not integration:
            raise HTTPException(status_code=404, detail="Integration not found")

        # Get current credentials
        credentials = None
        if provider == "notion":
            credentials = await get_notion_credentials(user_id, integration.get("org_id", ""))
            items = await get_items_notion(credentials)
            await cassandra.update_integration_items(user_id, provider, items)
            
        elif provider == "airtable":
            credentials = await get_airtable_credentials(user_id, integration.get("org_id", ""))
            items = await get_items_airtable(credentials)
            await cassandra.update_integration_items(user_id, provider, items)
            
        elif provider == "slack":
            credentials = await get_slack_credentials(user_id, integration.get("org_id", ""))
            items = await get_items_slack(credentials)
            await cassandra.update_integration_items(user_id, provider, items)
            
        elif provider == "hubspot":
            credentials = await get_hubspot_credentials(user_id, integration.get("org_id", ""))
            items = await get_items_hubspot(credentials)
            await cassandra.update_integration_items(user_id, provider, items)

        # Return updated status
        return await get_integration_status(provider, user_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/integrations/{provider}/disconnect")
async def disconnect_integration(
    provider: str,
    user_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Disconnect an integration"""
    try:
        await cassandra.remove_user_integration(user_id, provider)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# OAuth routes
@router.get("/api/integrations/notion/oauth2callback")
async def notion_callback(request: Request):
    return await oauth2callback_notion(request)

@router.get("/api/integrations/airtable/oauth2callback")
async def airtable_callback(request: Request):
    return await oauth2callback_airtable(request)

@router.get("/api/integrations/slack/oauth2callback")
async def slack_callback(request: Request):
    return await oauth2callback_slack(request)

@router.get("/api/integrations/hubspot/oauth2callback")
async def hubspot_callback(request: Request):
    return await oauth2callback_hubspot(request)
