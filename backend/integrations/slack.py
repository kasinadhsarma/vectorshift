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
