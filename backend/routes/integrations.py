<<<<<<< HEAD
"""Integration routes for OAuth providers."""
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.security import HTTPBearer
from typing import Dict, Callable, Optional, Any
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

router = APIRouter()
security = HTTPBearer()
cassandra = CassandraClient()
=======
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import Dict, Optional, List
from pydantic import BaseModel
from integrations import notion, airtable, hubspot, slack

router = APIRouter(prefix="/integrations")
>>>>>>> origin/main

class AuthorizeRequest(BaseModel):
    userId: str
    orgId: Optional[str] = None

<<<<<<< HEAD
class AuthorizeRequest(BaseModel):
    """Request model for authorization endpoints."""
    userId: str
    orgId: Optional[str] = None

    class Config:
        populate_by_name = True
        alias_generator = lambda string: string.replace('Id', '_id')

async def get_current_user(token: str = Depends(security)):
    """Mock authentication for development."""
    return {"id": "mock_user"}
=======
    class Config:
        populate_by_name = True
        alias_generator = lambda string: string.replace('Id', '_id')
>>>>>>> origin/main

class DataRequest(BaseModel):
    credentials: Dict
    userId: str
    orgId: Optional[str] = None

<<<<<<< HEAD
@router.post("/integrations/{provider}/authorize")
async def authorize_integration(provider: str, request: AuthorizeRequest):
    """Generate OAuth authorization URL for the provider."""
    try:
        logger.info(f"Authorizing {provider} for user {request.userId} in org {request.orgId}")
        provider_funcs = get_provider_functions(provider)
        auth_url = await provider_funcs["authorize"](request.userId, request.orgId)
        logger.info("Authorization URL generated successfully")
=======
    class Config:
        populate_by_name = True
        alias_generator = lambda string: string.replace('Id', '_id')

# Notion routes
@router.post("/notion/authorize")
async def authorize_notion(request: AuthorizeRequest):
    try:
        print(f"Authorizing Notion with userId: {request.userId}, orgId: {request.orgId}")
        response = await notion.authorize_notion(request.userId, request.orgId)
        print(f"Notion authorization response: {response}")
        return response
    except Exception as e:
        import traceback
        error_details = f"Error authorizing Notion: {str(e)}\n{traceback.format_exc()}"
        print(error_details)
        raise HTTPException(status_code=500, detail=error_details)

