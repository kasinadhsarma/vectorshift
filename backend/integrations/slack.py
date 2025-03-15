from fastapi import Request, HTTPException, Form
from fastapi.responses import HTMLResponse
import httpx
import json
import os
from dotenv import load_dotenv
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis
import secrets

load_dotenv()

def get_slack_config():
    return (
        os.environ.get('SLACK_CLIENT_ID'),
        os.environ.get('SLACK_CLIENT_SECRET'),
        os.environ.get('SLACK_REDIRECT_URI')
    )

async def authorize_slack(user_id: str, org_id: str) -> str:
    client_id, _, redirect_uri = get_slack_config()
    if not client_id:
        raise HTTPException(status_code=503, detail="Slack integration not configured")
    
    state = {'state': secrets.token_urlsafe(32), 'user_id': user_id, 'org_id': org_id}
    await add_key_value_redis(f'slack_state:{org_id}:{user_id}', json.dumps(state), expire=600)
    
    scopes = "channels:read users:read"
    auth_url = (
        f"https://slack.com/oauth/v2/authorize?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"scope={scopes}&"
        f"state={json.dumps(state)}"
    )
    return auth_url

async def oauth2callback_slack(request: Request):
    code = request.query_params.get('code')
    state = json.loads(request.query_params.get('state'))
    user_id, org_id = state['user_id'], state['org_id']
    
    saved_state = json.loads(await get_value_redis(f'slack_state:{org_id}:{user_id}'))
    if state['state'] != saved_state['state']:
        raise HTTPException(status_code=400, detail="State mismatch")
    
    client_id, client_secret, redirect_uri = get_slack_config()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            'https://slack.com/api/oauth.v2.access',
            data={'client_id': client_id, 'client_secret': client_secret, 'code': code, 'redirect_uri': redirect_uri}
        )
    credentials = response.json()
    await add_key_value_redis(f'slack_credentials:{org_id}:{user_id}', json.dumps(credentials))
    return HTMLResponse("<script>window.close();</script>")

async def get_slack_credentials(user_id: str, org_id: str) -> dict:
    credentials = await get_value_redis(f'slack_credentials:{org_id}:{user_id}')
    if not credentials:
        raise HTTPException(status_code=404, detail="No credentials found")
    return json.loads(credentials)

async def get_items_slack(credentials: dict):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            'https://slack.com/api/users.list',
            headers={'Authorization': f"Bearer {credentials['access_token']}"}
        )
        return response.json().get('members', [])