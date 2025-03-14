# slack.py

import json
import secrets
import logging
from typing import List
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import asyncio
import requests
from integrations.integration_item import IntegrationItem
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OAuth Configuration
CLIENT_ID = '7391038863203.8587488877844'
CLIENT_SECRET = 'b6374ab25d8870b3087be888b0f9778b'
REDIRECT_URI = 'http://localhost:8000/integrations/slack/oauth2callback'

<<<<<<< HEAD
# Define required scopes
SCOPES = [
    'channels:read',
    'channels:history',
    'chat:write',
    'team:read',
    'users:read'
]

async def authorize_slack(user_id: str, org_id: str):
    """Generate OAuth URL and store state"""
    try:
        logger.info(f"Generating Slack OAuth URL for user {user_id}")
        
        state_data = {
            'state': secrets.token_urlsafe(32),
            'user_id': user_id,
            'org_id': org_id
        }
        encoded_state = json.dumps(state_data)
        
        # Store state with 10 minute expiry
        await add_key_value_redis(
            f'slack_state:{org_id}:{user_id}',
            encoded_state,
            expire=600
        )
        
        # Build authorization URL
        auth_url = (
            'https://slack.com/oauth/v2/authorize'
            f'?client_id={CLIENT_ID}'
            f'&redirect_uri={REDIRECT_URI}'
            f'&scope={",".join(SCOPES)}'
            f'&state={encoded_state}'
        )
        
        logger.info("Successfully generated authorization URL")
        return {"url": auth_url}
        
    except Exception as e:
        logger.error(f"Error generating authorization URL: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate authorization URL: {str(e)}"
        )

async def oauth2callback_slack(request: Request):
    """Handle OAuth callback and store credentials"""
    try:
        # Check for OAuth errors
        error = request.query_params.get('error')
        if error:
            logger.error(f"OAuth error: {error}")
            raise HTTPException(status_code=400, detail=error)
        
        # Get and validate parameters
        code = request.query_params.get('code')
        encoded_state = request.query_params.get('state')
        
        if not code or not encoded_state:
            logger.error("Missing required parameters")
            raise HTTPException(status_code=400, detail="Missing required parameters")
        
        # Parse and validate state
        try:
            state_data = json.loads(encoded_state)
            original_state = state_data.get('state')
            user_id = state_data.get('user_id')
            org_id = state_data.get('org_id')
            
            if not all([original_state, user_id, org_id]):
                raise ValueError("Invalid state format")
                
        except Exception as e:
            logger.error(f"Invalid state format: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid state format")
        
        # Verify stored state
        saved_state = await get_value_redis(f'slack_state:{org_id}:{user_id}')
        if not saved_state or original_state != json.loads(saved_state).get('state'):
            logger.error("State mismatch")
            raise HTTPException(status_code=400, detail="State mismatch")
        
        # Exchange code for access token
        async with httpx.AsyncClient() as client:
            logger.info("Exchanging code for access token")
            
=======
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
>>>>>>> origin/main
            response = await client.post(
                'https://slack.com/api/oauth.v2.access',
                data={
                    'code': code,
                    'client_id': CLIENT_ID,
                    'client_secret': CLIENT_SECRET,
                    'redirect_uri': REDIRECT_URI
                }
<<<<<<< HEAD
            )
            
            if response.status_code != 200:
                logger.error(f"Token exchange failed: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to exchange code for access token"
                )
                
            # Store credentials
            credentials = response.json()
            await add_key_value_redis(
                f'slack_credentials:{org_id}:{user_id}',
                json.dumps(credentials),
                expire=None  # No expiry for credentials
            )
            
            logger.info("Successfully stored credentials")
            
            # Cleanup state
            await delete_key_redis(f'slack_state:{org_id}:{user_id}')
            
            return HTMLResponse(content="""
                <html>
                    <script>
                        if (window.opener) {
                            window.opener.postMessage({ type: "SLACK_AUTH_SUCCESS" }, "*");
                            window.close();
                        }
                    </script>
                    <body>
                        Authentication successful! You can close this window.
                    </body>
                </html>
            """)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in OAuth callback: {str(e)}")
        return HTMLResponse(content=f"""
            <html>
                <script>
                    if (window.opener) {{
                        window.opener.postMessage({{ 
                            type: "SLACK_AUTH_ERROR",
                            error: "{str(e)}"
                        }}, "*");
                        window.close();
                    }}
                </script>
                <body>
                    Authentication failed: {str(e)}
                    <br>
                    You can close this window.
                </body>
            </html>
        """)

async def get_slack_credentials(user_id: str, org_id: str):
    """Get stored Slack credentials"""
    try:
        logger.info(f"Getting Slack credentials for user {user_id}")
        credentials = await get_value_redis(f'slack_credentials:{org_id}:{user_id}')
        
        if not credentials:
            logger.info("No credentials found")
            return None
            
        creds_data = json.loads(credentials)
        
        # Clear stored credentials after retrieval
        await delete_key_redis(f'slack_credentials:{org_id}:{user_id}')
        
        return creds_data
        
    except Exception as e:
        logger.error(f"Error getting credentials: {str(e)}")
        return None

async def get_items_slack(credentials) -> List[IntegrationItem]:
    """Fetch and format Slack channels"""
    try:
        # Handle both string and dict credentials
        if isinstance(credentials, str):
            credentials = json.loads(credentials)
        
        access_token = credentials.get('access_token')
        if not access_token:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials: missing access token"
            )
            
        logger.info("Fetching Slack channels")
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://slack.com/api/conversations.list',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch channels: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch Slack channels"
                )
                
            data = response.json()
            if not data.get('ok', False):
                logger.error(f"Slack API error: {data.get('error', 'Unknown error')}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Slack API error: {data.get('error')}"
                )
                
            channels = data.get('channels', [])
            items = [
                IntegrationItem(
                    id=channel['id'],
                    type='channel',
                    name=channel['name'],
                    creation_time=channel.get('created'),
                    last_modified_time=None,  # Slack doesn't provide this
                    visibility=not channel.get('is_private', True),
                    parent_id=None
                )
                for channel in channels
            ]
            
            logger.info(f"Retrieved {len(items)} Slack channels")
            return items
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Slack items: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Slack items: {str(e)}"
        )
=======
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
>>>>>>> origin/main
