import json
import secrets
import os
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
from urllib.parse import quote, urlparse, urlunparse
import httpx
import asyncio
from dotenv import load_dotenv
from integrations.integration_item import IntegrationItem
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

load_dotenv()

CLIENT_ID = os.getenv('NOTION_CLIENT_ID')
CLIENT_SECRET = os.getenv('NOTION_CLIENT_SECRET')
REDIRECT_URI = os.getenv('NOTION_REDIRECT_URI')
AUTHORIZATION_URL = 'https://api.notion.com/v1/oauth/authorize'
TOKEN_URL = 'https://api.notion.com/v1/oauth/token'
NOTION_VERSION = '2022-06-28'

def validate_oauth_config():
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
    
    print(f"Using Notion redirect URI: {REDIRECT_URI}")

async def authorize_notion(user_id: str, org_id: str = None):
    """Generate OAuth URL and store state"""
    try:
        print("Validating OAuth config...")
        validate_oauth_config()
        
        print("Generating state and storing in Redis...")
        state = secrets.token_urlsafe(32)
        state_data = {'state': state, 'user_id': user_id}
        if org_id:
            state_data['org_id'] = org_id
            
        print(f"State data: {state_data}")
        await add_key_value_redis(f'notion_state:{state}', json.dumps(state_data), expire=600)
        
        print("Building authorization URL...")
        
        # Parse URL into components
        parsed = urlparse(REDIRECT_URI)
        # Encode only the path component
        encoded_path = quote(parsed.path, safe='/')
        # Reconstruct URL with encoded path
        encoded_redirect = urlunparse((
            parsed.scheme,
            parsed.netloc,
            encoded_path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        auth_url = f'{AUTHORIZATION_URL}?client_id={CLIENT_ID}&redirect_uri={encoded_redirect}&response_type=code&state={state}&owner=user'
        print(f"Authorization URL generated: {auth_url}")
        
        return {"url": auth_url}
    except Exception as e:
        import traceback
        error_details = f"Error in authorize_notion: {str(e)}\n{traceback.format_exc()}"
        print(error_details)
        raise HTTPException(status_code=500, detail=error_details)

async def oauth2callback_notion(request: Request):
    """Handle OAuth callback and store credentials"""
    error = request.query_params.get('error')
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    state, code = request.query_params.get('state'), request.query_params.get('code')
    if not state or not code:
        raise HTTPException(status_code=400, detail='Missing required parameters')
    
    try:
        saved_state = await get_value_redis(f'notion_state:{state}')
        if not saved_state:
            raise HTTPException(status_code=400, detail='Invalid or expired state')
        
        state_data = json.loads(saved_state)
        if state != state_data.get('state'):
            raise HTTPException(status_code=400, detail='State mismatch')
            
        user_id = state_data.get('user_id')
        org_id = state_data.get('org_id')
        
        if not user_id:
            raise HTTPException(status_code=400, detail='Missing user ID in state data')
            
        print(f"State verification successful for user: {user_id}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail='Invalid state data format')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'State verification error: {str(e)}')
    
    print(f"Starting OAuth callback with code: {code[:5]}...")
    print("\nStarting Notion OAuth token exchange:")
    print("----------------------------------------")
    print(f"1. Authorization code received: {code[:5]}...")
    print(f"2. State verification successful for user: {user_id}")
    print(f"3. Token request configuration:")
    print(f"   - Redirect URI: {REDIRECT_URI}")
    print(f"   - Client ID: {CLIENT_ID[:8]}...")
    print("----------------------------------------")

    # For token exchange, use the same encoding method
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
    
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': encoded_redirect,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }

    print("\nMaking token exchange request to Notion...")
    print("----------------------------------------")
    print("Request details:")
    print(f"URL: {TOKEN_URL}")
    print(f"Headers: Accept: application/json, Notion-Version: {NOTION_VERSION}")
    safe_data = {**token_data, 'client_secret': '***'}  # Hide sensitive data in logs
    print(f"Data: {json.dumps(safe_data, indent=2)}")
    print("----------------------------------------")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Configure client with proper SSL verification and timeout
            client.verify = True
            client.timeout = 30.0  # Belt and suspenders with the client timeout
            token_response = await client.post(
                TOKEN_URL,
                json=token_data,
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Notion-Version': NOTION_VERSION
                }
            )
            
            response_text = await token_response.aread()
            response_str = response_text.decode() if isinstance(response_text, bytes) else str(response_text)
            
            print("\nReceived response from Notion:")
            print("----------------------------------------")
            print(f"Status: {token_response.status_code}")
            print(f"Headers: {dict(token_response.headers)}")
            print(f"Response: {response_str}")

            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=token_response.status_code,
                    detail=f'Failed to get access token: {response_str}'
                )
            
            try:
                credentials = json.loads(response_str)
                if 'error' in credentials:
                    error_msg = f"Notion API error: {credentials.get('error')}"
                    if 'error_description' in credentials:
                        error_msg += f" - {credentials.get('error_description')}"
                    raise HTTPException(status_code=400, detail=error_msg)
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Invalid JSON response from Notion: {str(e)}"
                )

            # Store credentials in Redis
            redis_key = f'notion_credentials:{user_id}'
            if org_id:
                redis_key = f'notion_credentials:{org_id}:{user_id}'
            
            print("\nStoring credentials in Redis...")
            print(f"Using key: {redis_key}")
            
            await add_key_value_redis(redis_key, json.dumps(credentials), expire=3600)
            await delete_key_redis(f'notion_state:{state}')
            print("Credentials stored successfully")
            
            return HTMLResponse("<html><script>window.close();</script></html>")

    except httpx.TimeoutError:
        error_msg = "Timeout while connecting to Notion API"
        print(error_msg)
        raise HTTPException(status_code=504, detail=error_msg)
    except httpx.RequestError as e:
        error_msg = f"Network error during token request: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=502, detail=error_msg)
    except Exception as e:
        import traceback
        error_details = f"Error in token exchange: {str(e)}\n{traceback.format_exc()}"
        print(error_details)
        raise HTTPException(status_code=500, detail=error_details)

async def get_notion_credentials(user_id: str, org_id: str = None):
    """Retrieve stored Notion credentials"""
    redis_key = f'notion_credentials:{user_id}'
    if org_id:
        redis_key = f'notion_credentials:{org_id}:{user_id}'
    credentials = await get_value_redis(redis_key)
    if not credentials:
        return None
    return json.loads(credentials)

async def get_items_notion(credentials: dict) -> dict:
    """Retrieve Notion databases and pages"""
    # Ensure credentials is a dict, whether it comes as JSON string or dict
    if isinstance(credentials, str):
        try:
            credentials = json.loads(credentials)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail='Invalid credentials format')
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
