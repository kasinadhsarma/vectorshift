# notion.py

import json
import secrets
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import asyncio
import base64
import requests
from integrations.integration_item import IntegrationItem
import os
import logging
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis
from typing import Optional, Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

def get_notion_config():
    """Get Notion configuration from environment variables"""
    client_id = os.environ.get('NOTION_CLIENT_ID')
    client_secret = os.environ.get('NOTION_CLIENT_SECRET')
    redirect_uri = os.environ.get('NOTION_REDIRECT_URI')

    if not all([client_id, client_secret, redirect_uri]):
        logger.warning("Notion environment variables not configured")
        return None, None, None

    encoded_secret = base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode()
    auth_url = f'https://api.notion.com/v1/oauth/authorize?client_id={client_id}&response_type=code&owner=user&redirect_uri={redirect_uri}'
    
    return encoded_secret, auth_url, redirect_uri

def check_notion_config():
    """Verify Notion configuration is available"""
    if not all([os.environ.get('NOTION_CLIENT_ID'),
                os.environ.get('NOTION_CLIENT_SECRET'),
                os.environ.get('NOTION_REDIRECT_URI')]):
        raise HTTPException(
            status_code=503,
            detail="Notion integration not configured. Please set NOTION_CLIENT_ID, NOTION_CLIENT_SECRET, and NOTION_REDIRECT_URI"
        )

async def authorize_notion(user_id, org_id):
    """Start Notion OAuth flow"""
    check_notion_config()
    
    encoded_secret, auth_url, _ = get_notion_config()
    if not auth_url:
        raise HTTPException(status_code=503, detail="Notion integration not configured")

    state_data = {
        'state': secrets.token_urlsafe(32),
        'user_id': user_id,
        'org_id': org_id
    }
    encoded_state = json.dumps(state_data)
    await add_key_value_redis(f'notion_state:{org_id}:{user_id}', encoded_state, expire=600)

    return f'{auth_url}&state={encoded_state}'

async def oauth2callback_notion(request: Request):
    """Handle OAuth2 callback from Notion"""
    check_notion_config()
    encoded_secret, _, redirect_uri = get_notion_config()

    try:
        # Check for OAuth error
        if request.query_params.get('error'):
            raise HTTPException(
                status_code=400, 
                detail=request.query_params.get('error_description', request.query_params.get('error'))
            )

        # Get and validate required parameters
        code = request.query_params.get('code')
        encoded_state = request.query_params.get('state')
        
        if not code or not encoded_state:
            raise HTTPException(status_code=400, detail='Missing required parameters')

        try:
            state_data = json.loads(encoded_state)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail='Invalid state parameter')

        original_state = state_data.get('state')
        user_id = state_data.get('user_id')
        org_id = state_data.get('org_id')

        if not all([original_state, user_id, org_id]):
            raise HTTPException(status_code=400, detail='Invalid state data')

        # Validate state
        saved_state = await get_value_redis(f'notion_state:{org_id}:{user_id}')
        if not saved_state:
            raise HTTPException(status_code=400, detail='State expired or not found')

        if original_state != json.loads(saved_state).get('state'):
            raise HTTPException(status_code=400, detail='State mismatch')

        # Exchange code for token
        async with httpx.AsyncClient() as client:
            response, _ = await asyncio.gather(
                client.post(
                    'https://api.notion.com/v1/oauth/token',
                    json={
                        'grant_type': 'authorization_code',
                        'code': code,
                        'redirect_uri': redirect_uri
                    }, 
                    headers={
                        'Authorization': f'Basic {encoded_secret}',
                        'Content-Type': 'application/json',
                    }
                ),
                delete_key_redis(f'notion_state:{org_id}:{user_id}')
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Token exchange failed: {response.text}"
                )

            credentials = response.json()
            await add_key_value_redis(
                f'notion_credentials:{org_id}:{user_id}',
                json.dumps(credentials),
                expire=600
            )

        # Return success response
        close_window_script = """
        <html>
            <head>
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background-color: #f5f5f5;
                    }
                    .message {
                        text-align: center;
                        padding: 20px;
                        background: white;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }
                    .success {
                        color: #15803d;
                        font-size: 1.2em;
                        margin-bottom: 10px;
                    }
                </style>
            </head>
            <body>
                <div class="message">
                    <div class="success">Successfully connected to Notion!</div>
                    <p>You can close this window now.</p>
                </div>
                <script>
                    setTimeout(() => window.close(), 2000);
                </script>
            </body>
        </html>
        """
        return HTMLResponse(content=close_window_script)

    except HTTPException as e:
        error_script = f"""
        <html>
            <head>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background-color: #f5f5f5;
                    }}
                    .message {{
                        text-align: center;
                        padding: 20px;
                        background: white;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    .error {{
                        color: #dc2626;
                        font-size: 1.2em;
                        margin-bottom: 10px;
                    }}
                </style>
            </head>
            <body>
                <div class="message">
                    <div class="error">Authentication Failed</div>
                    <p>{e.detail}</p>
                </div>
                <script>
                    setTimeout(() => window.close(), 3000);
                </script>
            </body>
        </html>
        """
        return HTMLResponse(content=error_script, status_code=e.status_code)
    except Exception as e:
        logger.error(f"Unexpected error in Notion OAuth callback: {str(e)}")
        return HTMLResponse(
            content="""
            <html>
                <body>
                    <script>
                        window.close();
                    </script>
                </body>
            </html>
            """,
            status_code=500
        )

