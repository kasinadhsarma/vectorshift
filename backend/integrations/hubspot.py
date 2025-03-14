"""HubSpot integration module."""
import os
import json
import time
import secrets
import logging
from typing import Dict, List, Optional
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
import httpx
from urllib.parse import urlencode
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis
from models.integration import IntegrationItem, IntegrationItemParameter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# HubSpot API endpoints
HUBSPOT_AUTH_URL = "https://app.hubspot.com/oauth/authorize"
HUBSPOT_TOKEN_URL = "https://api.hubapi.com/oauth/v1/token"
HUBSPOT_CONTACTS_URL = "https://api.hubapi.com/crm/v3/objects/contacts"
HUBSPOT_COMPANIES_URL = "https://api.hubapi.com/crm/v3/objects/companies"
HUBSPOT_DEALS_URL = "https://api.hubapi.com/crm/v3/objects/deals"

# Get credentials from environment variables
HUBSPOT_CLIENT_ID = os.getenv("HUBSPOT_CLIENT_ID", "4ae1421f-b957-4ea5-beaa-45e9378c2854")
HUBSPOT_CLIENT_SECRET = os.getenv("HUBSPOT_CLIENT_SECRET", "f77688ab-9292-45ac-8ce4-749b21fec157")
HUBSPOT_REDIRECT_URI = os.getenv("HUBSPOT_REDIRECT_URI", "http://localhost:8000/api/integrations/hubspot/oauth2callback")

# Define required scopes
SCOPES = [
    "contacts",
    "oauth",
    "crm.objects.contacts.read",
    "crm.objects.companies.read",
    "crm.objects.deals.read"
]

async def authorize_hubspot(user_id: str, org_id: str = None) -> JSONResponse:
    """Generate OAuth URL for HubSpot authorization."""
    try:
        logger.info(f"Generating HubSpot OAuth URL for user {user_id}")
        
        # Generate state and store data
        state = secrets.token_urlsafe(32)
        state_data = {
            'state': state,
            'user_id': user_id,
            'org_id': org_id
        }
        
        # Store state with expiry
        await add_key_value_redis(
            f'hubspot_state:{state}',
            json.dumps(state_data),
            expire=600
        )
        
        # Build authorization URL
        params = {
            'client_id': HUBSPOT_CLIENT_ID,
            'redirect_uri': HUBSPOT_REDIRECT_URI,
            'scope': ' '.join(SCOPES),
            'state': state
        }
        auth_url = f"{HUBSPOT_AUTH_URL}?{urlencode(params)}"
        
        logger.info("Successfully generated authorization URL")
        return JSONResponse({"url": auth_url})
        
    except Exception as e:
        logger.error(f"Error generating authorization URL: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate authorization URL: {str(e)}"
        )

async def oauth2callback_hubspot(request: Request) -> HTMLResponse:
    """Handle OAuth callback from HubSpot."""
    try:
        # Check for OAuth errors
        error = request.query_params.get('error')
        if error:
            error_desc = request.query_params.get('error_description', 'Unknown error')
            logger.error(f"OAuth error: {error} - {error_desc}")
            raise HTTPException(status_code=400, detail=error_desc)
        
        # Get and validate parameters
        code = request.query_params.get('code')
        state = request.query_params.get('state')
        
        if not code or not state:
            logger.error("Missing required parameters")
            raise HTTPException(status_code=400, detail="Missing required parameters")
        
        # Get and verify state data
        saved_state = await get_value_redis(f'hubspot_state:{state}')
        if not saved_state:
            logger.error("State expired or invalid")
            raise HTTPException(status_code=400, detail="State expired or invalid")
        
        try:
            state_data = json.loads(saved_state)
            if state != state_data.get('state'):
                raise HTTPException(status_code=400, detail="State mismatch")
                
            user_id = state_data.get('user_id')
            org_id = state_data.get('org_id')
            
            if not user_id:
                raise HTTPException(status_code=400, detail="Missing user ID in state data")
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid state data format")
        
        # Exchange code for tokens
        async with httpx.AsyncClient() as client:
            logger.info("Exchanging code for access token")
            
            response = await client.post(
                HUBSPOT_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": HUBSPOT_CLIENT_ID,
                    "client_secret": HUBSPOT_CLIENT_SECRET,
                    "redirect_uri": HUBSPOT_REDIRECT_URI,
                    "code": code
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Token exchange failed: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to exchange code for token: {response.text}"
                )
            
            # Process token response
            token_info = response.json()
            credentials = {
                "access_token": token_info["access_token"],
                "refresh_token": token_info["refresh_token"],
                "expires_at": int(time.time()) + token_info["expires_in"],
                "token_type": token_info["token_type"]
            }
            
            # Store credentials
            redis_key = f'hubspot_credentials:{org_id}:{user_id}' if org_id else f'hubspot_credentials:{user_id}'
            await add_key_value_redis(redis_key, json.dumps(credentials), expire=3600)
            
            logger.info("Successfully stored credentials")
            
            # Cleanup state
            await delete_key_redis(f'hubspot_state:{state}')
            
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

