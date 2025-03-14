# notion.py

import json
import secrets
import logging
from typing import Optional, Dict, Any, Tuple
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import asyncio
import base64
from integrations.integration_item import IntegrationItem
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CLIENT_ID = '1b3d872b-594c-80ac-ad17-003784a50001'
CLIENT_SECRET = 'secret_1JGQEh5vDsMFOaadaIaDZ3GEatlCdVaEt7PkWauWm5x'
REDIRECT_URI = 'http://localhost:3000/api/integrations/notion/oauth2callback'
NOTION_API_VERSION = '2022-06-28'

<<<<<<< Updated upstream
def validate_oauth_config():
    if not all([CLIENT_ID, CLIENT_SECRET, REDIRECT_URI]):
        raise HTTPException(status_code=500, detail="Missing Notion OAuth configuration")

async def authorize_notion(user_id: str, org_id: str):
    """Generate OAuth URL and store state"""
    validate_oauth_config()
    state = secrets.token_urlsafe(32)
    state_data = {'state': state, 'user_id': user_id, 'org_id': org_id}
    await add_key_value_redis(f'notion_state:{state}', json.dumps(state_data), expire=600)
    
    auth_url = f'{AUTHORIZATION_URL}?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&state={state}&owner=user'
    return {"url": auth_url}

async def oauth2callback_notion(request: Request):
    """Handle OAuth callback and store credentials"""
    error = request.query_params.get('error')
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    state, code = request.query_params.get('state'), request.query_params.get('code')
    if not state or not code:
        raise HTTPException(status_code=400, detail='Missing required parameters')
    
    saved_state = await get_value_redis(f'notion_state:{state}')
    if not saved_state:
        raise HTTPException(status_code=400, detail='Invalid or expired state')
    
    state_data = json.loads(saved_state)
    user_id, org_id = state_data.get('user_id'), state_data.get('org_id')
    
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            TOKEN_URL,
            auth=(CLIENT_ID, CLIENT_SECRET),
            json={'grant_type': 'authorization_code', 'code': code, 'redirect_uri': REDIRECT_URI},
        )
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=token_response.status_code, detail='Failed to get access token')
        
        credentials = token_response.json()
        await add_key_value_redis(f'notion_credentials:{org_id}:{user_id}', json.dumps(credentials), expire=3600)
        await delete_key_redis(f'notion_state:{state}')
    
    return HTMLResponse("<html><script>window.close();</script></html>")

async def get_notion_credentials(user_id: str, org_id: str):
    """Retrieve stored Notion credentials"""
    credentials = await get_value_redis(f'notion_credentials:{org_id}:{user_id}')
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found')
    return json.loads(credentials)

async def get_items_notion(credentials: dict) -> dict:
    """Retrieve Notion databases and pages"""
    credentials = json.loads(credentials) if isinstance(credentials, str) else credentials
    access_token = credentials.get('access_token')
    if not access_token:
        raise HTTPException(status_code=400, detail='Invalid credentials')
    
    headers = {'Authorization': f'Bearer {access_token}', 'Notion-Version': NOTION_VERSION}
    async with httpx.AsyncClient() as client:
        responses = await asyncio.gather(
            client.get('https://api.notion.com/v1/users/me', headers=headers),
            client.post('https://api.notion.com/v1/search', headers=headers, json={'filter': {'property': 'object', 'value': 'database'}}),
            client.post('https://api.notion.com/v1/search', headers=headers, json={'filter': {'property': 'object', 'value': 'page'}}),
        )
    
    if any(response.status_code != 200 for response in responses):
        raise HTTPException(status_code=500, detail='Failed to fetch Notion data')
    
    user_response, db_response, page_response = responses
    
    databases = [
        {
            'id': db['id'],
            'name': db.get('title', [{}])[0].get('text', {}).get('content', 'Untitled'),
            'items': len(db.get('properties', {})),
        } for db in db_response.json().get('results', [])
    ]
    
    pages = [
        {
            'id': page['id'],
            'title': page.get('properties', {}).get('title', {}).get('title', [{}])[0].get('text', {}).get('content', 'Untitled'),
            'lastEdited': page.get('last_edited_time'),
        } for page in page_response.json().get('results', [])
    ]
    
    return {
        'isConnected': True,
        'status': 'active',
        'lastSync': user_response.json().get('bot', {}).get('last_seen'),
        'databases': databases,
        'pages': pages,
        'credentials': credentials,
    }
=======
encoded_client_id_secret = base64.b64encode(f'{CLIENT_ID}:{CLIENT_SECRET}'.encode()).decode()

class NotionError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)

