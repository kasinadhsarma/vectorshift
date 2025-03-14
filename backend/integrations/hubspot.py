<<<<<<< Updated upstream
# HubSpot OAuth integration
import json
import secrets
import os
=======
# hubspot.py

import json
import secrets
>>>>>>> Stashed changes
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import asyncio
import requests
<<<<<<< Updated upstream
from dotenv import load_dotenv
from integrations.integration_item import IntegrationItem
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

load_dotenv()

CLIENT_ID = os.getenv('HUBSPOT_CLIENT_ID')
CLIENT_SECRET = os.getenv('HUBSPOT_CLIENT_SECRET')
REDIRECT_URI = os.getenv('HUBSPOT_REDIRECT_URI')
AUTHORIZATION_URL = f'https://app.hubspot.com/oauth/authorize'

async def authorize_hubspot(user_id, org_id):
    state = secrets.token_urlsafe(32)
    state_data = {
        'state': state,
        'user_id': user_id,
        'org_id': org_id
    }
    encoded_state = json.dumps(state_data)
    await add_key_value_redis(f'hubspot_state:{org_id}:{user_id}', encoded_state, expire=600)
    
    auth_url = f'{AUTHORIZATION_URL}?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=crm.objects.contacts.read&state={state}'
    return auth_url

async def oauth2callback_hubspot(request: Request):
    if request.query_params.get('error'):
        raise HTTPException(status_code=400, detail=request.query_params.get('error_description'))
=======
from integrations.integration_item import IntegrationItem

from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

CLIENT_ID = '4ae1421f-b957-4ea5-beaa-45e9378c2854'
CLIENT_SECRET = 'f77688ab-9292-45ac-8ce4-749b21fec157'
REDIRECT_URI = 'http://localhost:8000/integrations/hubspot/oauth2callback'
AUTHORIZATION_URL = f'https://app.hubspot.com/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=contacts'

async def authorize_hubspot(user_id, org_id):
    state_data = {
        'state': secrets.token_urlsafe(32),
        'user_id': user_id,
        'org_id': org_id
    }
    encoded_state = json.dumps(state_data)
    await add_key_value_redis(f'hubspot_state:{org_id}:{user_id}', encoded_state, expire=600)
    
    return f'{AUTHORIZATION_URL}&state={encoded_state}'

async def oauth2callback_hubspot(request: Request):
    if request.query_params.get('error'):
        raise HTTPException(status_code=400, detail=request.query_params.get('error'))
>>>>>>> Stashed changes
    
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
                    'redirect_uri': REDIRECT_URI,
                    'code': code
<<<<<<< Updated upstream
                },
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            ),
            delete_key_redis(f'hubspot_state:{org_id}:{user_id}'),
=======
                }
            ),
            delete_key_redis(f'hubspot_state:{org_id}:{user_id}')
>>>>>>> Stashed changes
        )

    await add_key_value_redis(f'hubspot_credentials:{org_id}:{user_id}', json.dumps(response.json()), expire=600)
    
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
    await delete_key_redis(f'hubspot_credentials:{org_id}:{user_id}')

    return credentials

<<<<<<< Updated upstream
def create_integration_item_metadata_object(contact, parent_id=None):
    """Creates an integration metadata object from a HubSpot contact"""
    return IntegrationItem(
        id=str(contact['id']),
        type='contact',
        name=f"{contact.get('properties', {}).get('firstname', '')} {contact.get('properties', {}).get('lastname', '')}",
        creation_time=contact.get('properties', {}).get('createdate'),
        last_modified_time=contact.get('properties', {}).get('lastmodifieddate'),
        parent_id=parent_id
    )

async def get_items_hubspot(credentials) -> list[IntegrationItem]:
    """Fetch contact data from HubSpot"""
    credentials = json.loads(credentials)
    access_token = credentials.get('access_token')
    
    if not access_token:
        raise HTTPException(status_code=400, detail='Invalid credentials')

    try:
        response = requests.get(
            'https://api.hubapi.com/crm/v3/objects/contacts',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        response.raise_for_status()
        
        contacts = response.json().get('results', [])
        return [create_integration_item_metadata_object(contact) for contact in contacts]
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=str(e))

=======
def create_integration_item_metadata_object(response_json: dict) -> IntegrationItem:
    """Creates an integration metadata object from the HubSpot response"""
    return IntegrationItem(
        id=str(response_json.get('id')),
        name=response_json.get('properties', {}).get('name', 'Unknown'),
        type='Contact',
        creation_time=response_json.get('createdAt'),
        last_modified_time=response_json.get('updatedAt')
    )

async def get_items_hubspot(credentials) -> list[IntegrationItem]:
    """Aggregates contacts from HubSpot"""
    credentials = json.loads(credentials)
    response = requests.get(
        'https://api.hubapi.com/crm/v3/objects/contacts',
        headers={'Authorization': f'Bearer {credentials.get("access_token")}'}
    )

    if response.status_code == 200:
        results = response.json().get('results', [])
        return [create_integration_item_metadata_object(result) for result in results]
    
    return []
>>>>>>> Stashed changes