async def get_hubspot_credentials(user_id: str, org_id: str = None) -> Optional[Dict]:
    """Get and refresh HubSpot credentials if needed."""
    try:
        logger.info(f"Getting HubSpot credentials for user {user_id}")
        
        # Get stored credentials
        redis_key = f'hubspot_credentials:{org_id}:{user_id}' if org_id else f'hubspot_credentials:{user_id}'
        credentials = await get_value_redis(redis_key)
        
        if not credentials:
            logger.info("No credentials found")
            return None
            
        try:
            credentials = json.loads(credentials)
        except json.JSONDecodeError:
            logger.error("Invalid credentials format")
            return None
        
        # Check if token needs refresh
        if credentials["expires_at"] < int(time.time()):
            logger.info("Token expired, attempting refresh")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    HUBSPOT_TOKEN_URL,
                    data={
                        "grant_type": "refresh_token",
                        "client_id": HUBSPOT_CLIENT_ID,
                        "client_secret": HUBSPOT_CLIENT_SECRET,
                        "refresh_token": credentials["refresh_token"]
                    }
                )
                
                if response.status_code != 200:
                    logger.error("Token refresh failed")
                    await delete_key_redis(redis_key)
                    return None
                    
                # Update stored credentials
                token_info = response.json()
                credentials = {
                    "access_token": token_info["access_token"],
                    "refresh_token": token_info["refresh_token"],
                    "expires_at": int(time.time()) + token_info["expires_in"],
                    "token_type": token_info["token_type"]
                }
                
                await add_key_value_redis(redis_key, json.dumps(credentials), expire=3600)
                logger.info("Successfully refreshed token")
        
        return credentials
        
    except Exception as e:
        logger.error(f"Error getting credentials: {str(e)}")
        return None

async def get_items_hubspot(credentials: Dict) -> List[IntegrationItem]:
    """Fetch contacts, companies, and deals from HubSpot."""
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
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        items = []
        async with httpx.AsyncClient() as client:
            # Fetch contacts
            logger.info("Fetching HubSpot contacts")
            contacts_response = await client.get(
                f"{HUBSPOT_CONTACTS_URL}?limit=10&properties=firstname,lastname,email,company",
                headers=headers
            )
            
            if contacts_response.status_code == 200:
                contacts_data = contacts_response.json()
                for contact in contacts_data.get("results", []):
                    properties = contact.get("properties", {})
                    items.append(IntegrationItem(
                        id=contact.get("id", ""),
                        name=f"{properties.get('firstname', '')} {properties.get('lastname', '')}".strip(),
                        type="contact",
                        source="hubspot",
                        parameters=[
                            IntegrationItemParameter(
                                name="email",
                                value=properties.get("email", ""),
                                type="string"
                            ),
                            IntegrationItemParameter(
                                name="company",
                                value=properties.get("company", ""),
                                type="string"
                            )
                        ]
                    ))
            
            # Fetch companies
            logger.info("Fetching HubSpot companies")
            companies_response = await client.get(
                f"{HUBSPOT_COMPANIES_URL}?limit=10&properties=name,domain,industry,phone",
                headers=headers
            )
            
            if companies_response.status_code == 200:
                companies_data = companies_response.json()
                for company in companies_data.get("results", []):
                    properties = company.get("properties", {})
                    items.append(IntegrationItem(
                        id=company.get("id", ""),
                        name=properties.get("name", ""),
                        type="company",
                        source="hubspot",
                        parameters=[
                            IntegrationItemParameter(
                                name="domain",
                                value=properties.get("domain", ""),
                                type="string"
                            ),
                            IntegrationItemParameter(
                                name="industry",
                                value=properties.get("industry", ""),
                                type="string"
                            ),
                            IntegrationItemParameter(
                                name="phone",
                                value=properties.get("phone", ""),
                                type="string"
                            )
                        ]
                    ))
            
            # Fetch deals
            logger.info("Fetching HubSpot deals")
            deals_response = await client.get(
                f"{HUBSPOT_DEALS_URL}?limit=10&properties=dealname,amount,dealstage,closedate",
                headers=headers
            )
            
            if deals_response.status_code == 200:
                deals_data = deals_response.json()
                for deal in deals_data.get("results", []):
                    properties = deal.get("properties", {})
                    items.append(IntegrationItem(
                        id=deal.get("id", ""),
                        name=properties.get("dealname", ""),
                        type="deal",
                        source="hubspot",
                        parameters=[
                            IntegrationItemParameter(
                                name="amount",
                                value=properties.get("amount", ""),
                                type="string"
                            ),
                            IntegrationItemParameter(
                                name="stage",
                                value=properties.get("dealstage", ""),
                                type="string"
                            ),
                            IntegrationItemParameter(
                                name="closedate",
                                value=properties.get("closedate", ""),
                                type="string"
                            )
                        ]
                    ))
            
            logger.info(f"Retrieved {len(items)} HubSpot items")
            return items
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching HubSpot data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch HubSpot data: {str(e)}")
