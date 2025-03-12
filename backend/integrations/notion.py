import json
import secrets
import os
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
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