@router.get("/notion/oauthCallback", include_in_schema=False)
async def notion_callback(request: Request):
    try:
        return await notion.oauth2callback_notion(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notion/status")
async def get_notion_status(user_id: str = Query(..., alias="userId"), org_id: str = Query(None, alias="orgId")):
    try:
        credentials = await notion.get_notion_credentials(user_id, org_id)
        return {
            "isConnected": credentials is not None,
            "status": "active" if credentials else "inactive",
            "credentials": credentials
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/notion/data")
async def get_notion_data(request: DataRequest):
    try:
        data = await notion.get_items_notion(request.credentials)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Airtable routes
@router.post("/airtable/authorize")
async def authorize_airtable(request: AuthorizeRequest):
    try:
        auth_url = await airtable.authorize_airtable(request.userId, request.orgId)
>>>>>>> origin/main
        return {"url": auth_url}
    except Exception as e:
<<<<<<< HEAD
        logger.error(f"Error authorizing {provider}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/integrations/{provider}/credentials")
async def get_integration_credentials(
    provider: str,
    user_id: str = Query(...),
    org_id: str = Query(None)
):
    """Retrieve stored OAuth credentials for a provider."""
    try:
        logger.info(f"Getting {provider} credentials for user {user_id}")
        provider_funcs = get_provider_functions(provider)
        credentials = await provider_funcs["get_credentials"](user_id, org_id)
        return credentials
    
    except Exception as e:
        logger.error(f"Failed to retrieve {provider} credentials: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/integrations/{provider}/status")
async def get_integration_status(
    provider: str,
    user_id: str = Query(...),
    org_id: str = Query(None)
):
    """Fetch the connection status and workspace details for an integration."""
    try:
        logger.info(f"Checking {provider} status for user {user_id}")
        provider_funcs = get_provider_functions(provider)
        credentials = await provider_funcs["get_credentials"](user_id, org_id or user_id)
        
        if not credentials:
            logger.info(f"No {provider} credentials found")
            return {
                "isConnected": False,
                "status": "inactive",
                "workspace": None
            }

        items = await provider_funcs["get_items"](credentials)
        logger.info(f"Successfully retrieved {provider} workspace data")
=======
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/airtable/oauth2callback")
async def airtable_callback(request: Request):
    try:
        return await airtable.oauth2callback_airtable(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/airtable/status")
async def get_airtable_status(user_id: str = Query(..., alias="userId"), org_id: str = Query(None, alias="orgId")):
    try:
        credentials = await airtable.get_airtable_credentials(user_id, org_id)
>>>>>>> origin/main
        return {
            "isConnected": credentials is not None,
            "status": "active" if credentials else "inactive",
            "credentials": credentials
        }
    except Exception as e:
<<<<<<< HEAD
        logger.error(f"Error checking {provider} status: {str(e)}")
=======
        if isinstance(e, HTTPException) and e.status_code == 404:
            return {
                "isConnected": False,
                "status": "inactive"
            }
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/airtable/data")
async def get_airtable_data(request: DataRequest):
    try:
        items = await airtable.get_items_airtable(request.credentials, request.userId, request.orgId)
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# HubSpot routes
@router.post("/hubspot/authorize")
async def authorize_hubspot(request: AuthorizeRequest):
    try:
        result = await hubspot.authorize_hubspot(request.userId, request.orgId)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hubspot/oauth2callback")
async def hubspot_callback(request: Request):
    try:
        return await hubspot.oauth2callback_hubspot(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hubspot/status")
async def get_hubspot_status(user_id: str = Query(..., alias="userId"), org_id: str = Query(None, alias="orgId")):
    try:
        credentials = await hubspot.get_hubspot_credentials(user_id, org_id)
>>>>>>> origin/main
        return {
            "isConnected": credentials is not None,
            "status": "active" if credentials else "inactive",
            "credentials": credentials
        }
    except Exception as e:
        if isinstance(e, HTTPException) and e.status_code == 404:
            return {
                "isConnected": False,
                "status": "inactive"
            }
        raise HTTPException(status_code=500, detail=str(e))

<<<<<<< HEAD
@router.post("/integrations/{provider}/sync")
async def sync_integration(
    provider: str,
    user_id: str = Query(...),
    org_id: str = Query(None)
):
    """Sync the latest data from the integration provider."""
    try:
        logger.info(f"Syncing {provider} data for user {user_id}")
        provider_funcs = get_provider_functions(provider)
        credentials = await provider_funcs["get_credentials"](user_id, org_id or user_id)
        items = await provider_funcs["get_items"](credentials)
        
        logger.info(f"Successfully synced {provider} data")
=======
@router.post("/hubspot/data")
async def get_hubspot_data(request: DataRequest):
    try:
        items = await hubspot.get_items_hubspot(request.userId, request.orgId)
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Slack routes
@router.post("/slack/authorize")
async def authorize_slack(request: AuthorizeRequest):
    try:
        auth_url = await slack.authorize_slack(request.userId, request.orgId)
        return {"auth_url": auth_url}
    except HTTPException as e:
        if e.status_code == 400 and "invalid_scope" in e.detail:
            return {"detail": "Invalid scope provided for Slack authorization"}, 400
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/slack/oauth2callback")
async def slack_callback(request: Request):
    try:
        return await slack.oauth2callback_slack(request)
    except HTTPException as e:
        if e.status_code == 400 and "invalid_scope" in e.detail:
            return {"detail": "Invalid scope provided for Slack authorization"}, 400
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/slack/status")
async def get_slack_status(user_id: str = Query(..., alias="userId"), org_id: str = Query(None, alias="orgId")):
    try:
        credentials = await slack.get_slack_credentials(user_id, org_id)
>>>>>>> origin/main
        return {
            "isConnected": credentials is not None,
            "status": "active" if credentials else "inactive",
            "credentials": credentials
        }
    except HTTPException as e:
        if e.status_code == 400 and "invalid_scope" in e.detail:
            return {"detail": "Invalid scope provided for Slack authorization"}, 400
        raise e
    except Exception as e:
<<<<<<< HEAD
        logger.error(f"Error syncing {provider} data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/integrations/{provider}/disconnect")
async def disconnect_integration(
    provider: str,
    user_id: str = Query(...),
    org_id: str = Query(None)
):
    """Disconnect an integration and delete stored credentials."""
    try:
        logger.info(f"Disconnecting {provider} for user {user_id}")
        
        # Remove credentials from Redis
        redis_key = f"{provider}_credentials:{org_id or user_id}"
        await delete_key_redis(redis_key)
        
        # Remove from Cassandra (if applicable)
        cassandra_query = f"DELETE FROM integrations WHERE provider='{provider}' AND user_id='{user_id}'"
        cassandra.execute(cassandra_query)
        
        logger.info(f"Successfully disconnected {provider}")
        return {
            "status": "success",
            "message": f"Disconnected {provider} for user {user_id}"
        }
    
    except Exception as e:
        logger.error(f"Error disconnecting {provider}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/integrations/{provider}/oauth2callback")
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
=======
        if isinstance(e, HTTPException) and e.status_code == 404:
            return {
                "isConnected": False,
                "status": "inactive"
            }
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/slack/data")
async def get_slack_data(request: DataRequest):
    try:
        data = await slack.get_items_slack(request.credentials, request.userId, request.orgId)
        return data
    except Exception as e:
>>>>>>> origin/main
        raise HTTPException(status_code=500, detail=str(e))
