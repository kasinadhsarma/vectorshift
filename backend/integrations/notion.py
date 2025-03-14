"""Notion integration module."""
import os
import json
import time
import secrets
import logging
import base64
import asyncio
from typing import Dict, Any, Optional, List
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
from urllib.parse import quote, urlparse, urlunparse
import httpx
from integrations.integration_item import IntegrationItem
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OAuth Configuration
CLIENT_ID = '1b3d872b-594c-80ac-ad17-003784a50001'
CLIENT_SECRET = 'secret_1JGQEh5vDsMFOaadaIaDZ3GEatlCdVaEt7PkWauWm5x'
REDIRECT_URI = 'http://localhost:3000/api/integrations/notion/oauth2callback'
AUTHORIZATION_URL = 'https://api.notion.com/v1/oauth/authorize'
TOKEN_URL = 'https://api.notion.com/v1/oauth/token'
NOTION_VERSION = '2022-06-28'

class NotionError(Exception):
    """Custom exception for Notion API errors"""
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

def validate_oauth_config():
    """Validate required OAuth configuration."""
    missing = []
    if not CLIENT_ID:
        missing.append("NOTION_CLIENT_ID")
    if not CLIENT_SECRET:
        missing.append("NOTION_CLIENT_SECRET")
    if not REDIRECT_URI:
        missing.append("NOTION_REDIRECT_URI")
    
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"Missing Notion OAuth configuration: {', '.join(missing)}"
        )
    
    logger.info(f"Using Notion redirect URI: {REDIRECT_URI}")

