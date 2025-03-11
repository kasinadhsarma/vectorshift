import os
import json
import secrets
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
from dotenv import load_dotenv
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

load_dotenv()

CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8000/auth/google/callback')
AUTHORIZATION_URL = 'https://accounts.google.com/o/oauth2/auth'
TOKEN_URL = 'https://oauth2.googleapis.com/token'
USER_INFO_URL = 'https://www.googleapis.com/oauth2/v3/userinfo'

async def google_auth_url():
    """Generate Google OAuth URL"""
    state = secrets.token_urlsafe(32)
    
    try:
        # Store state in Redis for verification
        await add_key_value_redis(f'google_state:{state}', state, expire=600)
        
        auth_url = (
            f'{AUTHORIZATION_URL}'
            f'?client_id={CLIENT_ID}'
            f'&redirect_uri={REDIRECT_URI}'
            f'&response_type=code'
            f'&state={state}'
            f'&scope=openid email profile'
            f'&access_type=offline'
            f'&prompt=consent'
        )
        return auth_url
    except Exception as e:
        print(f"Error generating auth URL: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate authentication URL")

async def google_auth_callback(request: Request):
    """Handle Google OAuth callback"""
    state = None
    try:
        # Check for OAuth error
        if request.query_params.get('error'):
            error_desc = request.query_params.get('error_description', 'No error description')
            error_code = request.query_params.get('error', 'Unknown error')
            print(f"OAuth Error: {error_code} - {error_desc}")
            raise HTTPException(
                status_code=400,
                detail=f"OAuth error: {error_desc}"
            )
        
        # Get and validate code and state
        code = request.query_params.get('code')
        state = request.query_params.get('state')
        
        if not code:
            print("Error: No authorization code received")
            raise HTTPException(status_code=400, detail='No authorization code received')
            
        if not state:
            print("Error: No state parameter received")
            raise HTTPException(status_code=400, detail='No state parameter received')
        
        # Verify state
        saved_state = await get_value_redis(f'google_state:{state}')
        if not saved_state or state != saved_state:
            print(f"State mismatch. Received: {state}, Saved: {saved_state}")
            raise HTTPException(status_code=400, detail='Invalid state parameter')
    
        # Exchange code for token
        print(f"Exchanging code for token using client_id: {CLIENT_ID}")
        async with httpx.AsyncClient() as client:
            token_data = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': REDIRECT_URI,
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET
            }
            print(f"Token request data: {token_data}")
            
            response = await client.post(
                TOKEN_URL,
                data=token_data
            )
            
            if response.status_code != 200:
                error_body = response.json() if response.headers.get('content-type') == 'application/json' else response.text
                print(f"Token exchange failed: Status {response.status_code}, Body: {error_body}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f'Failed to obtain access token: {error_body}'
                )
        
            token_data = response.json()
            
            # Get user info
            user_response = await client.get(
                USER_INFO_URL,
                headers={'Authorization': f'Bearer {token_data["access_token"]}'}
            )
            
            if user_response.status_code != 200:
                raise HTTPException(
                    status_code=user_response.status_code,
                    detail='Failed to get user info'
                )
            
            user_info = user_response.json()

            # Return HTML that will close the popup and send the token to the parent window
            close_window_script = f"""
            <html>
                <script>
                    window.opener.postMessage({{
                        token: "{token_data['access_token']}",
                        user: {json.dumps(user_info)}
                    }}, "*");
                    window.close();
                </script>
            </html>
            """
            return HTMLResponse(content=close_window_script)

    except Exception as e:
        print(f"Error during OAuth callback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {str(e)}")
    finally:
        if state:
            try:
                await delete_key_redis(f'google_state:{state}')
            except Exception as e:
                print(f"Error cleaning up state: {str(e)}")

async def get_google_user_info(token):
    """Get Google user info from token"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                USER_INFO_URL,
                headers={'Authorization': f'Bearer {token}'}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail='Failed to get user info'
                )
            
            return response.json()
    except Exception as e:
        print(f"Error getting user info: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user information")