async def handle_notion_error(response: httpx.Response) -> None:
    """Handle Notion API error responses"""
    try:
        error_data = response.json()
        error_code = error_data.get('code', 'unknown_error')
        error_message = error_data.get('message', str(response.text))
        logger.error(f"Notion API error: {error_code} - {error_message}")
    except Exception:
        error_code = 'parsing_error'
        error_message = str(response.text)
        logger.error(f"Failed to parse error response: {response.text}")

    status_map = {
        401: ('unauthorized', 'Access token is invalid or expired. Please re-authorize.'),
        403: ('restricted_resource', 'Access to this resource is restricted.'),
        404: ('object_not_found', 'Resource not found. Make sure it is shared with the integration.'),
        429: ('rate_limited', 'Too many requests. Please try again later.'),
        500: ('internal_server_error', 'Notion server error. Please try again later.'),
        503: ('service_unavailable', 'Notion service is temporarily unavailable.')
    }

    default_code, default_message = status_map.get(
        response.status_code, 
        ('unknown_error', 'An unknown error occurred')
    )

    raise NotionError(
        response.status_code,
        error_code or default_code,
        error_message or default_message
    )

async def authorize_notion(user_id: str, org_id: str):
    """Generate OAuth URL and store state"""
    try:
        state = secrets.token_urlsafe(32)
        state_data = {
            'state': state,
            'user_id': user_id,
            'org_id': org_id
        }
        
        logger.info(f"Generating OAuth state for user {user_id} in org {org_id}")
        
        # Store state in Redis with 10 minute expiry
        await add_key_value_redis(
            f'notion_state:{org_id}:{user_id}', 
            json.dumps(state_data), 
            expire=600
        )
        
        auth_url = (
            f'https://api.notion.com/v1/oauth/authorize'
            f'?client_id={CLIENT_ID}'
            f'&response_type=code'
            f'&owner=user'
            f'&redirect_uri={REDIRECT_URI}'
            f'&state={json.dumps(state_data)}'
        )
        
        logger.info(f"Generated authorization URL")
        return {"url": auth_url}
        
    except Exception as e:
        logger.error(f"Error generating authorization URL: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate authorization URL: {str(e)}"
        )

