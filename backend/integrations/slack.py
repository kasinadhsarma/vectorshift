"""Slack integration module."""
import json
import secrets
import logging
from typing import Dict, List, Optional, Any
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import asyncio
from integrations.integration_item import IntegrationItem, IntegrationItemParameter
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OAuth Configuration
CLIENT_ID = '7391038863203.8587488877844'
CLIENT_SECRET = 'b6374ab25d8870b3087be888b0f9778b'
REDIRECT_URI = 'http://localhost:8000/integrations/slack/oauth2callback'
AUTHORIZATION_URL = 'https://slack.com/oauth/v2/authorize'
TOKEN_URL = 'https://slack.com/api/oauth.v2.access'

# API endpoints
CONVERSATIONS_LIST_URL = 'https://slack.com/api/conversations.list'
USERS_LIST_URL = 'https://slack.com/api/users.list'
TEAM_INFO_URL = 'https://slack.com/api/team.info'

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
        
        # Generate state with random component for extra security
        random_part = secrets.token_urlsafe(16)
        state = f"{random_part}.{org_id}.{user_id}"
        state_data = {
            'state': state,
            'user_id': user_id,
            'org_id': org_id
        }
        
        # Store state with 10 minute expiry
        await add_key_value_redis(
            f'slack_state:{org_id}:{user_id}',
            json.dumps(state_data),
            expire=600
        )
        
        # Build authorization URL
        auth_url = (
            f'{AUTHORIZATION_URL}'
            f'?client_id={CLIENT_ID}'
            f'&redirect_uri={REDIRECT_URI}'
            f'&scope={",".join(SCOPES)}'
            f'&state={state}'
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
        state = request.query_params.get('state')
        
        if not state:
            logger.error("Missing state parameter")
            raise HTTPException(status_code=400, detail="Missing state parameter")
            
        # Parse state to get user_id and org_id
        try:
            state_parts = state.split('.')
            if len(state_parts) != 3:  # Expecting format: random.org_id.user_id
                raise ValueError("Invalid state format")
            _, org_id, user_id = state_parts
        except Exception as e:
            logger.error(f"Invalid state format: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid state format")
        
        # Verify stored state
        saved_state = await get_value_redis(f'slack_state:{org_id}:{user_id}')
        if not saved_state:
            logger.error("State expired or invalid")
            raise HTTPException(status_code=400, detail="State expired or invalid")
            
        state_data = json.loads(saved_state)
        if state != state_data.get('state'):
            logger.error("State mismatch")
            raise HTTPException(status_code=400, detail="State mismatch")
        
        # Exchange code for access token
        async with httpx.AsyncClient() as client:
            logger.info("Exchanging code for access token")
            
            response = await client.post(
                TOKEN_URL,
                data={
                    'code': code,
                    'client_id': CLIENT_ID,
                    'client_secret': CLIENT_SECRET,
                    'redirect_uri': REDIRECT_URI
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Token exchange failed: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Slack API error: {response.text}"
                )
            
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                logger.error("Invalid JSON response from Slack")
                raise HTTPException(
                    status_code=500,
                    detail="Invalid JSON response from Slack"
                )
            
            if not response_data.get('ok', False):
                error_msg = response_data.get('error', 'Unknown error')
                logger.error(f"Slack API error: {error_msg}")
                
                if error_msg == 'invalid_scope':
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid scope provided for Slack authorization"
                    )
                raise HTTPException(
                    status_code=400,
                    detail=f"Slack error: {error_msg}"
                )
            
            # Store credentials
            await add_key_value_redis(
                f'slack_credentials:{org_id}:{user_id}',
                json.dumps(response_data),
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

async def get_slack_credentials(user_id: str, org_id: str) -> Optional[Dict[str, Any]]:
    """Get stored Slack credentials"""
    try:
        logger.info(f"Getting Slack credentials for user {user_id}")
        credentials = await get_value_redis(f'slack_credentials:{org_id}:{user_id}')
        
        if not credentials:
            logger.info("No credentials found")
            return None
            
        return json.loads(credentials)
        
    except Exception as e:
        logger.error(f"Error getting credentials: {str(e)}")
        return None

async def get_items_slack(credentials: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch channels, users, and team info from Slack."""
    try:
        # Handle both string and dict credentials
        if isinstance(credentials, str):
            try:
                credentials = json.loads(credentials)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid credentials format")
        
        access_token = credentials.get('access_token')
        if not access_token:
            raise HTTPException(status_code=401, detail="Missing access token")
            
        headers = {'Authorization': f'Bearer {access_token}'}
        
        async with httpx.AsyncClient() as client:
            logger.info("Making parallel requests to Slack API")
            
            # Make parallel requests
            responses = await asyncio.gather(
                client.get(CONVERSATIONS_LIST_URL, headers=headers),
                client.get(USERS_LIST_URL, headers=headers),
                client.get(TEAM_INFO_URL, headers=headers)
            )
            
            channels_resp, users_resp, team_resp = responses
            
            # Check all responses for errors
            for resp in responses:
                if resp.status_code != 200:
                    logger.error(f"Slack API error: {resp.text}")
                    raise HTTPException(
                        status_code=resp.status_code,
                        detail=f"Slack API error: {resp.text}"
                    )
                    
                data = resp.json()
                if not data.get('ok', False):
                    error_msg = data.get('error', 'Unknown error')
                    logger.error(f"Slack API error: {error_msg}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Slack API error: {error_msg}"
                    )
            
            # Process channels
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
            
            # Process users
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
            
            # Process team info
            team_data = team_resp.json()
            team_info = {
                'id': team_data['team']['id'],
                'name': team_data['team']['name'],
                'domain': team_data['team'].get('domain', ''),
                'email_domain': team_data['team'].get('email_domain', '')
            }
            
            logger.info(f"Retrieved {len(channels)} channels and {len(users)} users")
            return {
                'isConnected': True,
                'status': 'active',
                'channels': channels,
                'users': users,
                'team': team_info,
                'credentials': credentials
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Slack data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch Slack data: {str(e)}"
        )
