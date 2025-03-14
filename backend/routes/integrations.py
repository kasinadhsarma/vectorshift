<<<<<<< Updated upstream
from fastapi import Request, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer
from typing import Dict, Callable, Any
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
from redis_client import get_value_redis, delete_key_redis

router = APIRouter()
security = HTTPBearer()
cassandra = CassandraClient()
=======
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import Dict, Optional, List
from pydantic import BaseModel
from integrations import notion, airtable, hubspot, slack
import logging

router = APIRouter(prefix="/api/integrations")  # Updated prefix to include /api
logger = logging.getLogger(__name__)
>>>>>>> Stashed changes

# Provider mapping for OAuth integrations
PROVIDER_MAP = {
    "notion": {
        "authorize": authorize_notion,
        "oauth2callback": oauth2callback_notion,
        "get_credentials": get_notion_credentials,
        "get_items": get_items_notion,
    },
    "airtable": {
        "authorize": authorize_airtable,
        "oauth2callback": oauth2callback_airtable,
        "get_credentials": get_airtable_credentials,
        "get_items": get_items_airtable,
    },
    "slack": {
        "authorize": authorize_slack,
        "oauth2callback": oauth2callback_slack,
        "get_credentials": get_slack_credentials,
        "get_items": get_items_slack,
    },
    "hubspot": {
        "authorize": authorize_hubspot,
        "oauth2callback": oauth2callback_hubspot,
        "get_credentials": get_hubspot_credentials,
        "get_items": get_items_hubspot,
    }
}

async def get_current_user(token: str = Depends(security)):
    """Mock authentication for development."""
    return {"id": "mock_user"}

<<<<<<< Updated upstream
def get_provider_functions(provider: str) -> Dict[str, Callable]:
    """Retrieve provider-specific OAuth functions."""
    if provider not in PROVIDER_MAP:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
    return PROVIDER_MAP[provider]

@router.post("/integrations/{provider}/authorize")
async def authorize_integration(provider: str, request: Request):
    """Generate OAuth authorization URL for the provider."""
    try:
        provider_funcs = get_provider_functions(provider)
        
        # Handle both JSON and form data
        content_type = request.headers.get('content-type', '')
        if 'application/json' in content_type:
            body = await request.json()
            user_id = body.get('userId')
            org_id = body.get('orgId')
        else:
            form = await request.form()
            user_id = form.get('user_id')
            org_id = form.get('org_id')

        if not user_id or not org_id:
            raise HTTPException(status_code=400, detail="Missing user_id/org_id")

        auth_url = await provider_funcs["authorize"](user_id, org_id)
=======
class DataRequest(BaseModel):
    userId: str
    orgId: Optional[str] = None

    class Config:
        populate_by_name = True
        alias_generator = lambda string: string.replace('Id', '_id')

# Notion routes
@router.post("/notion/authorize")
async def authorize_notion_route(request: AuthorizeRequest):
    try:
        logger.info(f"Authorizing Notion for user {request.userId} in org {request.orgId}")
        response = await notion.authorize_notion(request.userId, request.orgId)
        logger.info("Authorization URL generated successfully")
        return response
    except Exception as e:
        logger.error(f"Error authorizing Notion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notion/oauth2callback")
async def notion_callback_route(request: Request):
    try:
        logger.info("Processing Notion OAuth callback")
        return await notion.oauth2callback_notion(request)
    except Exception as e:
        logger.error(f"Error in Notion OAuth callback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notion/status")
async def get_notion_status(
    userId: str = Query(...),
    orgId: str = Query(None)
):
    try:
        logger.info(f"Checking Notion status for user {userId} in org {orgId}")
        credentials = await notion.get_notion_credentials(userId, orgId)
        return {
            "isConnected": credentials is not None,
            "status": "active" if credentials else "inactive",
            "credentials": credentials
        }
    except Exception as e:
        logger.error(f"Error checking Notion status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/notion/data")
