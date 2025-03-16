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

CLIENT_ID = os.getenv('SLACK_CLIENT_ID')
CLIENT_SECRET = os.getenv('SLACK_CLIENT_SECRET')
REDIRECT_URI = os.getenv('SLACK_REDIRECT_URI')
AUTHORIZATION_URL = 'https://slack.com/oauth/v2/authorize'

async def authorize_slack(user_id, org_id):
    state = secrets.token_urlsafe(32)
    state_data = {
        'state': state,
        'user_id': user_id,
        'org_id': org_id
    }
    encoded_state = json.dumps(state_data)
    await add_key_value_redis(f'slack_state:{org_id}:{user_id}', encoded_state, expire=600)
    
    scope = 'channels:read,chat:write,team:read,users:read'
    auth_url = f'{AUTHORIZATION_URL}?client_id={CLIENT_ID}&scope={scope}&redirect_uri={REDIRECT_URI}&state={state}'
    return auth_url

async def oauth2callback_slack(request: Request):
    if request.query_params.get('error'):
        raise HTTPException(status_code=400, detail=request.query_params.get('error'))
    
    code = request.query_params.get('code')
    state = request.query_params.get('state')
    state_data = json.loads(state)

    user_id = state_data.get('user_id')
    org_id = state_data.get('org_id')

    saved_state = await get_value_redis(f'slack_state:{org_id}:{user_id}')
    if not saved_state or state != json.loads(saved_state).get('state'):
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

