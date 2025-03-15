from typing import Optional, Dict, List
import httpx
from datetime import datetime
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import json
import logging
import os
import secrets
import asyncio
from .integration_item import IntegrationItem
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

def get_hubspot_config():
    """Get HubSpot configuration from environment variables"""
    client_id = os.environ.get('HUBSPOT_CLIENT_ID')
    client_secret = os.environ.get('HUBSPOT_CLIENT_SECRET')
    redirect_uri = os.environ.get('HUBSPOT_REDIRECT_URI')
    
    if not all([client_id, client_secret, redirect_uri]):
        logger.warning("HubSpot environment variables not configured")
        return None, None, None
        
    return client_id, client_secret, redirect_uri

async def authorize_hubspot(user_id: str, org_id: str) -> str:
    """Initialize HubSpot OAuth flow"""
    client_id, _, redirect_uri = get_hubspot_config()
    if not client_id:
        raise HTTPException(status_code=503, detail="HubSpot integration not configured")
        
    # Generate a secure state with a random token to prevent CSRF
    state = {
        'state': secrets.token_urlsafe(32),
        'user_id': user_id,
        'org_id': org_id
    }
    
    # Store state in Redis
    await add_key_value_redis(
        f'hubspot_state:{org_id}:{user_id}', 
        json.dumps(state),
        expire=600
    )
    
    scopes = "contacts crm.objects.contacts.read"
    auth_url = (
        f"https://app.hubspot.com/oauth/authorize?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"scope={scopes}&"
        f"state={json.dumps(state)}"
    )
    
    return auth_url

async def oauth2callback_hubspot(request: Request):
    """Handle HubSpot OAuth callback"""
    if request.query_params.get('error'):
        raise HTTPException(status_code=400, detail=request.query_params.get('error'))
    
    code = request.query_params.get('code')
    encoded_state = request.query_params.get('state')
    if not code or not encoded_state:
        raise HTTPException(status_code=400, detail="Missing code or state parameters")
    
    # Parse the state parameter
    try:
        state_data = json.loads(encoded_state)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    original_state = state_data.get('state')
    user_id = state_data.get('user_id')
    org_id = state_data.get('org_id')

    if not all([original_state, user_id, org_id]):
        raise HTTPException(status_code=400, detail="Incomplete state data")

    # Verify state against Redis
    saved_state_str = await get_value_redis(f'hubspot_state:{org_id}:{user_id}')
    if not saved_state_str:
        raise HTTPException(status_code=400, detail="State not found or expired")

    saved_state = json.loads(saved_state_str)
    if original_state != saved_state.get('state'):
        raise HTTPException(status_code=400, detail="State mismatch")

    # Get configuration
    client_id, client_secret, redirect_uri = get_hubspot_config()
    if not all([client_id, client_secret, redirect_uri]):
        raise HTTPException(status_code=503, detail="HubSpot integration not configured")

    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        response, _ = await asyncio.gather(
            client.post(
                'https://api.hubapi.com/oauth/v1/token',
                data={
                    'grant_type': 'authorization_code',
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'code': code,
                    'redirect_uri': redirect_uri
                }
            ),
            delete_key_redis(f'hubspot_state:{org_id}:{user_id}')
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to get access token: {response.text}"
        )

    credentials = response.json()
    await add_key_value_redis(
        f'hubspot_credentials:{org_id}:{user_id}',
        json.dumps(credentials),
        expire=600  # Credentials expire after 10 minutes; adjust as needed
    )

    close_window_script = """
    <html>
        <script>
            window.close();
        </script>
    </html>
    """
    return HTMLResponse(content=close_window_script)

async def get_hubspot_credentials(user_id: str, org_id: str) -> Dict:
    """Retrieve stored HubSpot credentials"""
    credentials = await get_value_redis(f'hubspot_credentials:{org_id}:{user_id}')
    if not credentials:
        raise HTTPException(status_code=404, detail="No credentials found")
        
    return json.loads(credentials)

class HubspotIntegration:
    def __init__(self, credentials: Dict[str, str]):
        self.access_token = credentials.get('access_token')
        self.hub_domain = credentials.get('hub_domain')

    async def get_contacts(self, limit: int = 100) -> List[IntegrationItem]:
        """Fetch contacts from HubSpot CRM"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://api.hubapi.com/crm/v3/objects/contacts',
                params={'limit': limit},
                headers={
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch HubSpot contacts"
                )
                
            data = response.json()
            contacts = []
            
            for contact in data.get('results', []):
                contact_props = contact.get('properties', {})
                contacts.append(
                    IntegrationItem(
                        id=contact['id'],
                        name=f"{contact_props.get('firstname', '')} {contact_props.get('lastname', '')}".strip(),
                        type='contact',
                        email=contact_props.get('email'),
                        company=contact_props.get('company'),
                        last_modified_time=datetime.fromisoformat(contact['updatedAt'].replace('Z', '+00:00')) if contact.get('updatedAt') else None,
                        creation_time=datetime.fromisoformat(contact['createdAt'].replace('Z', '+00:00')) if contact.get('createdAt') else None
                    )
                )
            
            return contacts

async def get_items_hubspot(credentials: Dict) -> List[IntegrationItem]:
    """Fetch HubSpot items (contacts)"""
    try:
        integration = HubspotIntegration(credentials)
        contacts = await integration.get_contacts()
        return contacts
    except Exception as e:
        logger.error(f"Error fetching HubSpot items: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch HubSpot items")