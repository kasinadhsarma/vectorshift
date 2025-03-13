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

CLIENT_ID = os.getenv('AIRTABLE_CLIENT_ID')
CLIENT_SECRET = os.getenv('AIRTABLE_CLIENT_SECRET')
REDIRECT_URI = os.getenv('AIRTABLE_REDIRECT_URI')
AUTHORIZATION_URL = 'https://airtable.com/oauth2/v1/authorize'
TOKEN_URL = 'https://airtable.com/oauth2/v1/token'
API_URL = 'https://api.airtable.com/v0/meta'

async def authorize_airtable(user_id, org_id):
    state = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(32)
    
    # Generate code challenge using the verifier
    import base64
    import hashlib
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    
    state_data = {
        'state': state,
        'user_id': user_id,
        'org_id': org_id,
        'code_verifier': code_verifier
    }
    encoded_state = json.dumps(state_data)
    await add_key_value_redis(f'airtable_state:{org_id}:{user_id}', encoded_state, expire=600)
    
    scopes = [
        'data.records:read',
        'data.records:write',
        'schema.bases:read',
        'schema.bases:write'
    ]
    
    auth_url = (
        f'{AUTHORIZATION_URL}'
        f'?client_id={CLIENT_ID}'
        f'&redirect_uri={REDIRECT_URI}'
        f'&response_type=code'
        f'&state={state}'
        f'&scope={" ".join(scopes)}'
        f'&code_challenge={code_challenge}'
        f'&code_challenge_method=S256'
    )
    return {"url": auth_url}

async def oauth2callback_airtable(request: Request):
    if request.query_params.get('error'):
        raise HTTPException(
            status_code=400,
            detail=request.query_params.get('error_description', 'OAuth error')
        )
    
    code = request.query_params.get('code')
    state = request.query_params.get('state')
    
    # First get the saved state by state parameter
    saved_state = await get_value_redis(f'airtable_state:{state}')
    if not saved_state:
        raise HTTPException(status_code=400, detail='State not found')
        
    try:
        state_data = json.loads(saved_state)
        user_id = state_data.get('user_id')
        org_id = state_data.get('org_id')
        code_verifier = state_data.get('code_verifier')
        
        if not all([user_id, org_id, code_verifier]):
            raise HTTPException(status_code=400, detail='Missing required state data')
            
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail='Invalid state data format')

    saved_state = await get_value_redis(f'airtable_state:{org_id}:{user_id}')
    if not saved_state or state != json.loads(saved_state).get('state'):
        raise HTTPException(status_code=400, detail='State mismatch')

    async with httpx.AsyncClient() as client:
        response, _ = await asyncio.gather(
            client.post(
                TOKEN_URL,
                data={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': REDIRECT_URI,
                    'client_id': CLIENT_ID,
                    'client_secret': CLIENT_SECRET,
                    'code_verifier': code_verifier
                }
            ),
            delete_key_redis(f'airtable_state:{org_id}:{user_id}')
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail='Failed to obtain access token'
            )

        token_data = response.json()
        await add_key_value_redis(
            f'airtable_credentials:{org_id}:{user_id}',
            json.dumps(token_data),
            expire=token_data.get('expires_in', 7200)
        )
    
    return HTMLResponse(content="<html><script>window.close();</script></html>")

async def get_airtable_credentials(user_id: str, org_id: str) -> dict:
    """Get Airtable credentials using the standardized credentials function."""
    from redis_client import get_credentials
    return await get_credentials('airtable', user_id, org_id)

async def get_items_airtable(credentials) -> dict:
    """Get enhanced data from Airtable including bases, tables, and workspace info"""
    # Ensure credentials is a dict
    if isinstance(credentials, str):
        try:
            credentials = json.loads(credentials)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail='Invalid credentials format')
    
    access_token = credentials.get('access_token')
    if not access_token:
        raise HTTPException(status_code=400, detail='Missing access token')

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Make parallel requests for bases and workspace info
            responses = await asyncio.gather(
                client.get(f'{API_URL}/bases', headers=headers),
                client.get(f'{API_URL}/workspaces', headers=headers)
            )
            
            bases_response, workspaces_response = responses
            
            # Check responses for errors
            for resp in responses:
                if resp.status_code != 200:
                    error_msg = f'Airtable API error: {resp.text}'
                    raise HTTPException(status_code=resp.status_code, detail=error_msg)
                
                try:
                    resp.json()
                except json.JSONDecodeError:
                    raise HTTPException(status_code=500, detail='Invalid JSON response from Airtable')
            
            # Process workspace data
            workspace_data = workspaces_response.json()
            workspaces = [
                {
                    'id': workspace.get('id'),
                    'name': workspace.get('name'),
                    'type': workspace.get('type', 'workspace'),
                    'url': f"https://airtable.com/{workspace.get('id')}",
                } for workspace in workspace_data.get('workspaces', [])
            ]
            
            # Process bases with enhanced metadata
            bases = []
            tables = []
            bases_data = bases_response.json()
            
            for base in bases_data.get('bases', []):
                # Add base with enhanced metadata
                bases.append({
                    'id': base.get('id'),
                    'name': base.get('name', 'Untitled Base'),
                    'type': 'base',
                    'url': f"https://airtable.com/{base.get('id')}",
                    'created_time': base.get('createdTime'),
                    'modified_time': base.get('modifiedTime'),
                    'permission_level': base.get('permissionLevel'),
                    'workspace_id': base.get('workspaceId'),
                    'schema_version': base.get('revision')
                })
                
                # Process tables with enhanced metadata
                for table in base.get('tables', []):
                    tables.append({
                        'id': table.get('id'),
                        'name': table.get('name', 'Untitled Table'),
                        'type': 'table',
                        'url': f"https://airtable.com/{base.get('id')}/{table.get('id')}",
                        'created_time': table.get('createdTime'),
                        'modified_time': table.get('modifiedTime'),
                        'primary_field_id': table.get('primaryFieldId'),
                        'fields_count': len(table.get('fields', [])),
                        'description': table.get('description', ''),
                        'base_id': base.get('id'),
                        'workspace_id': base.get('workspaceId')
                    })
            
            return {
                'isConnected': True,
                'status': 'active',
                'workspaces': workspaces,
                'bases': bases,
                'tables': tables,
                'credentials': credentials
            }
            
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500,
                detail=f'Failed to connect to Airtable API: {str(e)}'
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f'Error fetching Airtable data: {str(e)}'
            )
