import os
import json
import time
import secrets
import httpx
from typing import Dict, List, Optional
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis
from models.integration import IntegrationItem, IntegrationItemParameter
from urllib.parse import urlencode

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


async def authorize_hubspot(user_id: str, org_id: str = None) -> JSONResponse:
    """
    Generate the authorization URL for HubSpot OAuth flow
    """
    try:
        # Generate a unique state parameter to prevent CSRF
        state = secrets.token_urlsafe(32)
        state_data = {
            'state': state,
            'user_id': user_id,
            'org_id': org_id
        }
        await add_key_value_redis(f'hubspot_state:{state}', json.dumps(state_data), expire=600)
        
        # Define scopes
        scopes = [
            "contacts",
            "oauth",
            "crm.objects.contacts.read",
            "crm.objects.companies.read",
            "crm.objects.deals.read"
        ]
        
        # Build query parameters
        params = {
            'client_id': HUBSPOT_CLIENT_ID,
            'redirect_uri': HUBSPOT_REDIRECT_URI,
            'scope': ' '.join(scopes),
            'state': state
        }
        
        # Construct URL with properly encoded parameters
        auth_url = f"{HUBSPOT_AUTH_URL}?{urlencode(params)}"
        
        print(f"Generated HubSpot auth URL with redirect_uri: {HUBSPOT_REDIRECT_URI}")
        return JSONResponse({"url": auth_url})
    except Exception as e:
        print(f"Error in authorize_hubspot: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate authorization URL: {str(e)}")

async def oauth2callback_hubspot(request: Request) -> Dict:
    """
    Handle the OAuth callback from HubSpot
    """
    error = request.query_params.get('error')
    if error:
        raise HTTPException(status_code=400, detail=error)
        
    state = request.query_params.get('state')
    code = request.query_params.get('code')
    if not state or not code:
        raise HTTPException(status_code=400, detail='Missing required parameters')
    
    # Get and verify state data
    saved_state = await get_value_redis(f'hubspot_state:{state}')
    if not saved_state:
        raise HTTPException(status_code=400, detail='Invalid or expired state')
    
    try:
        state_data = json.loads(saved_state)
        if state != state_data.get('state'):
            raise HTTPException(status_code=400, detail='State mismatch')
            
        user_id = state_data.get('user_id')
        org_id = state_data.get('org_id')
        
        if not user_id:
            raise HTTPException(status_code=400, detail='Missing user ID in state data')
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail='Invalid state data format')
    
    try:
        # Exchange the authorization code for an access token
        async with httpx.AsyncClient() as client:
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
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to exchange code for token: {response.text}"
                )
            
            token_info = response.json()
            
            # Store credentials in Redis
            credentials = {
                "access_token": token_info["access_token"],
                "refresh_token": token_info["refresh_token"],
                "expires_at": int(time.time()) + token_info["expires_in"],
                "token_type": token_info["token_type"]
            }
            
            redis_key = f'hubspot_credentials:{org_id}:{user_id}' if org_id else f'hubspot_credentials:{user_id}'
            await add_key_value_redis(redis_key, json.dumps(credentials), expire=3600)
            
            # Clean up state
            await delete_key_redis(f'hubspot_state:{state}')
            
            return HTMLResponse("<html><script>window.close();</script></html>")
            
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Network error during token exchange: {str(e)}"
        )

async def get_hubspot_credentials(user_id: str, org_id: str = None) -> Optional[Dict]:
    """
    Retrieve stored HubSpot credentials from Redis
    """
    redis_key = f'hubspot_credentials:{org_id}:{user_id}' if org_id else f'hubspot_credentials:{user_id}'
    credentials = await get_value_redis(redis_key)
    
    if not credentials:
        return None
        
    try:
        credentials = json.loads(credentials)
    except json.JSONDecodeError:
        return None
    
    # Check if token is expired
    if credentials["expires_at"] < int(time.time()):
        # Attempt to refresh token
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
                await delete_key_redis(redis_key)
                return None
                
            token_info = response.json()
            credentials = {
                "access_token": token_info["access_token"],
                "refresh_token": token_info["refresh_token"],
                "expires_at": int(time.time()) + token_info["expires_in"],
                "token_type": token_info["token_type"]
            }
            
            await add_key_value_redis(redis_key, json.dumps(credentials), expire=3600)
    
    return credentials

async def get_items_hubspot(user_id: str, org_id: str = None) -> List[IntegrationItem]:
    """
    Retrieve items from HubSpot using the stored credentials
    """
    credentials = await get_hubspot_credentials(user_id, org_id)
    
    if not credentials:
        raise HTTPException(status_code=401, detail="HubSpot credentials not found or expired")
    
    access_token = credentials["access_token"]
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    items = []
    
    try:
        async with httpx.AsyncClient() as client:
            # Fetch contacts
            contacts_response = await client.get(
                f"{HUBSPOT_CONTACTS_URL}?limit=10&properties=firstname,lastname,email,company",
                headers=headers
            )
            
            if contacts_response.status_code == 200:
                contacts_data = contacts_response.json()
                for contact in contacts_data.get("results", []):
                    properties = contact.get("properties", {})
                    
                    item = IntegrationItem(
                        id=contact.get("id", ""),
                        name=f"{properties.get('firstname', '')} {properties.get('lastname', '')}".strip(),
                        type="contact",
                        source="hubspot",
                        parameters=[
                            IntegrationItemParameter(
                                name="id",
                                value=contact.get("id", ""),
                                type="string"
                            ),
                            IntegrationItemParameter(
                                name="name",
                                value=f"{properties.get('firstname', '')} {properties.get('lastname', '')}".strip(),
                                type="string"
                            ),
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
                    )
                    items.append(item)
            
            # Fetch companies
            companies_response = await client.get(
                f"{HUBSPOT_COMPANIES_URL}?limit=10&properties=name,domain,industry,phone",
                headers=headers
            )
            
            if companies_response.status_code == 200:
                companies_data = companies_response.json()
                for company in companies_data.get("results", []):
                    properties = company.get("properties", {})
                    
                    item = IntegrationItem(
                        id=company.get("id", ""),
                        name=properties.get("name", ""),
                        type="company",
                        source="hubspot",
                        parameters=[
                            IntegrationItemParameter(
                                name="id",
                                value=company.get("id", ""),
                                type="string"
                            ),
                            IntegrationItemParameter(
                                name="name",
                                value=properties.get("name", ""),
                                type="string"
                            ),
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
                    )
                    items.append(item)
            
            # Fetch deals
            deals_response = await client.get(
                f"{HUBSPOT_DEALS_URL}?limit=10&properties=dealname,amount,dealstage,closedate",
                headers=headers
            )
            
            if deals_response.status_code == 200:
                deals_data = deals_response.json()
                for deal in deals_data.get("results", []):
                    properties = deal.get("properties", {})
                    
                    item = IntegrationItem(
                        id=deal.get("id", ""),
                        name=properties.get("dealname", ""),
                        type="deal",
                        source="hubspot",
                        parameters=[
                            IntegrationItemParameter(
                                name="id",
                                value=deal.get("id", ""),
                                type="string"
                            ),
                            IntegrationItemParameter(
                                name="name",
                                value=properties.get("dealname", ""),
                                type="string"
                            ),
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
                    )
                    items.append(item)
                    
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching HubSpot data: {str(e)}"
        )
    
    return items