async def oauth2callback_notion(request: Request):
    """Handle OAuth callback and store credentials"""
    try:
        # Get query parameters
        params = request.query_params
        if params.get('error'):
            error_msg = params.get('error')
            logger.error(f"OAuth error: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
            
        code = params.get('code')
        state_json = params.get('state')
        
        if not code or not state_json:
            logger.error("Missing required parameters")
            raise HTTPException(status_code=400, detail="Missing required parameters")
            
        # Parse and validate state
        try:
            state_data = json.loads(state_json)
            original_state = state_data.get('state')
            user_id = state_data.get('user_id')
            org_id = state_data.get('org_id')
            
            logger.info(f"Processing callback for user {user_id} in org {org_id}")
            
            if not all([original_state, user_id, org_id]):
                raise ValueError("Invalid state format")
        except Exception as e:
            logger.error(f"Invalid state format: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid state format: {str(e)}")
            
        # Verify stored state
        stored_state = await get_value_redis(f'notion_state:{org_id}:{user_id}')
        
        if not stored_state:
            logger.error("State expired or invalid")
            raise HTTPException(status_code=400, detail="State expired or invalid")
            
        stored_state_data = json.loads(stored_state)
        if original_state != stored_state_data.get('state'):
            logger.error("State mismatch")
            raise HTTPException(status_code=400, detail="State mismatch")
            
        # Exchange code for access token
        async with httpx.AsyncClient() as client:
            logger.info("Exchanging code for access token")
            
            encoded_credentials = base64.b64encode(
                f"{CLIENT_ID}:{CLIENT_SECRET}".encode()
            ).decode()
            
            token_response = await client.post(
                'https://api.notion.com/v1/oauth/token',
                json={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': REDIRECT_URI
                },
                headers={
                    'Authorization': f'Basic {encoded_credentials}',
                    'Content-Type': 'application/json',
                    'Notion-Version': NOTION_API_VERSION
                }
            )
            
            if token_response.status_code != 200:
                logger.error(f"Token exchange failed with status {token_response.status_code}")
                logger.error(f"Response: {token_response.text}")
                await handle_notion_error(token_response)
                
            credentials = token_response.json()
            logger.info("Successfully obtained access token")
            
            # Store credentials in Redis
            redis_key = f'notion_credentials:{org_id}:{user_id}'
            logger.info(f"Storing credentials in Redis with key: {redis_key}")
            
            # Store credentials with extended structure
            stored_creds = {
                "isConnected": True,
                "status": "active",
                "credentials": credentials,
                "access_token": credentials.get("access_token"),
                "workspace_name": credentials.get("workspace_name"),
                "bot_id": credentials.get("bot_id")
            }
            
            await add_key_value_redis(
                redis_key,
                json.dumps(stored_creds),
                expire=None  # No expiry for credentials
            )
            
            logger.info("Successfully stored credentials")
            
            # Cleanup state
            await delete_key_redis(f'notion_state:{org_id}:{user_id}')
            
            return HTMLResponse(content="""
                <html>
                    <script>
                        if (window.opener) {
                            window.opener.postMessage({ type: "NOTION_AUTH_SUCCESS" }, "*");
                            window.close();
                        }
                    </script>
                    <body>
                        Authentication successful! You can close this window.
                    </body>
                </html>
            """)
            
    except NotionError as e:
        logger.error(f"Notion API error: {e.code} - {e.message}")
        return HTMLResponse(content=f"""
            <html>
                <script>
                    if (window.opener) {{
                        window.opener.postMessage({{ 
                            type: "NOTION_AUTH_ERROR",
                            error: "{e.message}"
                        }}, "*");
                        window.close();
                    }}
                </script>
                <body>
                    Authentication failed: {e.message}
                    <br>
                    You can close this window.
                </body>
            </html>
        """)
    except Exception as e:
        logger.error(f"Error in OAuth callback: {str(e)}")
        return HTMLResponse(content=f"""
            <html>
                <script>
                    if (window.opener) {{
                        window.opener.postMessage({{ 
                            type: "NOTION_AUTH_ERROR",
                            error: "{str(e)}"
                        }}, "*");
                        window.close();
                    }}
                </script>
                <body>
                    Authentication failed: {str(e)}
                    <br>
                    You can close this window.
                </body>
            </html>
        """)

async def get_notion_credentials(user_id: str, org_id: str = None) -> Optional[Dict[str, Any]]:
    """Get stored Notion credentials"""
    try:
        redis_key = f'notion_credentials:{org_id or user_id}:{user_id}'
        logger.info(f"\n=== Getting notion credentials ===")
        logger.info(f"User ID: {user_id}")
        logger.info(f"Org ID: {org_id}")
        logger.info(f"Redis key: {redis_key}")
        
        stored_creds = await get_value_redis(redis_key)
        
        if stored_creds:
            logger.info("Found credentials in Redis")
            if isinstance(stored_creds, str):
                return json.loads(stored_creds)
            return stored_creds
            
        logger.info("No credentials found in Redis")
        return None
        
    except Exception as e:
        logger.error(f"Error getting credentials: {str(e)}")
        return None
    finally:
        logger.info("=== Credentials lookup complete ===\n")

async def get_notion_data(credentials: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch Notion data using stored credentials"""
    try:
        # First try to get access token from nested structure
        access_token = (
            credentials.get('access_token') or 
            credentials.get('credentials', {}).get('access_token')
        )
        
        if not access_token:
            raise HTTPException(
                status_code=401, 
                detail="Invalid credentials: missing access token"
            )
            
        logger.info("Making requests to Notion API")
        async with httpx.AsyncClient() as client:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Notion-Version': NOTION_API_VERSION
            }

            # Fetch databases
            logger.info("Fetching databases...")
            db_response = await client.get(
                'https://api.notion.com/v1/databases',
                headers=headers
            )
            
            if db_response.status_code != 200:
                await handle_notion_error(db_response)
                
            # Fetch pages
            logger.info("Fetching pages...")
            pages_response = await client.post(
                'https://api.notion.com/v1/search',
                headers=headers,
                json={
                    "filter": {"property": "object", "value": "page"}
                }
            )
            
            if pages_response.status_code != 200:
                await handle_notion_error(pages_response)

            db_data = db_response.json()
            pages_data = pages_response.json()
                
            logger.info(f"Successfully fetched {len(db_data.get('results', []))} databases and {len(pages_data.get('results', []))} pages")
            
            return {
                "databases": db_data.get('results', []),
                "pages": pages_data.get('results', [])
            }
            
    except NotionError as e:
        logger.error(f"Notion API error: {e.code} - {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error fetching Notion data: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch Notion data: {str(e)}"
        )

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
    credentials = json.loads(credentials)
    response = requests.post(
        'https://api.notion.com/v1/search',
        headers={
            'Authorization': f'Bearer {credentials.get("access_token")}',
            'Notion-Version': '2022-06-28',
        },
    )

    if response.status_code == 200:
        results = response.json()['results']
        list_of_integration_item_metadata = []
        for result in results:
            list_of_integration_item_metadata.append(
                create_integration_item_metadata_object(result)
            )

        print(list_of_integration_item_metadata)
    return
>>>>>>> Stashed changes