async def get_notion_credentials(user_id, org_id):
    """Get stored Notion credentials for a user"""
    credentials = await get_value_redis(f'notion_credentials:{org_id}:{user_id}')
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found.')
    credentials = json.loads(credentials)
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found.')
    await delete_key_redis(f'notion_credentials:{org_id}:{user_id}')

    return credentials

def _recursive_dict_search(data, target_key):
    """Recursively search for a key in a dictionary of dictionaries."""
    if target_key in data:
        return data[target_key]

    for value in data.values():
        if isinstance(value, dict):
            result = _recursive_dict_search(value, target_key)
            if result is not None:
                return result
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    result = _recursive_dict_search(item, target_key)
                    if result is not None:
                        return result
    return None

def create_integration_item_metadata_object(
    response_json: str,
) -> IntegrationItem:
    """creates an integration metadata object from the response"""
    name = _recursive_dict_search(response_json['properties'], 'content')
    parent_type = (
        ''
        if response_json['parent']['type'] is None
        else response_json['parent']['type']
    )
    if response_json['parent']['type'] == 'workspace':
        parent_id = None
    else:
        parent_id = (
            response_json['parent'][parent_type]
        )

    name = _recursive_dict_search(response_json, 'content') if name is None else name
    name = 'multi_select' if name is None else name
    name = response_json['object'] + ' ' + name

    integration_item_metadata = IntegrationItem(
        id=response_json['id'],
        type=response_json['object'],
        name=name,
        creation_time=response_json['created_time'],
        last_modified_time=response_json['last_edited_time'],
        parent_id=parent_id,
    )

    return integration_item_metadata

async def get_items_notion(credentials) -> list[IntegrationItem]:
    """Aggregates all metadata relevant for a notion integration"""
    try:
        check_notion_config()
        credentials = json.loads(credentials) if isinstance(credentials, str) else credentials
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://api.notion.com/v1/search',
                headers={
                    'Authorization': f'Bearer {credentials.get("access_token")}',
                    'Notion-Version': '2022-06-28',
                    'Content-Type': 'application/json'
                },
                json={}  # Empty search to get all items
            )

            response.raise_for_status()
            results = response.json()['results']
            
            list_of_integration_item_metadata = [
                create_integration_item_metadata_object(result)
                for result in results
                if result.get('id')  # Only include items with valid IDs
            ]

            return list_of_integration_item_metadata

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=e.response.status_code if hasattr(e, 'response') else 500,
            detail=f"Error fetching Notion data: {str(e)}"
        )
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid credentials format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

class NotionIntegration:
    def __init__(self, credentials: Dict[str, str]):
        self.access_token = credentials.get('access_token')
        self.workspace_id = credentials.get('workspace_id')
        
    async def get_pages(self) -> List[IntegrationItem]:
        # TODO: Implement Notion API call to fetch pages
        pass

    async def get_databases(self) -> List[IntegrationItem]:
        # TODO: Implement Notion API call to fetch databases
        pass
        
    async def search(self, query: str) -> List[IntegrationItem]:
        # TODO: Implement Notion API search
        pass

    async def sync_data(self) -> Dict[str, any]:
        """Sync data from Notion workspace"""
        try:
            pages = await self.get_pages()
            databases = await self.get_databases()
            
            return {
                "status": "success",
                "data": {
                    "pages": pages,
                    "databases": databases
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
