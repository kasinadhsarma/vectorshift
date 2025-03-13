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
    random_part = secrets.token_urlsafe(16)
    state = f"{random_part}.{org_id}.{user_id}"
    state_data = {
        'state': state,
        'user_id': user_id,
        'org_id': org_id
    }
    encoded_state = json.dumps(state_data)
    await add_key_value_redis(f'slack_state:{org_id}:{user_id}', encoded_state, expire=600)
    
    scope = 'channels:read%2Cchat:write%2Cteam:read%2Cusers:read'
    auth_url = f'{AUTHORIZATION_URL}?client_id={CLIENT_ID}&scope={scope}&redirect_uri={REDIRECT_URI}&state={state}'
    return {"url": auth_url}

async def oauth2callback_slack(request: Request):
    if request.query_params.get('error'):
        raise HTTPException(status_code=400, detail=request.query_params.get('error'))
    
    code = request.query_params.get('code')
    state = request.query_params.get('state')
    
    # First get the saved state data from Redis
    if not state:
        raise HTTPException(status_code=400, detail='Missing state parameter')

    # Decode the state to get user_id and org_id
    try:
        state_parts = state.split('.')
        if len(state_parts) != 3:  # Expecting format: random.org_id.user_id
            raise HTTPException(status_code=400, detail='Invalid state format')
        _, org_id, user_id = state_parts
        
        # Get state data from Redis using org_id and user_id
        saved_state = await get_value_redis(f'slack_state:{org_id}:{user_id}')
        if not saved_state:
            raise HTTPException(status_code=400, detail='Invalid or expired state')
            
        state_data = json.loads(saved_state)
        if state != state_data.get('state'):
            raise HTTPException(status_code=400, detail='State mismatch')
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=400, detail='Invalid state data format')

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                'https://slack.com/api/oauth.v2.access',
                data={
                    'code': code,
                    'client_id': CLIENT_ID,
                    'client_secret': CLIENT_SECRET,
                    'redirect_uri': REDIRECT_URI
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f'Slack API error: {response.text}'
                )
            
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=500,
                    detail='Invalid JSON response from Slack'
                )
                
            if not response_data.get('ok', False):
                if response_data.get('error') == 'invalid_scope':
                    raise HTTPException(
                        status_code=400,
                        detail='Invalid scope provided for Slack authorization'
                    )
                raise HTTPException(
                    status_code=400,
                    detail=f"Slack error: {response_data.get('error', 'Unknown error')}"
                )
                
            await add_key_value_redis(
                f'slack_credentials:{org_id}:{user_id}',
                json.dumps(response_data),
                expire=3600
            )
            
            await delete_key_redis(f'slack_state:{org_id}:{user_id}')
            
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500,
                detail=f'Failed to connect to Slack: {str(e)}'
            )
    
    return HTMLResponse(content="<html><script>window.close();</script></html>")

async def get_slack_credentials(user_id: str, org_id: str) -> dict:
    """Get Slack credentials using the standardized credentials function."""
    from redis_client import get_credentials
    return await get_credentials('slack', user_id, org_id)

async def get_items_slack(credentials) -> dict:
    if isinstance(credentials, str):
        try:
            credentials = json.loads(credentials)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail='Invalid credentials format')
    
    access_token = credentials.get('access_token')
    if not access_token:
        raise HTTPException(status_code=400, detail='Invalid credentials')

    headers = {'Authorization': f'Bearer {access_token}'}
    
    async with httpx.AsyncClient() as client:
        try:
            responses = await asyncio.gather(
                client.get('https://slack.com/api/conversations.list', headers=headers),
                client.get('https://slack.com/api/users.list', headers=headers),
                client.get('https://slack.com/api/team.info', headers=headers)
            )
            
            channels_resp, users_resp, team_resp = responses
            
            for resp in responses:
                if resp.status_code != 200 or not resp.json().get('ok', False):
                    error_msg = resp.json().get('error', 'Unknown error')
                    raise HTTPException(status_code=400, detail=f'Slack API error: {error_msg}')
            
            channels_data = channels_resp.json()
            channels = [
                {
                    'id': channel['id'],
                    'name': channel['name'],
                    'description': channel.get('topic', {}).get('value', ''),
                    'members': channel.get('num_members', 0),
                    'is_private': channel['is_private'],
                    'created': channel.get('created')
                }
                for channel in channels_data.get('channels', [])
            ]
            
            users_data = users_resp.json()
            users = [
                {
                    'id': user['id'],
                    'name': user['name'],
                    'real_name': user.get('real_name', ''),
                    'email': user.get('profile', {}).get('email', ''),
                    'title': user.get('profile', {}).get('title', ''),
                    'status_text': user.get('profile', {}).get('status_text', ''),
                    'status_emoji': user.get('profile', {}).get('status_emoji', '')
                }
                for user in users_data.get('members', [])
                if not user.get('is_bot') and not user.get('deleted')
            ]
            
            team_data = team_resp.json()
            team_info = {
                'id': team_data['team']['id'],
                'name': team_data['team']['name'],
                'domain': team_data['team'].get('domain', ''),
                'email_domain': team_data['team'].get('email_domain', '')
            }
            
            return {
                'isConnected': True,
                'status': 'active',
                'channels': channels,
                'users': users,
                'team': team_info,
                'credentials': credentials
            }
            
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f'Failed to fetch Slack data: {str(e)}')
