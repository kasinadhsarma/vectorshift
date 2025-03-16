from fastapi import Request, APIRouter, HTTPException, Depends, Response, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBearer
from typing import Dict, Callable, Any, Optional
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

# CORS headers for OAuth callbacks
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "http://localhost:3000",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Allow-Credentials": "true",
}

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

@router.post("/{provider}/authorize")
async def authorize_integration(provider: str, request: Request):
    """Generate OAuth authorization URL for the provider."""
    print(f"Authorizing {provider}")
    try:
        provider_funcs = get_provider_functions(provider)
        
        # Handle both JSON and form data
        content_type = request.headers.get('content-type', '')
        if 'application/json' in content_type:
            body = await request.json()
            user_id = body.get('user_id') or body.get('userId')
            org_id = body.get('org_id') or body.get('orgId')
        else:
            form = await request.form()
            user_id = form.get('user_id')
            org_id = form.get('org_id')

        print(f"Auth request for {provider} - user: {user_id}, org: {org_id}")

        if not user_id or not org_id:
            raise HTTPException(status_code=400, detail="Missing user_id/org_id")

        auth_url = await provider_funcs["authorize"](user_id, org_id)
        return {"url": auth_url}
    
    except Exception as e:
        print(f"Authorization error for {provider}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Authorization error: {str(e)}")

@router.get("/{provider}/status")
async def get_integration_status(
    provider: str,
    user_id: str = Query(..., description="User ID"),
    org_id: Optional[str] = Query(None, description="Organization ID")
):
    """Fetch the connection status and workspace details for an integration."""
    print(f"Checking status for {provider} - user: {user_id}, org: {org_id}")
    try:
        provider_funcs = get_provider_functions(provider)
        try:
            credentials = await provider_funcs["get_credentials"](user_id, org_id or user_id)
            items = await provider_funcs["get_items"](credentials)

            return {
                "isConnected": True,
                "status": "active",
                "lastSync": "2025-03-12T12:00:00Z",
                "workspace": items
            }
        except Exception as e:
            print(f"Error getting credentials/items: {str(e)}")
            if "No credentials found" in str(e):
                return {
                    "isConnected": False,
                    "status": "disconnected",
                    "error": "Integration not connected"
                }
            return {
                "isConnected": False,
                "status": "error",
                "error": str(e)
            }
    
    except Exception as e:
        print(f"Status error for {provider}: {str(e)}")
        return {
            "isConnected": False,
            "status": "error",
            "error": str(e)
        }

@router.post("/{provider}/sync")
async def sync_integration(
    provider: str,
    request: Request
):
    """Sync the latest data from the integration provider."""
    try:
        content_type = request.headers.get('content-type', '')
        if 'application/json' in content_type:
            body = await request.json()
            user_id = body.get('user_id')
            org_id = body.get('org_id')
        else:
            form = await request.form()
            user_id = form.get('user_id')
            org_id = form.get('org_id')

        if not user_id:
            raise HTTPException(status_code=400, detail="Missing user_id")

        print(f"Syncing {provider} - user: {user_id}, org: {org_id}")
        
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
        print(f"Sync error for {provider}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sync error: {str(e)}")

@router.post("/{provider}/disconnect")
async def disconnect_integration(
    provider: str,
    request: Request
):
    """Disconnect an integration and delete stored credentials."""
    try:
        content_type = request.headers.get('content-type', '')
        if 'application/json' in content_type:
            body = await request.json()
            user_id = body.get('user_id')
            org_id = body.get('org_id')
        else:
            form = await request.form()
            user_id = form.get('user_id')
            org_id = form.get('org_id')

        if not user_id:
            raise HTTPException(status_code=400, detail="Missing user_id")

        print(f"Disconnecting {provider} - user: {user_id}, org: {org_id}")

        # Remove credentials from Redis
        redis_key = f"{provider}_credentials:{org_id or user_id}:{user_id}"
        await delete_key_redis(redis_key)

        return {"status": "success", "message": f"Disconnected {provider} for user {user_id}"}
    
    except Exception as e:
        print(f"Disconnect error for {provider}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Disconnection error: {str(e)}")

@router.get("/{provider}/oauth2callback", include_in_schema=False)
async def oauth_callback(provider: str, request: Request):
    """Handle OAuth callback from provider."""
    print(f"OAuth callback for {provider}")
    try:
        provider_funcs = get_provider_functions(provider)
        response = await provider_funcs["oauth2callback"](request)
        
        # Add CORS headers to response
        for key, value in CORS_HEADERS.items():
            response.headers[key] = value
        
        return response
    except Exception as e:
        print(f"OAuth callback error for {provider}: {str(e)}")
        error_message = str(e)
        return HTMLResponse(
            content=f"""
                <html>
                    <head><title>Integration Error</title></head>
                    <body>
                        <h1>Connection Failed</h1>
                        <p>Failed to connect to the service.</p>
                        <script>
                            window.opener.postMessage(
                                {{ 
                                    type: '{provider}-oauth-callback',
                                    success: false,
                                    error: "{error_message}"
                                }},
                                '*'
                            );
                            setTimeout(() => window.close(), 1000);
                        </script>
                    </body>
                </html>
            """,
            headers=CORS_HEADERS
        )

@router.options("/{provider}/oauth2callback", include_in_schema=False)
async def oauth_callback_options(provider: str):
    """Handle preflight requests for OAuth2 callback."""
    return Response(content="", headers=CORS_HEADERS)
