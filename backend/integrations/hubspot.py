# hubspot.py

import json
import secrets
import os
import logging
from typing import List
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import asyncio
import requests
from dotenv import load_dotenv
from integrations.integration_item import IntegrationItem
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# OAuth Configuration
CLIENT_ID = os.getenv('HUBSPOT_CLIENT_ID', '4ae1421f-b957-4ea5-beaa-45e9378c2854')
CLIENT_SECRET = os.getenv('HUBSPOT_CLIENT_SECRET', 'f77688ab-9292-45ac-8ce4-749b21fec157')
REDIRECT_URI = os.getenv('HUBSPOT_REDIRECT_URI', 'http://localhost:8000/integrations/hubspot/oauth2callback')

# Define required scopes
SCOPES = [
    'crm.objects.contacts.read',
    'crm.objects.contacts.write'
]

async def authorize_hubspot(user_id: str, org_id: str):
    """Generate OAuth URL and store state"""
    try:
        logger.info(f"Generating HubSpot OAuth URL for user {user_id}")
        
        state_data = {
            'state': secrets.token_urlsafe(32),
            'user_id': user_id,
            'org_id': org_id
        }
        encoded_state = json.dumps(state_data)
        
        # Store state with 10 minute expiry
        await add_key_value_redis(
            f'hubspot_state:{org_id}:{user_id}',
            encoded_state,
            expire=600
        )
        
        # Build authorization URL
        auth_url = (
            'https://app.hubspot.com/oauth/authorize'
            f'?client_id={CLIENT_ID}'
            f'&redirect_uri={REDIRECT_URI}'
            f'&scope={" ".join(SCOPES)}'
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

async def oauth2callback_hubspot(request: Request):
    """Handle OAuth callback and store credentials"""
    try:
        # Check for OAuth errors
        error = request.query_params.get('error')
        if error:
            error_desc = request.query_params.get('error_description', 'Unknown error')
            logger.error(f"OAuth error: {error} - {error_desc}")
            raise HTTPException(status_code=400, detail=error_desc)
        
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
        saved_state = await get_value_redis(f'hubspot_state:{org_id}:{user_id}')
        if not saved_state or original_state != json.loads(saved_state).get('state'):
            logger.error("State mismatch")
            raise HTTPException(status_code=400, detail="State mismatch")
            
        # Exchange code for access token
        async with httpx.AsyncClient() as client:
            logger.info("Exchanging code for access token")
            
            response = await client.post(
                'https://api.hubapi.com/oauth/v1/token',
                data={
                    'grant_type': 'authorization_code',
                    'client_id': CLIENT_ID,
                    'client_secret': CLIENT_SECRET,
                    'redirect_uri': REDIRECT_URI,
                    'code': code
                },
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded'
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
                f'hubspot_credentials:{org_id}:{user_id}',
                json.dumps(credentials),
                expire=None  # No expiry for credentials
            )
            
            logger.info("Successfully stored credentials")
            
            # Cleanup state
            await delete_key_redis(f'hubspot_state:{org_id}:{user_id}')
            
            return HTMLResponse(content="""
                <html>
                    <script>
                        if (window.opener) {
                            window.opener.postMessage({ type: "HUBSPOT_AUTH_SUCCESS" }, "*");
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
                            type: "HUBSPOT_AUTH_ERROR",
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

async def get_hubspot_credentials(user_id: str, org_id: str):
    """Get stored HubSpot credentials"""
    try:
        logger.info(f"Getting HubSpot credentials for user {user_id}")
        credentials = await get_value_redis(f'hubspot_credentials:{org_id}:{user_id}')
        
        if not credentials:
            logger.info("No credentials found")
            return None
            
        creds_data = json.loads(credentials)
        
        # Clear stored credentials after retrieval
        await delete_key_redis(f'hubspot_credentials:{org_id}:{user_id}')
        
        return creds_data
        
    except Exception as e:
        logger.error(f"Error getting credentials: {str(e)}")
        return None

def create_integration_item_metadata_object(contact: dict) -> IntegrationItem:
    """Creates an integration metadata object from a HubSpot contact"""
    properties = contact.get('properties', {})
    return IntegrationItem(
        id=str(contact.get('id')),
        type='contact',
        name=f"{properties.get('firstname', '')} {properties.get('lastname', '')}".strip() or 'Unnamed Contact',
        creation_time=properties.get('createdate'),
        last_modified_time=properties.get('lastmodifieddate'),
        parent_id=None,
        email=properties.get('email'),
        company=properties.get('company')
    )

async def get_items_hubspot(credentials) -> List[IntegrationItem]:
    """Fetch contact data from HubSpot"""
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
            
        logger.info("Fetching HubSpot contacts")
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Use httpx for async request
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://api.hubapi.com/crm/v3/objects/contacts',
                headers=headers
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch contacts: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch HubSpot contacts"
                )
                
            data = response.json()
            contacts = data.get('results', [])
            
            items = [
                create_integration_item_metadata_object(contact)
                for contact in contacts
            ]
            
            logger.info(f"Retrieved {len(items)} HubSpot contacts")
            return items
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting HubSpot items: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get HubSpot items: {str(e)}"
        )
