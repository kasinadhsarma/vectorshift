from fastapi import HTTPException
import os
import jwt
from slack_sdk import WebClient
from slack_sdk.oauth import AuthorizeUrlGenerator, OpenIDConnectAuthorizeUrlGenerator
from slack_sdk.oauth.installation_store import Installation
from cassandra_client import CassandraClient
from datetime import datetime, timedelta

db_client = CassandraClient()

async def authorize_slack(user_id: str, org_id: str):
    """Initialize Slack OAuth flow"""
    try:
        client_id = os.getenv('SLACK_CLIENT_ID')
        redirect_uri = os.getenv('SLACK_REDIRECT_URI')
        scope = "channels:read,groups:read,chat:write"
        
        generator = AuthorizeUrlGenerator(
            client_id=client_id,
            scopes=[scope],
            redirect_uri=redirect_uri,
        )
        
        state = jwt.encode({'user_id': user_id, 'org_id': org_id}, os.getenv('SESSION_SECRET'))
        authorize_url = generator.generate(state=state)
        
        return {"url": authorize_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def oauth2callback_slack(request):
    """Handle Slack OAuth callback"""
    try:
        code = request.query_params.get('code')
        state = request.query_params.get('state')
        error = request.query_params.get('error')

        if error:
            raise HTTPException(status_code=400, detail=f"Slack OAuth error: {error}")

        if not code:
            raise HTTPException(status_code=400, detail="Missing authorization code")

        # Decode state to get user_id and org_id
        try:
            decoded_state = jwt.decode(state, os.getenv('SESSION_SECRET'), algorithms=['HS256'])
            user_id = decoded_state['user_id']
            org_id = decoded_state['org_id']
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid state parameter")

        # Exchange code for access token
        client_id = os.getenv('SLACK_CLIENT_ID')
        client_secret = os.getenv('SLACK_CLIENT_SECRET')
        redirect_uri = os.getenv('SLACK_REDIRECT_URI')

        slack_client = WebClient()
        response = await slack_client.oauth_v2_access_async(
            client_id=client_id,
            client_secret=client_secret,
            code=code,
            redirect_uri=redirect_uri
        )

        result = response.data
        if not result.get('ok', False):
            raise HTTPException(status_code=400, detail=f"Slack error: {result.get('error')}")

        # Store credentials
        access_token = result['access_token']
        expires_at = (datetime.now() + timedelta(days=90)).isoformat()

        credentials = {
            'access_token': access_token,
            'expires_at': expires_at,
            'workspace_id': result.get('team', {}).get('id'),
            'workspace_name': result.get('team', {}).get('name')
        }

        if not db_client.session:
            await db_client.connect()

        query = """
            INSERT INTO integration_credentials (user_id, org_id, integration_type, credentials)
            VALUES (%s, %s, %s, %s)
        """
        future = await db_client.session.execute_async(query, [user_id, org_id, 'slack', str(credentials)])
        await future.result()

        return {"success": True}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def get_slack_credentials(user_id: str, org_id: str):
    """Retrieve Slack credentials for a user"""
    try:
        if not db_client.session:
            await db_client.connect()

        query = """
            SELECT credentials
            FROM integration_credentials
            WHERE user_id = %s AND org_id = %s AND integration_type = 'slack'
            LIMIT 1
        """
        rows = await (await db_client.session.execute_async(query, [user_id, org_id])).all()
        
        if not rows:
            return None
            
        return rows[0].credentials
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def get_items_slack(credentials: str):
    """Get Slack channels and messages"""
    try:
        # Parse credentials string to dict if needed
        if isinstance(credentials, str):
            try:
                credentials = eval(credentials)
            except:
                raise HTTPException(status_code=400, detail="Invalid credentials format")

        access_token = credentials.get('access_token')
        if not access_token:
            raise HTTPException(status_code=400, detail="Access token not found in credentials")

        slack_client = WebClient(token=access_token)
        
        # Get channels
        try:
            response = await slack_client.conversations_list_async()
            result = response.data
            
            if not result.get('ok', False):
                raise HTTPException(status_code=400, detail=f"Slack API error: {result.get('error')}")

            channels = [{
                'id': channel['id'],
                'name': channel['name'],
                'visibility': not channel['is_private'],
                'creation_time': datetime.fromtimestamp(channel['created']).isoformat(),
                'type': 'channel'
            } for channel in result.get('channels', [])]

            return channels
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error fetching Slack channels: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
