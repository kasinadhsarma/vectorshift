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
        body = await request.json()
        user_id = body.get('userId')
        org_id = body.get('orgId')

        if not user_id or not org_id:
            raise HTTPException(status_code=400, detail="Missing userId or orgId")

        auth_url = await provider_funcs["authorize"](user_id, org_id)
        return {"url": auth_url}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authorization error: {str(e)}")

@router.post("/integrations/{provider}/credentials")
async def get_integration_credentials(provider: str, request: Request):
    """Retrieve stored OAuth credentials for a provider."""
    try:
        provider_funcs = get_provider_functions(provider)
        body = await request.json()
        user_id = body.get('user_id')
        org_id = body.get('org_id')

        if not user_id or not org_id:
            raise HTTPException(status_code=400, detail="Missing user_id or org_id")

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
