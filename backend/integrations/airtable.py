# airtable.py

import datetime
import json
import secrets
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import asyncio
import base64
import hashlib
import os
import logging
import requests
from integrations.integration_item import IntegrationItem
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

def get_airtable_config():
    """Get Airtable configuration from environment variables"""
    client_id = os.environ.get('AIRTABLE_CLIENT_ID')
    client_secret = os.environ.get('AIRTABLE_CLIENT_SECRET')
    redirect_uri = os.environ.get('AIRTABLE_REDIRECT_URI')

    if not all([client_id, client_secret, redirect_uri]):
        logger.warning("Airtable environment variables not configured")
        return None, None, None

    encoded_secret = base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode()
    auth_url = f'https://airtable.com/oauth2/v1/authorize?client_id={client_id}&response_type=code&owner=user&redirect_uri={redirect_uri}'
    
    return encoded_secret, auth_url, redirect_uri

def check_airtable_config():
    """Verify Airtable configuration is available"""
    if not all([os.environ.get('AIRTABLE_CLIENT_ID'),
                os.environ.get('AIRTABLE_CLIENT_SECRET'),
                os.environ.get('AIRTABLE_REDIRECT_URI')]):
        raise HTTPException(
            status_code=503,
            detail="Airtable integration not configured. Please set AIRTABLE_CLIENT_ID, AIRTABLE_CLIENT_SECRET, and AIRTABLE_REDIRECT_URI"
        )

async def authorize_airtable(user_id: str, org_id: str) -> str:
    """Initialize Airtable OAuth flow"""
    client_id, _, redirect_uri = get_airtable_config()
    if not client_id:
        raise HTTPException(status_code=503, detail="Airtable integration not configured")
        
    state = {
        'user_id': user_id,
        'org_id': org_id
    }
    
    # Store state in Redis
    await add_key_value_redis(
        f'airtable_state:{org_id}:{user_id}', 
        json.dumps(state),
        expire=600
    )
    
    scopes = "data.records:read,schema.bases:read"
    auth_url = f"https://airtable.com/oauth2/v1/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&scope={scopes}"
    
    return auth_url

async def oauth2callback_airtable(request: Request):
    """Handle OAuth2 callback from Airtable"""
    check_airtable_config()
    encoded_secret, _, redirect_uri = get_airtable_config()

    try:
        if request.query_params.get('error'):
            raise HTTPException(
                status_code=400,
                detail=request.query_params.get('error_description', 'OAuth error')
            )

        code = request.query_params.get('code')
        encoded_state = request.query_params.get('state')
        if not code or not encoded_state:
            raise HTTPException(status_code=400, detail="Missing required parameters")

        try:
            state_data = json.loads(base64.urlsafe_b64decode(encoded_state).decode('utf-8'))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid state parameter")

        original_state = state_data.get('state')
        user_id = state_data.get('user_id')
        org_id = state_data.get('org_id')

        if not all([original_state, user_id, org_id]):
            raise HTTPException(status_code=400, detail="Invalid state data")

        saved_state, code_verifier = await asyncio.gather(
            get_value_redis(f'airtable_state:{org_id}:{user_id}'),
            get_value_redis(f'airtable_verifier:{org_id}:{user_id}'),
        )

        if not saved_state or original_state != json.loads(saved_state).get('state'):
            raise HTTPException(status_code=400, detail='State mismatch')

        async with httpx.AsyncClient() as client:
            response, _, _ = await asyncio.gather(
                client.post(
                    'https://airtable.com/oauth2/v1/token',
                    data={
                        'grant_type': 'authorization_code',
                        'code': code,
                        'redirect_uri': redirect_uri,
                        'client_id': os.environ.get('AIRTABLE_CLIENT_ID'),
                        'code_verifier': code_verifier.decode('utf-8'),
                    },
                    headers={
                        'Authorization': f'Basic {encoded_secret}',
                        'Content-Type': 'application/x-www-form-urlencoded',
                    }
                ),
                delete_key_redis(f'airtable_state:{org_id}:{user_id}'),
                delete_key_redis(f'airtable_verifier:{org_id}:{user_id}'),
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Token exchange failed: {response.text}"
                )

            credentials = response.json()
            await add_key_value_redis(
                f'airtable_credentials:{org_id}:{user_id}',
                json.dumps(credentials),
                expire=600
            )

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
                    <div class="success">Successfully connected to Airtable!</div>
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

