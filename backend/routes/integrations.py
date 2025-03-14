"""Integration routes for OAuth providers."""
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.security import HTTPBearer
from typing import Dict, Optional, List
from pydantic import BaseModel
import logging

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

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations")
security = HTTPBearer()
cassandra = CassandraClient()

class AuthorizeRequest(BaseModel):
    """Request model for authorization endpoints."""
    userId: str
    orgId: Optional[str] = None

    class Config:
        populate_by_name = True
        alias_generator = lambda string: string.replace('Id', '_id')

class DataRequest(BaseModel):
    """Request model for data endpoints."""
    credentials: Dict
    userId: str
    orgId: Optional[str] = None

    class Config:
        populate_by_name = True
        alias_generator = lambda string: string.replace('Id', '_id')

async def get_current_user(token: str = Depends(security)):
    """Mock authentication for development."""
    return {"id": "mock_user"}

def get_provider_functions(provider: str) -> Dict:
    """Get the appropriate functions for a given provider."""
    providers = {
        "notion": {
            "authorize": authorize_notion,
            "oauth2callback": oauth2callback_notion,
            "get_credentials": get_notion_credentials,
            "get_items": get_items_notion
        },
        "airtable": {
            "authorize": authorize_airtable,
            "oauth2callback": oauth2callback_airtable,
            "get_credentials": get_airtable_credentials,
            "get_items": get_items_airtable
        },
        "slack": {
            "authorize": authorize_slack,
            "oauth2callback": oauth2callback_slack,
            "get_credentials": get_slack_credentials,
            "get_items": get_items_slack
        },
        "hubspot": {
            "authorize": authorize_hubspot,
            "oauth2callback": oauth2callback_hubspot,
            "get_credentials": get_hubspot_credentials,
            "get_items": get_items_hubspot
        }
    }
    
    if provider not in providers:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider: {provider}"
        )
    
    return providers[provider]

# Generic provider routes
@router.post("/{provider}/authorize")
async def authorize_integration(provider: str, request: AuthorizeRequest):
    """Generate OAuth authorization URL for the provider."""
    try:
        logger.info(f"Authorizing {provider} for user {request.userId} in org {request.orgId}")
        provider_funcs = get_provider_functions(provider)
        auth_url = await provider_funcs["authorize"](request.userId, request.orgId)
        logger.info("Authorization URL generated successfully")
        return auth_url
        
    except Exception as e:
        logger.error(f"Error authorizing {provider}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{provider}/oauth2callback")
async def oauth_callback(provider: str, request: Request):
    """Handle OAuth2 callback from provider."""
    try:
        logger.info(f"Processing {provider} OAuth callback")
        provider_funcs = get_provider_functions(provider)
        result = await provider_funcs["oauth2callback"](request)
        logger.info(f"Successfully processed {provider} OAuth callback")
        return result
        
    except Exception as e:
        logger.error(f"Error in {provider} OAuth callback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{provider}/status")
async def get_integration_status(
    provider: str,
    user_id: str = Query(..., alias="userId"),
    org_id: str = Query(None, alias="orgId")
):
    """Fetch the connection status and details for an integration."""
    try:
        logger.info(f"Checking {provider} status for user {user_id}")
        provider_funcs = get_provider_functions(provider)
        credentials = await provider_funcs["get_credentials"](user_id, org_id)
        
        if not credentials:
            logger.info(f"No {provider} credentials found")
            return {
                "isConnected": False,
                "status": "inactive",
                "credentials": None
            }
            
        logger.info(f"Successfully retrieved {provider} credentials")
        return {
            "isConnected": True,
            "status": "active",
            "credentials": credentials
        }
        
    except Exception as e:
        logger.error(f"Error checking {provider} status: {str(e)}")
        if isinstance(e, HTTPException) and e.status_code == 404:
            return {
                "isConnected": False,
                "status": "inactive"
            }
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{provider}/data")
async def get_integration_data(provider: str, request: DataRequest):
    """Fetch data from the integration provider."""
    try:
        logger.info(f"Fetching {provider} data for user {request.userId}")
        provider_funcs = get_provider_functions(provider)
        data = await provider_funcs["get_items"](request.credentials)
        logger.info(f"Successfully retrieved {provider} data")
        return data
        
    except Exception as e:
        logger.error(f"Error fetching {provider} data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{provider}/disconnect")
async def disconnect_integration(
    provider: str,
    user_id: str = Query(..., alias="userId"),
    org_id: str = Query(None, alias="orgId")
):
    """Disconnect an integration and delete stored credentials."""
    try:
        logger.info(f"Disconnecting {provider} for user {user_id}")
        
        # Remove credentials from Redis
        redis_key = f"{provider}_credentials:{org_id or user_id}:{user_id}"
        await delete_key_redis(redis_key)
        
        # Remove from Cassandra (if applicable)
        cassandra_query = f"DELETE FROM integrations WHERE provider='{provider}' AND user_id='{user_id}'"
        await cassandra.execute(cassandra_query)
        
        logger.info(f"Successfully disconnected {provider}")
        return {
            "status": "success",
            "message": f"Successfully disconnected {provider}"
        }
        
    except Exception as e:
        logger.error(f"Error disconnecting {provider}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
