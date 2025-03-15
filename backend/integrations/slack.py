from fastapi import HTTPException, Request
import os
import jwt
from slack_sdk import WebClient
from slack_sdk.oauth import AuthorizeUrlGenerator, OpenIDConnectAuthorizeUrlGenerator
from slack_sdk.oauth.installation_store import Installation
from cassandra_client import CassandraClient
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import httpx
import json
import logging
from .integration_item import IntegrationItem
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)

db_client = CassandraClient()

def get_slack_config():
    """Get Slack configuration from environment variables"""
    client_id = os.environ.get('SLACK_CLIENT_ID')
    client_secret = os.environ.get('SLACK_CLIENT_SECRET')
    redirect_uri = os.environ.get('SLACK_REDIRECT_URI')
    
    if not all([client_id, client_secret, redirect_uri]):
        logger.warning("Slack environment variables not configured")
        return None, None, None
        
    return client_id, client_secret, redirect_uri

async def authorize_slack(user_id: str, org_id: str) -> str:
    """Initialize Slack OAuth flow"""
    client_id, _, redirect_uri = get_slack_config()
    if not client_id:
        raise HTTPException(status_code=503, detail="Slack integration not configured")
        
    state = {
        'user_id': user_id,
        'org_id': org_id
    }
    
    # Store state in Redis
    await add_key_value_redis(
        f'slack_state:{org_id}:{user_id}', 
        json.dumps(state),
        expire=600
    )
    
    scopes = "channels:read,channels:history,groups:read,im:read,mpim:read"
    auth_url = f"https://slack.com/oauth/v2/authorize?client_id={client_id}&scope={scopes}&redirect_uri={redirect_uri}"
    
    return auth_url

async def oauth2callback_slack(request: Request):
    """Handle Slack OAuth callback"""
    if request.query_params.get('error'):
        raise HTTPException(status_code=400, detail=request.query_params.get('error'))
        
    code = request.query_params.get('code')
    state_data = json.loads(request.query_params.get('state', '{}'))
    
    user_id = state_data.get('user_id')
    org_id = state_data.get('org_id')
    
    if not all([code, user_id, org_id]):
        raise HTTPException(status_code=400, detail="Missing required parameters")

    client_id, client_secret, redirect_uri = get_slack_config()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            'https://slack.com/api/oauth.v2.access',
            data={
                'client_id': client_id,
                'client_secret': client_secret,
                'code': code,
                'redirect_uri': redirect_uri
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to get access token")
            
        data = response.json()
        if not data.get('ok'):
            raise HTTPException(status_code=400, detail=data.get('error'))
            
        credentials = {
            'access_token': data['access_token'],
            'team_id': data['team']['id'],
            'team_name': data['team']['name']
        }
        
        # Store credentials in Redis
        await add_key_value_redis(
            f'slack_credentials:{org_id}:{user_id}',
            json.dumps(credentials),
            expire=None
        )
        
        close_window_script = """
        <html>
            <script>
                window.opener.postMessage({type: 'SLACK_AUTH_SUCCESS'}, '*');
                window.close();
            </script>
        </html>
        """
        return HTMLResponse(content=close_window_script)

async def get_slack_credentials(user_id: str, org_id: str) -> Dict:
    """Retrieve stored Slack credentials"""
    credentials = await get_value_redis(f'slack_credentials:{org_id}:{user_id}')
    if not credentials:
        raise HTTPException(status_code=404, detail="No credentials found")
        
    return json.loads(credentials)

class SlackIntegration:
    def __init__(self, credentials: Dict[str, str]):
        self.access_token = credentials['access_token']
        self.team_id = credentials.get('team_id')
        self.team_name = credentials.get('team_name')

    async def list_channels(self) -> List[IntegrationItem]:
        """List all channels in the workspace"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://slack.com/api/conversations.list',
                headers={'Authorization': f'Bearer {self.access_token}'},
                params={
                    'types': 'public_channel,private_channel',
                    'exclude_archived': True,
                    'limit': 100
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch channels"
                )
                
            data = response.json()
            if not data.get('ok'):
                raise HTTPException(status_code=400, detail=data.get('error'))
                
            channels = []
            for channel in data.get('channels', []):
                channels.append(
                    IntegrationItem(
                        id=channel['id'],
                        name=channel['name'],
                        type='channel',
                        creation_time=datetime.fromtimestamp(channel['created']),
                        visibility=not channel.get('is_private', False)
                    )
                )
                
            return channels

    async def get_channel_messages(self, channel_id: str, limit: int = 100) -> List[Dict]:
        """Get messages from a specific channel"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://slack.com/api/conversations.history',
                headers={'Authorization': f'Bearer {self.access_token}'},
                params={
                    'channel': channel_id,
                    'limit': limit
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch messages"
                )
                
            data = response.json()
            if not data.get('ok'):
                raise HTTPException(status_code=400, detail=data.get('error'))
                
            return data.get('messages', [])

    async def sync_data(self) -> Dict:
        """Sync all available data from Slack"""
        try:
            channels = await self.list_channels()
            
            return {
                "status": "success",
                "data": {
                    "channels": channels,
                    "team_name": self.team_name,
                    "team_id": self.team_id
                }
            }
        except Exception as e:
            logger.error(f"Error syncing Slack data: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
