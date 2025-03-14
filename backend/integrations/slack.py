# slack.py

import json
import secrets
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import asyncio
import requests
from integrations.integration_item import IntegrationItem

from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

CLIENT_ID = '7391038863203.8587488877844'
CLIENT_SECRET = 'b6374ab25d8870b3087be888b0f9778b'
REDIRECT_URI = 'http://localhost:8000/integrations/slack/oauth2callback'
AUTHORIZATION_URL = f'https://slack.com/oauth/v2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=channels:read,channels:history,chat:write'

async def authorize_slack(user_id, org_id):
<<<<<<< Updated upstream
    state = secrets.token_urlsafe(32)
=======
>>>>>>> Stashed changes
    state_data = {
        'state': secrets.token_urlsafe(32),
        'user_id': user_id,
        'org_id': org_id
    }
    encoded_state = json.dumps(state_data)
    await add_key_value_redis(f'slack_state:{org_id}:{user_id}', encoded_state, expire=600)
    
<<<<<<< Updated upstream
    scope = 'channels:read,chat:write,team:read,users:read'
    auth_url = f'{AUTHORIZATION_URL}?client_id={CLIENT_ID}&scope={scope}&redirect_uri={REDIRECT_URI}&state={state}'
    return auth_url
=======
    return f'{AUTHORIZATION_URL}&state={encoded_state}'
>>>>>>> Stashed changes

async def oauth2callback_slack(request: Request):
    if request.query_params.get('error'):
        raise HTTPException(status_code=400, detail=request.query_params.get('error'))
    
    code = request.query_params.get('code')
<<<<<<< Updated upstream
    state = request.query_params.get('state')
    state_data = json.loads(state)

=======
    encoded_state = request.query_params.get('state')
    state_data = json.loads(encoded_state)

    original_state = state_data.get('state')
>>>>>>> Stashed changes
    user_id = state_data.get('user_id')
    org_id = state_data.get('org_id')

    saved_state = await get_value_redis(f'slack_state:{org_id}:{user_id}')
<<<<<<< Updated upstream
    if not saved_state or state != json.loads(saved_state).get('state'):
=======

    if not saved_state or original_state != json.loads(saved_state).get('state'):
>>>>>>> Stashed changes
        raise HTTPException(status_code=400, detail='State does not match.')

    async with httpx.AsyncClient() as client:
        response, _ = await asyncio.gather(
            client.post(
                'https://slack.com/api/oauth.v2.access',
                data={
                    'code': code,
                    'client_id': CLIENT_ID,
                    'client_secret': CLIENT_SECRET,
                    'redirect_uri': REDIRECT_URI
                }
            ),
<<<<<<< Updated upstream
            delete_key_redis(f'slack_state:{org_id}:{user_id}'),
        )

    await add_key_value_redis(f'slack_credentials:{org_id}:{user_id}', json.dumps(response.json()), expire=600)
    
    return HTMLResponse(content="<html><script>window.close();</script></html>")

async def get_slack_credentials(user_id, org_id):
    credentials = await get_value_redis(f'slack_credentials:{org_id}:{user_id}')
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found.')
    credentials = json.loads(credentials)
    await delete_key_redis(f'slack_credentials:{org_id}:{user_id}')
    return credentials

async def get_items_slack(credentials) -> list[IntegrationItem]:
    credentials = json.loads(credentials)
    access_token = credentials.get('access_token')
    
    if not access_token:
        raise HTTPException(status_code=400, detail='Invalid credentials')

    async with httpx.AsyncClient() as client:
        response = await client.get(
            'https://slack.com/api/conversations.list',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail='Failed to fetch Slack channels')

        channels = response.json().get('channels', [])
        return [
            IntegrationItem(
                id=channel['id'],
                type='channel',
                name=channel['name'],
                creation_time=channel.get('created'),
                visibility=not channel['is_private']
            )
            for channel in channels
        ]

=======
            delete_key_redis(f'slack_state:{org_id}:{user_id}')
        )

    await add_key_value_redis(f'slack_credentials:{org_id}:{user_id}', json.dumps(response.json()), expire=600)
    
    close_window_script = """
    <html>
        <script>
            window.close();
        </script>
    </html>
    """
    return HTMLResponse(content=close_window_script)

async def get_slack_credentials(user_id, org_id):
    credentials = await get_value_redis(f'slack_credentials:{org_id}:{user_id}')
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found.')
    credentials = json.loads(credentials)
    await delete_key_redis(f'slack_credentials:{org_id}:{user_id}')

    return credentials

def create_integration_item_metadata_object(response_json: dict) -> IntegrationItem:
    """Creates an integration metadata object from the Slack response"""
    return IntegrationItem(
        id=response_json.get('id'),
        name=response_json.get('name', 'Unknown'),
        type='Channel',
        creation_time=response_json.get('created'),
        directory=response_json.get('is_channel', False)
    )

async def get_items_slack(credentials) -> list[IntegrationItem]:
    """Aggregates channels from Slack workspace"""
    credentials = json.loads(credentials)
    response = requests.get(
        'https://slack.com/api/conversations.list',
        headers={'Authorization': f'Bearer {credentials.get("access_token")}'}
    )

    if response.status_code == 200 and response.json().get('ok'):
        channels = response.json().get('channels', [])
        return [create_integration_item_metadata_object(channel) for channel in channels]
    
    return []
>>>>>>> Stashed changes
