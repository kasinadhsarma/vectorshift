# airtable.py

import json
import secrets
import hashlib
import logging
from typing import List, Dict, Optional, Any
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import asyncio
import base64
import requests
from integrations.integration_item import IntegrationItem
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OAuth Configuration
CLIENT_ID = '4ee0b67c-f213-41cb-8fd8-23e9e8471af0'
CLIENT_SECRET = 'b1104130021f6fa0fb4da71ba4e3446c5d790eb5ad37f73881ab7906aaac6f30'
REDIRECT_URI = 'http://localhost:8000/integrations/airtable/oauth2callback'
AUTHORIZATION_URL = 'https://airtable.com/oauth2/v1/authorize'
TOKEN_URL = 'https://airtable.com/oauth2/v1/token'
API_URL = 'https://api.airtable.com/v0/meta'

# Pre-encode client credentials
encoded_client_id_secret = base64.b64encode(f'{CLIENT_ID}:{CLIENT_SECRET}'.encode()).decode()

# Define required scopes
SCOPES = [
    'data.records:read',
    'data.records:write',
    'schema.bases:read',
    'schema.bases:write'
]

async def authorize_airtable(user_id: str, org_id: str):
    """Generate OAuth URL with PKCE flow and store state"""
    try:
        logger.info(f"Generating Airtable OAuth URL for user {user_id}")
        
        # Generate state and PKCE verifier
        state_data = {
            'state': secrets.token_urlsafe(32),
            'user_id': user_id,
            'org_id': org_id
        }
        encoded_state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()
        
        # Generate PKCE challenge
        code_verifier = secrets.token_urlsafe(32)
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).rstrip(b'=').decode()
        
        # Store state and verifier
        await asyncio.gather(
            add_key_value_redis(
                f'airtable_state:{org_id}:{user_id}',
                json.dumps(state_data),
                expire=600
            ),
            add_key_value_redis(
                f'airtable_verifier:{org_id}:{user_id}',
                code_verifier,
                expire=600
            )
        )
        
        # Build authorization URL
        auth_url = (
            f'{AUTHORIZATION_URL}'
            f'?client_id={CLIENT_ID}'
            f'&redirect_uri={REDIRECT_URI}'
            f'&response_type=code'
            f'&state={encoded_state}'
            f'&code_challenge={code_challenge}'
            f'&code_challenge_method=S256'
            f'&scope={" ".join(SCOPES)}'
        )
        
        logger.info("Successfully generated authorization URL")
        return {"url": auth_url}
        
    except Exception as e:
        logger.error(f"Error generating authorization URL: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate authorization URL: {str(e)}"
        )

async def oauth2callback_airtable(request: Request):
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
            
        # Decode and validate state
        try:
            state_data = json.loads(base64.urlsafe_b64decode(encoded_state).decode())
            original_state = state_data.get('state')
            user_id = state_data.get('user_id')
            org_id = state_data.get('org_id')
            
            if not all([original_state, user_id, org_id]):
                raise ValueError("Invalid state format")
                
        except Exception as e:
            logger.error(f"Invalid state format: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid state format: {str(e)}")
            
        # Verify stored state and get code verifier
        saved_state, code_verifier = await asyncio.gather(
            get_value_redis(f'airtable_state:{org_id}:{user_id}'),
            get_value_redis(f'airtable_verifier:{org_id}:{user_id}'),
        )
        
        if not saved_state:
            logger.error("State expired or invalid")
            raise HTTPException(status_code=400, detail="State expired or invalid")
            
        saved_state_data = json.loads(saved_state)
        if original_state != saved_state_data.get('state'):
            logger.error("State mismatch")
            raise HTTPException(status_code=400, detail="State mismatch")
            
        # Exchange code for access token
        async with httpx.AsyncClient() as client:
            logger.info("Exchanging code for access token")
            
            response = await client.post(
                TOKEN_URL,
                data={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': REDIRECT_URI,
                    'client_id': CLIENT_ID,
                    'code_verifier': code_verifier.decode(),
                },
                headers={
                    'Authorization': f'Basic {encoded_client_id_secret}',
                    'Content-Type': 'application/x-www-form-urlencoded',
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
                f'airtable_credentials:{org_id}:{user_id}',
                json.dumps(credentials)
            )
            
            logger.info("Successfully stored credentials")
            
            # Cleanup state and verifier
            await asyncio.gather(
                delete_key_redis(f'airtable_state:{org_id}:{user_id}'),
                delete_key_redis(f'airtable_verifier:{org_id}:{user_id}')
            )
            
            return HTMLResponse(content="""
                <html>
                    <script>
                        if (window.opener) {
                            window.opener.postMessage({ type: "AIRTABLE_AUTH_SUCCESS" }, "*");
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
                            type: "AIRTABLE_AUTH_ERROR",
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

async def get_airtable_credentials(user_id: str, org_id: str) -> Optional[Dict[str, Any]]:
    """Get stored Airtable credentials"""
    try:
        logger.info(f"Getting Airtable credentials for user {user_id}")
        credentials = await get_value_redis(f'airtable_credentials:{org_id}:{user_id}')
        
        if not credentials:
            logger.info("No credentials found")
            return None
            
        return json.loads(credentials)
        
    except Exception as e:
        logger.error(f"Error getting credentials: {str(e)}")
        return None

def create_integration_item_metadata_object(
    response_json: Dict,
    item_type: str,
    parent_id: Optional[str] = None,
    parent_name: Optional[str] = None
) -> IntegrationItem:
    """Creates an integration metadata object from the response"""
    parent_id = f"{parent_id}_Base" if parent_id else None
    
    return IntegrationItem(
        id=f"{response_json.get('id', '')}_" + item_type,
        name=response_json.get('name', 'Untitled'),
        type=item_type,
        parent_id=parent_id,
        parent_path_or_name=parent_name,
        creation_time=response_json.get('createdTime'),
        last_modified_time=response_json.get('modifiedTime')
    )

async def get_items_airtable(credentials: Dict[str, Any]) -> List[IntegrationItem]:
    """Aggregates all metadata relevant for an Airtable integration"""
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
            
        headers = {'Authorization': f'Bearer {access_token}'}
        items: List[IntegrationItem] = []
        
        # Fetch bases
        async with httpx.AsyncClient() as client:
            response = await client.get(f'{API_URL}/bases', headers=headers)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch Airtable bases"
                )
                
            bases_data = response.json()
            
            # Process bases and their tables
            for base in bases_data.get('bases', []):
                # Add base
                items.append(create_integration_item_metadata_object(base, 'Base'))
                
                # Fetch and add tables for this base
                tables_response = await client.get(
                    f'{API_URL}/bases/{base["id"]}/tables',
                    headers=headers
                )
                
                if tables_response.status_code == 200:
                    tables_data = tables_response.json()
                    for table in tables_data.get('tables', []):
                        items.append(
                            create_integration_item_metadata_object(
                                table,
                                'Table',
                                base.get('id'),
                                base.get('name')
                            )
                        )
                        
            logger.info(f"Retrieved {len(items)} Airtable items")
            return items
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Airtable items: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Airtable items: {str(e)}"
        )
