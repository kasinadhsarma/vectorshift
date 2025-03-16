import json
import secrets
import os
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import asyncio
from dotenv import load_dotenv
from integrations.integration_item import IntegrationItem
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

load_dotenv()

CLIENT_ID = os.getenv('HUBSPOT_CLIENT_ID')
CLIENT_SECRET = os.getenv('HUBSPOT_CLIENT_SECRET')
REDIRECT_URI = os.getenv('HUBSPOT_REDIRECT_URI')
AUTHORIZATION_URL = 'https://app.hubspot.com/oauth/authorize'
TOKEN_URL = 'https://api.hubapi.com/oauth/v1/token'

SCOPES = [
    'contacts',
    'crm.objects.contacts.read',
    'crm.objects.companies.read',
    'crm.objects.deals.read'
]

def validate_oauth_config():
    if not all([CLIENT_ID, CLIENT_SECRET, REDIRECT_URI]):
        raise HTTPException(status_code=500, detail="Missing HubSpot OAuth configuration")

async def authorize_hubspot(user_id: str, org_id: str) -> str:
    """Generate OAuth URL and store state"""
    validate_oauth_config()
    state = secrets.token_urlsafe(32)
    state_data = {'state': state, 'user_id': user_id, 'org_id': org_id}
    await add_key_value_redis(f'hubspot_state:{state}', json.dumps(state_data), expire=600)
    
    scope = " ".join(SCOPES)
    auth_url = (
        f'{AUTHORIZATION_URL}'
        f'?client_id={CLIENT_ID}'
        f'&redirect_uri={REDIRECT_URI}'
        f'&scope={scope}'
        f'&state={state}'
    )
    return auth_url

async def oauth2callback_hubspot(request: Request) -> HTMLResponse:
    """Handle OAuth callback and store credentials"""
    error = request.query_params.get('error')
    if error:
        return HTMLResponse(content=f"""
            <html>
                <head><title>HubSpot Connection Failed</title></head>
                <body>
                    <h1>Connection Failed</h1>
                    <p>Error: {error}</p>
                    <script>
                        window.opener.postMessage(
                            {{ type: 'hubspot-oauth-callback', success: false, error: "{error}" }}, 
                            '*'
                        );
                        setTimeout(() => window.close(), 1000);
                    </script>
                </body>
            </html>
        """)
    
    state = request.query_params.get('state')
    code = request.query_params.get('code')
    
    if not state or not code:
        raise HTTPException(status_code=400, detail='Missing required parameters')
    
    saved_state = await get_value_redis(f'hubspot_state:{state}')
    if not saved_state:
        raise HTTPException(status_code=400, detail='Invalid or expired state')
    
    state_data = json.loads(saved_state)
    user_id = state_data.get('user_id')
    org_id = state_data.get('org_id')
    
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            TOKEN_URL,
            data={
                'grant_type': 'authorization_code',
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'redirect_uri': REDIRECT_URI,
                'code': code
            }
        )
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=token_response.status_code, detail='Failed to get access token')
        
        credentials = token_response.json()
        await add_key_value_redis(f'hubspot_credentials:{org_id}:{user_id}', json.dumps(credentials), expire=3600)
        await delete_key_redis(f'hubspot_state:{state}')
    
    return HTMLResponse(content="""
        <html>
            <head><title>HubSpot Connection Successful</title></head>
            <body>
                <h1>Connection Successful!</h1>
                <p>You have successfully connected your HubSpot account.</p>
                <script>
                    window.opener.postMessage(
                        { type: 'hubspot-oauth-callback', success: true },
                        '*'
                    );
                    setTimeout(() => window.close(), 1000);
                </script>
            </body>
        </html>
    """)

async def get_hubspot_credentials(user_id: str, org_id: str) -> dict:
    """Retrieve stored HubSpot credentials"""
    credentials = await get_value_redis(f'hubspot_credentials:{org_id}:{user_id}')
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found')
    return json.loads(credentials)

async def get_items_hubspot(credentials: dict) -> list[IntegrationItem]:
    """Retrieve HubSpot contacts, companies, and deals"""
    credentials = json.loads(credentials) if isinstance(credentials, str) else credentials
    access_token = credentials.get('access_token')
    if not access_token:
        raise HTTPException(status_code=400, detail='Invalid credentials')

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    async with httpx.AsyncClient() as client:
        # Get contacts and companies in parallel
        responses = await asyncio.gather(
            client.get('https://api.hubapi.com/crm/v3/objects/contacts', headers=headers),
            client.get('https://api.hubapi.com/crm/v3/objects/companies', headers=headers)
        )

        contacts_response, companies_response = responses

        if contacts_response.status_code != 200 or companies_response.status_code != 200:
            raise HTTPException(status_code=500, detail='Failed to fetch HubSpot data')

        contacts_data = contacts_response.json()
        companies_data = companies_response.json()

    items = []

    # Process contacts
    for contact in contacts_data.get('results', []):
        properties = contact.get('properties', {})
        item = IntegrationItem(
            id=contact['id'],
            type='contact',
            name=f"{properties.get('firstname', '')} {properties.get('lastname', '')}".strip() or 'Unnamed Contact',
            email=properties.get('email'),
            company=properties.get('company'),
            last_modified_time=contact.get('updatedAt'),
            source='hubspot'
        )
        items.append(item)

    # Process companies
    for company in companies_data.get('results', []):
        properties = company.get('properties', {})
        item = IntegrationItem(
            id=company['id'],
            type='company',
            name=properties.get('name', 'Unnamed Company'),
            domain=properties.get('domain'),
            industry=properties.get('industry'),
            last_modified_time=company.get('updatedAt'),
            source='hubspot'
        )
        items.append(item)

    return items
