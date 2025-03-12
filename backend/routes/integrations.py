from fastapi import Request, APIRouter, HTTPException, Depends, Form
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
from redis_client import get_value_redis

router = APIRouter()
security = HTTPBearer()
cassandra = CassandraClient()

# Mapping of provider names to their integration functions
PROVIDER_MAP = {
    "notion": {
        "authorize": authorize_notion,
        "oauth2callback": oauth2callback_notion,
        "get_credentials": get_notion_credentials,
        "get_items": get_items_notion,
        "mock_data": {
            "id": "mock-workspace-id",
            "name": "Mock Notion Workspace",
            "icon": "https://notion.so/favicon.ico",
            "pages": [
                {
                    "id": "page1",
                    "title": "Test Page 1",
                    "lastEdited": "2025-03-12T12:00:00Z"
                },
                {
                    "id": "page2",
                    "title": "Test Page 2",
                    "lastEdited": "2025-03-12T11:00:00Z"
                }
            ]
        }
    },
    "airtable": {
        "authorize": authorize_airtable,
        "oauth2callback": oauth2callback_airtable,
        "get_credentials": get_airtable_credentials,
        "get_items": get_items_airtable,
        "mock_data": {
            "id": "mock-airtable-id",
            "name": "Mock Airtable Workspace",
            "bases": [
                {
                    "id": "base1",
                    "name": "Test Base 1",
                    "lastModified": "2025-03-12T12:00:00Z"
                },
                {
                    "id": "base2",
                    "name": "Test Base 2",
                    "lastModified": "2025-03-12T11:00:00Z"
                }
            ]
        }
    },
    "slack": {
        "authorize": authorize_slack,
        "oauth2callback": oauth2callback_slack,
        "get_credentials": get_slack_credentials,
        "get_items": get_items_slack,
        "mock_data": {
            "id": "mock-slack-id",
            "name": "Mock Slack Workspace",
            "icon": "https://slack.com/favicon.ico",
            "channels": [
                {
                    "id": "channel1",
                    "name": "general",
                    "visibility": "public",
                    "creation_time": "2025-03-12T12:00:00Z"
                },
                {
                    "id": "channel2",
                    "name": "random",
                    "visibility": "public",
                    "creation_time": "2025-03-12T11:00:00Z"
                }
            ]
        }
    },
    "hubspot": {
        "authorize": authorize_hubspot,
        "oauth2callback": oauth2callback_hubspot,
        "get_credentials": get_hubspot_credentials,
        "get_items": get_items_hubspot,
        "mock_data": {
            "id": "mock-hubspot-id",
            "name": "Mock HubSpot Account",
            "contacts": [
                {
                    "id": "contact1",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "company": "Example Co",
                    "last_modified_time": "2025-03-12T12:00:00Z"
                },
                {
                    "id": "contact2",
                    "name": "Jane Smith",
                    "email": "jane@example.com",
                    "company": "Test Inc",
                    "last_modified_time": "2025-03-12T11:00:00Z"
                }
            ]
        }
    }
}

async def get_current_user(token: str = Depends(security)):
    # For development, bypass authentication
    return {"id": "mock_user"}

def get_provider_functions(provider: str) -> Dict[str, Callable]:
    """Get provider-specific functions"""
    if provider not in PROVIDER_MAP:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
    return PROVIDER_MAP[provider]

@router.post("/integrations/{provider}/authorize")
async def authorize_integration(
    provider: str,
    request: Request,
    current_user: Dict = None  # Make optional for development
):
    """Authorize an integration"""
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
            user_id = form.get('userId')
            org_id = form.get('orgId')

        if not user_id or not org_id:
            raise HTTPException(status_code=400, detail="Missing userId or orgId")

        auth_url = await provider_funcs["authorize"](user_id, org_id)
        return {"url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/integrations/{provider}/status")
async def get_integration_status(
    provider: str,
    user_id: str,
    current_user: Dict = None  # Make optional for development
):
    """Get integration status and workspace info"""
    try:
        provider_funcs = get_provider_functions(provider)
        credentials = await provider_funcs["get_credentials"](user_id, current_user["id"])
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
async def sync_integration(
    provider: str,
    user_id: str,
    current_user: Dict = None  # Make optional for development
):
    """Sync integration data"""
    try:
        provider_funcs = get_provider_functions(provider)
        credentials = await provider_funcs["get_credentials"](user_id, current_user["id"])
        items = await provider_funcs["get_items"](credentials)
        return {
            "isConnected": True,
            "status": "active",
            "lastSync": "2025-03-12T12:00:00Z",
            "workspace": items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/integrations/{provider}/disconnect")
async def disconnect_integration(
    provider: str,
    user_id: str,
    current_user: Dict = None  # Make optional for development
):
    """Disconnect an integration"""
    try:
        # For testing, just return success
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/integrations/{provider}/oauth2callback")
async def oauth_callback(provider: str, request: Request):
    """Generic OAuth callback handler"""
    provider_funcs = get_provider_functions(provider)
    return await provider_funcs["oauth2callback"](request)
