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

CLIENT_ID = os.getenv('AIRTABLE_CLIENT_ID')
CLIENT_SECRET = os.getenv('AIRTABLE_CLIENT_SECRET')
REDIRECT_URI = os.getenv('AIRTABLE_REDIRECT_URI')
AUTHORIZATION_URL = 'https://airtable.com/oauth2/v1/authorize'
TOKEN_URL = 'https://airtable.com/oauth2/v1/token'
API_URL = 'https://api.airtable.com/v0/meta'

async def authorize_airtable(user_id, org_id):
    state = secrets.token_urlsafe(32)
    state_data = {
        'state': state,
        'user_id': user_id,
        'org_id': org_id
    }
    encoded_state = json.dumps(state_data)
    await add_key_value_redis(f'airtable_state:{org_id}:{user_id}', encoded_state, expire=600)
    
    scopes = [
        'data.records:read',
        'data.records:write',
        'schema.bases:read',
        'schema.bases:write'
    ]
    
    auth_url = (
        f'{AUTHORIZATION_URL}'
        f'?client_id={CLIENT_ID}'
        f'&redirect_uri={REDIRECT_URI}'
        f'&response_type=code'
        f'&state={state}'
        f'&scope={" ".join(scopes)}'
    )
    return auth_url

async def oauth2callback_airtable(request: Request):
    if request.query_params.get('error'):
        raise HTTPException(
            status_code=400,
            detail=request.query_params.get('error_description', 'OAuth error')
        )
    
    code = request.query_params.get('code')
    state = request.query_params.get('state')
    
    try:
        state_data = json.loads(state)
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(status_code=400, detail='Invalid state parameter')

    user_id = state_data.get('user_id')
    org_id = state_data.get('org_id')

    saved_state = await get_value_redis(f'airtable_state:{org_id}:{user_id}')
    if not saved_state or state != json.loads(saved_state).get('state'):
        raise HTTPException(status_code=400, detail='State mismatch')

    async with httpx.AsyncClient() as client:
        response, _ = await asyncio.gather(
            client.post(
                TOKEN_URL,
                data={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': REDIRECT_URI,
                    'client_id': CLIENT_ID,
                    'client_secret': CLIENT_SECRET
                }
            ),
            delete_key_redis(f'airtable_state:{org_id}:{user_id}')
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail='Failed to obtain access token'
            )

        token_data = response.json()
        await add_key_value_redis(
            f'airtable_credentials:{org_id}:{user_id}',
            json.dumps(token_data),
            expire=token_data.get('expires_in', 7200)
        )
    
    return HTMLResponse(content="""
        <html>
            <head><title>Airtable Connection Successful</title></head>
            <body>
                <h1>Connection Successful!</h1>
                <p>You have successfully connected your Airtable account.</p>
                <script>
                    window.opener.postMessage(
                        { 
                            type: 'airtable-oauth-callback',
                            success: true,
                            workspaceId: 'airtable'
                        },
                        '*'
                    );
                    setTimeout(() => window.close(), 1000);
                </script>
            </body>
        </html>
    """)

async def get_airtable_credentials(user_id, org_id):
    credentials = await get_value_redis(f'airtable_credentials:{org_id}:{user_id}')
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found')
    
    credentials_data = json.loads(credentials)
    await delete_key_redis(f'airtable_credentials:{org_id}:{user_id}')
    return credentials_data

async def get_items_airtable(credentials) -> list[IntegrationItem]:
    """Get list of bases and tables from Airtable"""
    try:
        creds = json.loads(credentials)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail='Invalid credentials format')
    
    access_token = creds.get('access_token')
    if not access_token:
        raise HTTPException(status_code=400, detail='Missing access token')

    async with httpx.AsyncClient() as client:
        bases_response = await client.get(
            f'{API_URL}/bases',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if bases_response.status_code != 200:
            raise HTTPException(
                status_code=bases_response.status_code,
                detail='Failed to fetch Airtable bases'
            )
        
        bases_data = bases_response.json()
        
    items = []
    for base in bases_data.get('bases', []):
        # Add base as an item
        base_item = IntegrationItem(
            id=base.get('id'),
            type='base',
            name=base.get('name', 'Untitled Base'),
            url=f"https://airtable.com/{base.get('id')}",
            creation_time=base.get('createdTime'),
            last_modified_time=base.get('modifiedTime'),
            permissions=base.get('permissionLevel')
        )
        items.append(base_item)
        
        # Add each table in the base
        for table in base.get('tables', []):
            table_item = IntegrationItem(
                id=f"{base.get('id')}/{table.get('id')}",
                type='table',
                name=table.get('name', 'Untitled Table'),
                url=f"https://airtable.com/{base.get('id')}/{table.get('id')}",
                creation_time=table.get('createdTime'),
                last_modified_time=table.get('modifiedTime'),
                parent_id=base.get('id')
            )
            items.append(table_item)

    return items
