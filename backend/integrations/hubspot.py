import json
import secrets
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import asyncio
import base64
from integrations.integration_item import IntegrationItem
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv('HUBSPOT_CLIENT_ID')
CLIENT_SECRET = os.getenv('HUBSPOT_CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:8000/integrations/hubspot/oauth2callback'

authorization_url = f'https://app.hubspot.com/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=contacts'

async def authorize_hubspot(user_id, org_id):
    state_data = {
        'state': secrets.token_urlsafe(32),
        'user_id': user_id,
        'org_id': org_id
    }
    encoded_state = json.dumps(state_data)
    await add_key_value_redis(f'hubspot_state:{org_id}:{user_id}', encoded_state, expire=600)
    
    return f'{authorization_url}&state={encoded_state}'

async def oauth2callback_hubspot(request: Request):
    if request.query_params.get('error'):
        raise HTTPException(status_code=400, detail=request.query_params.get('error'))
    
    code = request.query_params.get('code')
    encoded_state = request.query_params.get('state')
    state_data = json.loads(encoded_state)

    original_state = state_data.get('state')
    user_id = state_data.get('user_id')
    org_id = state_data.get('org_id')

    saved_state = await get_value_redis(f'hubspot_state:{org_id}:{user_id}')

    if not saved_state or original_state != json.loads(saved_state).get('state'):
        raise HTTPException(status_code=400, detail='State does not match.')

    async with httpx.AsyncClient() as client:
        response, _ = await asyncio.gather(
            client.post(
                'https://api.hubapi.com/oauth/v1/token',
                data={
                    'grant_type': 'authorization_code',
                    'client_id': CLIENT_ID,
                    'client_secret': CLIENT_SECRET,
                    'code': code,
                    'redirect_uri': REDIRECT_URI
                }
            ),
            delete_key_redis(f'hubspot_state:{org_id}:{user_id}')
        )

    await add_key_value_redis(
        f'hubspot_credentials:{org_id}:{user_id}',
        json.dumps(response.json()),
        expire=600
    )

    close_window_script = """
    <html>
        <script>
            window.close();
        </script>
    </html>
    """
    return HTMLResponse(content=close_window_script)

async def get_hubspot_credentials(user_id, org_id):
    credentials = await get_value_redis(f'hubspot_credentials:{org_id}:{user_id}')
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found.')
    
    credentials = json.loads(credentials)
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found.')
    
    await delete_key_redis(f'hubspot_credentials:{org_id}:{user_id}')
    return credentials

def create_integration_item_metadata_object(contact_data: dict) -> IntegrationItem:
    """Creates an integration metadata object from a HubSpot contact"""
    return IntegrationItem(
        id=str(contact_data['id']),
        type='contact',
        name=contact_data.get('properties', {}).get('name', 'Unknown Contact'),
        creation_time=contact_data.get('createdAt'),
        last_modified_time=contact_data.get('updatedAt'),
        parent_id=None
    )

async def get_items_hubspot(credentials) -> list[IntegrationItem]:
    """Retrieves all contacts from HubSpot"""
    if not isinstance(credentials, dict):
        credentials = json.loads(credentials)
    
    access_token = credentials.get('access_token')
    if not access_token:
        raise HTTPException(status_code=400, detail='Invalid credentials')

    async with httpx.AsyncClient() as client:
        response = await client.get(
            'https://api.hubapi.com/crm/v3/objects/contacts',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail='Failed to fetch HubSpot contacts'
            )

        data = response.json()
        contacts = data.get('results', [])
        
        return [create_integration_item_metadata_object(contact) for contact in contacts]
