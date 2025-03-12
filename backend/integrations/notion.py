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
    """Generate OAuth URL and store state"""
    try:
        if not all([CLIENT_ID, CLIENT_SECRET, REDIRECT_URI]):
            raise HTTPException(
                status_code=500,
                detail="Missing required Notion OAuth configuration"
            )

        state = secrets.token_urlsafe(32)
        state_data = {
            'state': state,
            'user_id': user_id,
            'org_id': org_id
        }
        encoded_state = json.dumps(state_data)
        await add_key_value_redis(f'notion_state:{state}', encoded_state, expire=600)
        
        auth_url = f'{AUTHORIZATION_URL}?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&state={state}&owner=user'
        return {"url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def oauth2callback_notion(request: Request):
    """Handle OAuth callback and store credentials"""
    try:
        error = request.query_params.get('error')
        if error:
            raise HTTPException(status_code=400, detail=error)

        state = request.query_params.get('state')
        code = request.query_params.get('code')
        
        if not state or not code:
            raise HTTPException(
                status_code=400, 
                detail='Missing required parameters'
            )
            
        saved_state = await get_value_redis(f'notion_state:{state}')
        if not saved_state:
            raise HTTPException(
                status_code=400, 
                detail='Invalid or expired state'
            )
            
        state_data = json.loads(saved_state)
        user_id = state_data.get('user_id')
        org_id = state_data.get('org_id')

        if not user_id or not org_id:
            raise HTTPException(
                status_code=400, 
                detail='Invalid state data'
            )

        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                'https://api.notion.com/v1/oauth/token',
                auth=(CLIENT_ID, CLIENT_SECRET),
                json={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': REDIRECT_URI
                }
            )
            
            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=token_response.status_code,
                    detail='Failed to get access token'
                )

            credentials = token_response.json()
            await add_key_value_redis(
                f'notion_credentials:{org_id}:{user_id}', 
                json.dumps(credentials), 
                expire=3600  # Store for 1 hour
            )
            await delete_key_redis(f'notion_state:{state}')

            return HTMLResponse(
                content="<html><script>window.close();</script></html>"
            )

    except Exception as e:
        return HTMLResponse(
            content=f"""
                <html>
                    <script>
                        window.opener.postMessage(
                            {{error: '{str(e)}'}}, 
                            '*'
                        );
                        window.close();
                    </script>
                </html>
            """
        )

async def get_notion_credentials(user_id, org_id):
    """Get stored credentials"""
    try:
        credentials = await get_value_redis(f'notion_credentials:{org_id}:{user_id}')
        if not credentials:
            raise HTTPException(
                status_code=400, 
                detail='No credentials found'
            )
        return json.loads(credentials)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500, 
            detail='Invalid credentials format'
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

async def get_items_notion(credentials) -> list[IntegrationItem]:
    """Get list of databases and pages from Notion"""
    try:
        if isinstance(credentials, str):
            credentials = json.loads(credentials)
            
        access_token = credentials.get('access_token')
        if not access_token:
            raise HTTPException(
                status_code=400,
                detail='Invalid credentials'
            )

        async with httpx.AsyncClient() as client:
            user_response = await client.get(
                'https://api.notion.com/v1/users/me',
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Notion-Version': '2022-06-28'
                }
            )
            
            if user_response.status_code != 200:
                raise HTTPException(
                    status_code=user_response.status_code,
                    detail='Failed to get user data'
                )

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
            
            if search_response.status_code != 200:
                raise HTTPException(
                    status_code=search_response.status_code,
                    detail='Failed to search databases'
                )

            search_data = search_response.json()
            
            return [
                IntegrationItem(
                    id=result.get('id'),
                    type='database',
                    name=result.get('title', [{}])[0].get('text', {}).get('content', 'Untitled'),
                    url=result.get('url'),
                    creation_time=result.get('created_time'),
                    last_modified_time=result.get('last_edited_time')
                )
                for result in search_data.get('results', [])
            ]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Error fetching Notion data: {str(e)}'
        )
