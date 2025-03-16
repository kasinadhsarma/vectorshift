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

CLIENT_ID = os.getenv('NOTION_CLIENT_ID')
CLIENT_SECRET = os.getenv('NOTION_CLIENT_SECRET')
REDIRECT_URI = os.getenv('NOTION_REDIRECT_URI')
AUTHORIZATION_URL = 'https://api.notion.com/v1/oauth/authorize'
TOKEN_URL = 'https://api.notion.com/v1/oauth/token'
NOTION_VERSION = '2022-06-28'

def validate_oauth_config():
    if not all([CLIENT_ID, CLIENT_SECRET, REDIRECT_URI]):
        raise HTTPException(status_code=500, detail="Missing Notion OAuth configuration")

async def authorize_notion(user_id: str, org_id: str):
    """Generate OAuth URL and store state"""
    validate_oauth_config()
    state = secrets.token_urlsafe(32)
    state_data = {'state': state, 'user_id': user_id, 'org_id': org_id}
    await add_key_value_redis(f'notion_state:{state}', json.dumps(state_data), expire=600)
    
    auth_url = f'{AUTHORIZATION_URL}?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&state={state}&owner=user'
    return {"url": auth_url}

async def oauth2callback_notion(request: Request):
    """Handle OAuth callback and store credentials"""
    error = request.query_params.get('error')
    if error:
        return HTMLResponse(content=f"""
            <html>
                <head><title>Notion Connection Failed</title></head>
                <body>
                    <h1>Connection Failed</h1>
                    <p>Error: {error}</p>
                    <script>
                        window.opener.postMessage(
                            {{ type: 'notion-oauth-callback', success: false, error: "{error}" }}, 
                            '*'
                        );
                        setTimeout(() => window.close(), 1000);
                    </script>
                </body>
            </html>
        """)
    
    state, code = request.query_params.get('state'), request.query_params.get('code')
    if not state or not code:
        raise HTTPException(status_code=400, detail='Missing required parameters')
    
    saved_state = await get_value_redis(f'notion_state:{state}')
    if not saved_state:
        raise HTTPException(status_code=400, detail='Invalid or expired state')
    
    state_data = json.loads(saved_state)
    user_id, org_id = state_data.get('user_id'), state_data.get('org_id')
    
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            TOKEN_URL,
            auth=(CLIENT_ID, CLIENT_SECRET),
            json={'grant_type': 'authorization_code', 'code': code, 'redirect_uri': REDIRECT_URI},
        )
        
        if token_response.status_code != 200:
            error_message = 'Failed to get access token'
            return HTMLResponse(content=f"""
                <html>
                    <head><title>Notion Connection Failed</title></head>
                    <body>
                        <h1>Connection Failed</h1>
                        <p>Error: {error_message}</p>
                        <script>
                            window.opener.postMessage(
                                {{ type: 'notion-oauth-callback', success: false, error: "{error_message}" }}, 
                                '*'
                            );
                            setTimeout(() => window.close(), 1000);
                        </script>
                    </body>
                </html>
            """)
        
        credentials = token_response.json()
        await add_key_value_redis(f'notion_credentials:{org_id}:{user_id}', json.dumps(credentials), expire=3600)
        await delete_key_redis(f'notion_state:{state}')
    
    return HTMLResponse(content="""
        <html>
            <head><title>Notion Connection Successful</title></head>
            <body>
                <h1>Connection Successful!</h1>
                <p>You have successfully connected your Notion account.</p>
                <script>
                    try {
                        if (window.opener) {
                            window.opener.postMessage(
                                { 
                                    type: 'notion-oauth-callback', 
                                    success: true,
                                    redirect: "/dashboard/integrations/notion"
                                }, 
                                window.location.origin
                            );
                            setTimeout(() => window.close(), 500);
                        } else {
                            window.location.href = "/dashboard/integrations/notion";
                        }
                    } catch (e) {
                        console.error('Error in popup:', e);
                        document.body.innerHTML = '<h1>Error</h1><p>An error occurred during authentication.</p><pre>' + e.toString() + '</pre>';
                    }
                </script>
            </body>
        </html>
    """)

async def get_notion_credentials(user_id: str, org_id: str):
    """Retrieve stored Notion credentials"""
    credentials = await get_value_redis(f'notion_credentials:{org_id}:{user_id}')
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found')
    return json.loads(credentials)

async def get_items_notion(credentials: dict) -> list[IntegrationItem]:
    """Retrieve Notion databases and pages"""
    credentials = json.loads(credentials) if isinstance(credentials, str) else credentials
    access_token = credentials.get('access_token')
    if not access_token:
        raise HTTPException(status_code=400, detail='Invalid credentials')
    
    headers = {'Authorization': f'Bearer {access_token}', 'Notion-Version': NOTION_VERSION}
    async with httpx.AsyncClient() as client:
        responses = await asyncio.gather(
            client.get('https://api.notion.com/v1/users/me', headers=headers),
            client.post('https://api.notion.com/v1/search', headers=headers, json={'filter': {'property': 'object', 'value': 'database'}}),
            client.post('https://api.notion.com/v1/search', headers=headers, json={'filter': {'property': 'object', 'value': 'page'}}),
        )
    
    if any(response.status_code != 200 for response in responses):
        raise HTTPException(status_code=500, detail='Failed to fetch Notion data')
    
    user_response, db_response, page_response = responses
    items = []

    # Process databases
    for db in db_response.json().get('results', []):
        items.append(IntegrationItem(
            id=db['id'],
            type='database',
            name=db.get('title', [{}])[0].get('text', {}).get('content', 'Untitled'),
            items=len(db.get('properties', {})),
            last_modified_time=db.get('last_edited_time'),
            source='notion'
        ))
    
    # Process pages
    for page in page_response.json().get('results', []):
        try:
            # Handle different page title structures
            properties = page.get('properties', {})
            title_prop = None
            
            # Try to find title in properties
            for prop in properties.values():
                if prop.get('type') == 'title':
                    title_prop = prop
                    break
            
            # Extract title from property
            if title_prop and title_prop.get('title'):
                title_parts = []
                for text_obj in title_prop['title']:
                    if text_obj.get('type') == 'text':
                        title_parts.append(text_obj.get('text', {}).get('content', ''))
                title = ' '.join(title_parts) if title_parts else 'Untitled'
            else:
                # Fallback to page title if properties don't contain it
                title = page.get('title', [{}])[0].get('text', {}).get('content', 'Untitled')
            
            items.append(IntegrationItem(
                id=page['id'],
                type='page',
                title=title,
                name=title,  # Add name field for compatibility
                last_modified_time=page.get('last_edited_time'),
                source='notion'
            ))
        except Exception as e:
            print(f"Error processing Notion page {page.get('id')}: {str(e)}")
            # Continue processing other pages even if one fails
            continue
    
    return items
