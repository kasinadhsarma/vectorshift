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

async def authorize_notion(user_id, org_id):
    state = secrets.token_urlsafe(32)
    state_data = {
        'state': state,
        'user_id': user_id,
        'org_id': org_id
    }
    encoded_state = json.dumps(state_data)
    await add_key_value_redis(f'notion_state:{org_id}:{user_id}', encoded_state, expire=600)
    
    auth_url = f'{AUTHORIZATION_URL}?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&state={state}&owner=user'
    return auth_url

async def oauth2callback_notion(request: Request):
    if request.query_params.get('error'):
        raise HTTPException(status_code=400, detail=request.query_params.get('error'))
    
    code = request.query_params.get('code')
    state = request.query_params.get('state')
    state_data = json.loads(state)

    user_id = state_data.get('user_id')
    org_id = state_data.get('org_id')

    saved_state = await get_value_redis(f'notion_state:{org_id}:{user_id}')
    if not saved_state or state != json.loads(saved_state).get('state'):
        raise HTTPException(status_code=400, detail='State does not match.')

    async with httpx.AsyncClient() as client:
        response, _ = await asyncio.gather(
            client.post(
                'https://api.notion.com/v1/oauth/token',
                auth=(CLIENT_ID, CLIENT_SECRET),
                json={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': REDIRECT_URI
                }
            ),
            delete_key_redis(f'notion_state:{org_id}:{user_id}')
        )

    await add_key_value_redis(f'notion_credentials:{org_id}:{user_id}', json.dumps(response.json()), expire=600)
    
    return HTMLResponse(content="<html><script>window.close();</script></html>")

async def get_notion_credentials(user_id, org_id):
    credentials = await get_value_redis(f'notion_credentials:{org_id}:{user_id}')
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found.')
    credentials = json.loads(credentials)
    await delete_key_redis(f'notion_credentials:{org_id}:{user_id}')
    return credentials

async def get_items_notion(credentials) -> list[IntegrationItem]:
    """Get list of databases and pages from Notion"""
    creds = json.loads(credentials)
    access_token = creds.get('access_token')
    
    if not access_token:
        raise HTTPException(status_code=400, detail='Invalid credentials')

    async with httpx.AsyncClient() as client:
        # Get user data
        user_response = await client.get(
            'https://api.notion.com/v1/users/me',
            headers={
                'Authorization': f'Bearer {access_token}',
                'Notion-Version': '2022-06-28'
            }
        )
        user_data = user_response.json()

        # Get search results (databases and pages)
        search_response = await client.post(
            'https://api.notion.com/v1/search',
            headers={
                'Authorization': f'Bearer {access_token}',
                'Notion-Version': '2022-06-28'
            },
            json={
                'filter': {'property': 'object', 'value': 'database'}
            }
        )
        search_data = search_response.json()

    items = []
    for result in search_data.get('results', []):
        item = IntegrationItem(
            id=result.get('id'),
            type='database',
            name=result.get('title', [{}])[0].get('text', {}).get('content', 'Untitled'),
            url=result.get('url'),
            creation_time=result.get('created_time'),
            last_modified_time=result.get('last_edited_time')
        )
        items.append(item)

    return items