async def get_notion_data_route(request: DataRequest):
    try:
        logger.info(f"Fetching Notion data for user {request.userId} in org {request.orgId}")
        
        # Get credentials from Redis
        credentials = await notion.get_notion_credentials(request.userId, request.orgId)
        if not credentials:
            logger.error("No credentials found")
            raise HTTPException(
                status_code=401,
                detail="No credentials found. Please reconnect to Notion."
            )
            
        # Fetch data using the stored credentials
        data = await notion.get_notion_data(credentials)
        return data
    except notion.NotionError as e:
        # Handle specific Notion API errors
        logger.error(f"Notion API error: {e.code} - {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error fetching Notion data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Airtable routes
@router.post("/airtable/authorize")
async def authorize_airtable(request: AuthorizeRequest):
    try:
        auth_url = await airtable.authorize_airtable(request.userId, request.orgId)
>>>>>>> Stashed changes
        return {"url": auth_url}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authorization error: {str(e)}")

@router.post("/integrations/{provider}/credentials")
async def get_integration_credentials(provider: str, request: Request):
    """Retrieve stored OAuth credentials for a provider."""
    try:
        provider_funcs = get_provider_functions(provider)
        
        # Handle both JSON and form data
        content_type = request.headers.get('content-type', '')
        if 'application/json' in content_type:
            body = await request.json()
            user_id = body.get('user_id')
            org_id = body.get('org_id')
        else:
            form = await request.form()
            user_id = form.get('user_id')
            org_id = form.get('org_id')

        if not user_id or not org_id:
            raise HTTPException(status_code=400, detail="Missing user_id/org_id")

        credentials = await provider_funcs["get_credentials"](user_id, org_id)
        return credentials
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve credentials: {str(e)}")

@router.get("/integrations/{provider}/status")
async def get_integration_status(provider: str, user_id: str, org_id: str = None):
    """Fetch the connection status and workspace details for an integration."""
    try:
        provider_funcs = get_provider_functions(provider)
        credentials = await provider_funcs["get_credentials"](user_id, org_id or user_id)
        items = await provider_funcs["get_items"](credentials)

        return {
            "isConnected": True,
            "status": "active",
            "lastSync": "2025-03-12T12:00:00Z",
            "workspace": items
        }
    
    except Exception as e:
        return {
            "isConnected": False,
            "status": "error",
            "error": str(e)
        }

@router.post("/integrations/{provider}/sync")
async def sync_integration(provider: str, user_id: str, org_id: str = None):
    """Sync the latest data from the integration provider."""
    try:
        provider_funcs = get_provider_functions(provider)
        credentials = await provider_funcs["get_credentials"](user_id, org_id or user_id)
        items = await provider_funcs["get_items"](credentials)

        return {
            "isConnected": True,
            "status": "active",
            "lastSync": "2025-03-12T12:00:00Z",
            "workspace": items
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync error: {str(e)}")

@router.post("/integrations/{provider}/disconnect")
async def disconnect_integration(provider: str, user_id: str, org_id: str = None):
    """Disconnect an integration and delete stored credentials."""
    try:
        provider_funcs = get_provider_functions(provider)

        # Remove credentials from Redis
        redis_key = f"{provider}_credentials:{org_id or user_id}"
        await delete_key_redis(redis_key)

        # Remove from Cassandra (if applicable)
        cassandra_query = f"DELETE FROM integrations WHERE provider='{provider}' AND user_id='{user_id}'"
        cassandra.execute(cassandra_query)

        return {"status": "success", "message": f"Disconnected {provider} for user {user_id}"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Disconnection error: {str(e)}")

@router.get("/integrations/{provider}/oauth2callback")
async def oauth_callback(provider: str, request: Request):
    """Handle OAuth2 callback from provider."""
    try:
        provider_funcs = get_provider_functions(provider)
        return await provider_funcs["oauth2callback"](request)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth2 callback error: {str(e)}")