async def authorize_notion(user_id: str, org_id: str = None):
    """Generate OAuth URL and store state"""
    try:
        logger.info("Validating OAuth config...")
        validate_oauth_config()
        
        # Generate state and store data
        state = secrets.token_urlsafe(32)
        state_data = {
            'state': state,
            'user_id': user_id
        }
        if org_id:
            state_data['org_id'] = org_id
            
        logger.info(f"Generated state data: {state_data}")
        await add_key_value_redis(f'notion_state:{state}', json.dumps(state_data), expire=600)
        
        # Parse and encode redirect URI
        parsed = urlparse(REDIRECT_URI)
        encoded_path = quote(parsed.path, safe='/')
        encoded_redirect = urlunparse((
            parsed.scheme,
            parsed.netloc,
            encoded_path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        
        # Build authorization URL
        auth_url = (
            f'{AUTHORIZATION_URL}'
            f'?client_id={CLIENT_ID}'
            f'&redirect_uri={encoded_redirect}'
            f'&response_type=code'
            f'&state={state}'
            f'&owner=user'
        )
        
        logger.info("Successfully generated authorization URL")
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
        # Check for OAuth errors
        error = request.query_params.get('error')
        if error:
            error_desc = request.query_params.get('error_description', 'Unknown error')
            logger.error(f"OAuth error: {error} - {error_desc}")
            raise HTTPException(status_code=400, detail=error_desc)
        
        # Get and validate parameters
        code = request.query_params.get('code')
        state = request.query_params.get('state')
        
        if not code or not state:
            logger.error("Missing required parameters")
            raise HTTPException(status_code=400, detail="Missing required parameters")
        
        # Get and verify state data
        saved_state = await get_value_redis(f'notion_state:{state}')
        if not saved_state:
            logger.error("State expired or invalid")
            raise HTTPException(status_code=400, detail="State expired or invalid")
        
        try:
            state_data = json.loads(saved_state)
            if state != state_data.get('state'):
                raise HTTPException(status_code=400, detail="State mismatch")
                
            user_id = state_data.get('user_id')
            org_id = state_data.get('org_id')
            
            if not user_id:
                raise HTTPException(status_code=400, detail="Missing user ID in state data")
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid state data format")
        
        # Exchange code for tokens
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info("Exchanging code for access token")
            
            # Parse and encode redirect URI for token exchange
            parsed = urlparse(REDIRECT_URI)
            encoded_path = quote(parsed.path, safe='/')
            encoded_redirect = urlunparse((
                parsed.scheme,
                parsed.netloc,
                encoded_path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
            
            # Prepare token request
            token_data = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': encoded_redirect
            }
            
            # Basic auth with client credentials
            auth = base64.b64encode(
                f"{CLIENT_ID}:{CLIENT_SECRET}".encode()
            ).decode()
            
            token_response = await client.post(
                TOKEN_URL,
                json=token_data,
                headers={
                    'Authorization': f'Basic {auth}',
                    'Content-Type': 'application/json',
                    'Notion-Version': NOTION_VERSION
                }
            )
            
            if token_response.status_code != 200:
                logger.error(f"Token exchange failed: {token_response.text}")
                await handle_notion_error(token_response)
            
            # Process token response
            token_info = token_response.json()
            if 'error' in token_info:
                error_msg = f"Notion API error: {token_info.get('error')}"
                if 'error_description' in token_info:
                    error_msg += f" - {token_info.get('error_description')}"
                raise HTTPException(status_code=400, detail=error_msg)
            
            # Store credentials
            credentials = {
                'access_token': token_info['access_token'],
                'bot_id': token_info.get('bot_id'),
                'workspace_name': token_info.get('workspace_name'),
                'workspace_icon': token_info.get('workspace_icon'),
                'owner': token_info.get('owner')
            }
            
            redis_key = f'notion_credentials:{org_id}:{user_id}' if org_id else f'notion_credentials:{user_id}'
            await add_key_value_redis(redis_key, json.dumps(credentials), expire=None)
            
            logger.info("Successfully stored credentials")
            
            # Cleanup state
            await delete_key_redis(f'notion_state:{state}')
            
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
    """Get stored Notion credentials and connection status"""
    try:
        redis_key = f'notion_credentials:{org_id}:{user_id}' if org_id else f'notion_credentials:{user_id}'
        logger.info(f"Getting Notion credentials for user {user_id}")
        
        stored_creds = await get_value_redis(redis_key)
        if not stored_creds:
            logger.info("No credentials found")
            return {
                "isConnected": False,
                "status": "inactive",
                "credentials": None
            }
            
        try:
            if isinstance(stored_creds, str):
                credentials = json.loads(stored_creds)
            else:
                credentials = stored_creds
                
            # Validate access token exists
            if not credentials.get('access_token'):
                return {
                    "isConnected": False,
                    "status": "invalid",
                    "credentials": None
                }
                
            return {
                "isConnected": True,
                "status": "active",
                "credentials": credentials
            }
                
        except json.JSONDecodeError:
            logger.error("Invalid credentials format")
            return {
                "isConnected": False,
                "status": "error",
                "credentials": None
            }
        
    except Exception as e:
        logger.error(f"Error getting credentials: {str(e)}")
        return {
            "isConnected": False,
            "status": "error",
            "credentials": None,
            "error": str(e)
        }

async def get_items_notion(credentials: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch databases and pages from Notion."""
    try:
        # Handle both string and dict credentials
        if isinstance(credentials, str):
            try:
                credentials = json.loads(credentials)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid credentials format")
        
        access_token = credentials.get('access_token')
        if not access_token:
            raise HTTPException(status_code=401, detail="Missing access token")
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Notion-Version': NOTION_VERSION,
            'Content-Type': 'application/json'
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info("Making requests to Notion API")
            
            # Make parallel requests for user info, databases and pages
            responses = await asyncio.gather(
                client.get('https://api.notion.com/v1/users/me', headers=headers),
                client.post(
                    'https://api.notion.com/v1/search',
                    headers=headers,
                    json={'filter': {'property': 'object', 'value': 'database'}, 'page_size': 20}
                ),
                client.post(
                    'https://api.notion.com/v1/search',
                    headers=headers,
                    json={'filter': {'property': 'object', 'value': 'page'}, 'page_size': 20}
                )
            )
            
            user_response, db_response, page_response = responses
            
            # Check responses for errors
            for resp in responses:
                if resp.status_code != 200:
                    await handle_notion_error(resp)
                    
                try:
                    resp_data = resp.json()
                    if resp_data.get('object') == 'error':
                        raise HTTPException(
                            status_code=400,
                            detail=f"Notion error: {resp_data.get('message', 'Unknown error')}"
                        )
                except json.JSONDecodeError:
                    raise HTTPException(status_code=500, detail="Invalid JSON response from Notion")
            
            # Process user data
            user_data = user_response.json()
            user_info = {
                'id': user_data.get('id'),
                'name': user_data.get('name'),
                'avatar_url': user_data.get('avatar_url'),
                'type': user_data.get('type', 'unknown')
            }
            
            # Process databases
            databases = []
            for db in db_response.json().get('results', []):
                title = next(
                    (text.get('text', {}).get('content', '')
                    for text in db.get('title', [{}])
                    if 'text' in text),
                    'Untitled'
                )
                
                databases.append({
                    'id': db['id'],
                    'name': title,
                    'created_time': db.get('created_time'),
                    'last_edited_time': db.get('last_edited_time'),
                    'url': db.get('url'),
                    'icon': db.get('icon'),
                    'cover': db.get('cover'),
                    'properties': list(db.get('properties', {}).keys())
                })
            
            # Process pages
            pages = []
            for page in page_response.json().get('results', []):
                title = next(
                    (text.get('text', {}).get('content', '')
                    for text in page.get('properties', {}).get('title', {}).get('title', [{}])
                    if 'text' in text),
                    'Untitled'
                )
                
                pages.append({
                    'id': page['id'],
                    'title': title,
                    'created_time': page.get('created_time'),
                    'last_edited_time': page.get('last_edited_time'),
                    'url': page.get('url'),
                    'icon': page.get('icon'),
                    'cover': page.get('cover'),
                    'parent': {
                        'type': page.get('parent', {}).get('type'),
                        'id': page.get('parent', {}).get('database_id') or page.get('parent', {}).get('page_id')
                    }
                })
            
            logger.info(f"Retrieved {len(databases)} databases and {len(pages)} pages")
            return {
                'isConnected': True,
                'status': 'active',
                'user': user_info,
                'lastSync': user_data.get('bot', {}).get('last_seen'),
                'databases': databases,
                'pages': pages,
                'credentials': credentials
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