async def get_airtable_credentials(user_id: str, org_id: str) -> Dict:
    """Retrieve stored Airtable credentials"""
    credentials = await get_value_redis(f'airtable_credentials:{org_id}:{user_id}')
    if not credentials:
        raise HTTPException(status_code=404, detail="No credentials found")
        
    return json.loads(credentials)

def create_integration_item_metadata_object(
    response_json: str, item_type: str, parent_id=None, parent_name=None
) -> IntegrationItem:
    """Create an integration item metadata object"""
    parent_id = None if parent_id is None else parent_id + '_Base'
    integration_item_metadata = IntegrationItem(
        id=response_json.get('id', None) + '_' + item_type,
        name=response_json.get('name', None),
        type=item_type,
        parent_id=parent_id,
        parent_path_or_name=parent_name,
    )

    return integration_item_metadata

async def fetch_items(access_token: str, url: str, offset=None) -> list:
    """Fetch items from Airtable API with pagination"""
    items = []
    params = {'offset': offset} if offset is not None else {}
    headers = {'Authorization': f'Bearer {access_token}'}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        items.extend(data.get('bases', []))
        
        if data.get('offset'):
            additional_items = await fetch_items(access_token, url, data['offset'])
            items.extend(additional_items)
            
    return items

async def get_items_airtable(credentials) -> list[IntegrationItem]:
    """Aggregate all metadata relevant for an Airtable integration"""
    try:
        check_airtable_config()
        credentials = json.loads(credentials) if isinstance(credentials, str) else credentials
        access_token = credentials.get('access_token')
        if not access_token:
            raise HTTPException(status_code=400, detail="Invalid credentials")

        url = 'https://api.airtable.com/v0/meta/bases'
        list_of_integration_item_metadata = []
        bases = await fetch_items(access_token, url)

        async with httpx.AsyncClient() as client:
            for base in bases:
                list_of_integration_item_metadata.append(
                    create_integration_item_metadata_object(base, 'Base')
                )
                
                tables_response = await client.get(
                    f'https://api.airtable.com/v0/meta/bases/{base.get("id")}/tables',
                    headers={'Authorization': f'Bearer {access_token}'}
                )
                tables_response.raise_for_status()
                tables_data = tables_response.json()

                for table in tables_data['tables']:
                    list_of_integration_item_metadata.append(
                        create_integration_item_metadata_object(
                            table,
                            'Table',
                            base.get('id'),
                            base.get('name'),
                        )
                    )

        logger.debug(f'Retrieved {len(list_of_integration_item_metadata)} Airtable items')
        return list_of_integration_item_metadata

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=e.response.status_code if hasattr(e, 'response') else 500,
            detail=f"Error fetching Airtable data: {str(e)}"
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

class AirtableIntegration:
    def __init__(self, credentials: Dict[str, str]):
        self.access_token = credentials.get('access_token')
        self.workspace_id = credentials.get('workspace_id')

    async def get_bases(self) -> List[IntegrationItem]:
        """Fetch bases from Airtable workspace"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://api.airtable.com/v0/meta/bases',
                headers={
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch Airtable bases"
                )
                
            data = response.json()
            bases = []
            
            for base in data.get('bases', []):
                bases.append(
                    IntegrationItem(
                        id=base['id'],
                        name=base['name'],
                        type='base',
                        last_modified_time=datetime.fromisoformat(base.get('modifiedTime', '')),
                        url=base.get('url')
                    )
                )
            
            return bases

    async def get_tables(self, base_id: str) -> List[Dict]:
        """Fetch tables within a base"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f'https://api.airtable.com/v0/meta/bases/{base_id}/tables',
                headers={
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch tables"
                )
                
            return response.json().get('tables', [])

    async def sync_data(self) -> Dict:
        """Sync all available data from Airtable"""
        try:
            bases = await self.get_bases()
            all_tables = {}
            
            for base in bases:
                if base.id:
                    tables = await self.get_tables(base.id)
                    all_tables[base.id] = tables
            
            return {
                "status": "success",
                "data": {
                    "bases": bases,
                    "tables": all_tables
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
