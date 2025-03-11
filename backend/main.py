from fastapi import FastAPI, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json

from auth_routes import router as auth_router
from integrations.airtable import authorize_airtable, get_items_airtable, oauth2callback_airtable, get_airtable_credentials
from integrations.notion import authorize_notion, get_items_notion, oauth2callback_notion, get_notion_credentials
from integrations.hubspot import authorize_hubspot, get_hubspot_credentials, get_items_hubspot, oauth2callback_hubspot
from integrations.slack import authorize_slack, get_slack_credentials, get_items_slack, oauth2callback_slack
from integrations.google_auth import google_auth_url, google_auth_callback, get_google_user_info

app = FastAPI()

origins = [
    "http://localhost:3000",  # Next.js frontend
    "http://localhost:8000",  # Backend
    "https://accounts.google.com",  # Google OAuth
    "null",  # Allow requests from popup windows
    "http://localhost:8000/auth/google/callback",  # OAuth callback
    "http://localhost:3000/auth/google/callback",  # OAuth callback
]

# Enable credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include auth routes
app.include_router(auth_router, prefix="/auth", tags=["authentication"])

@app.get('/')
def read_root():
    return {'Ping': 'Pong'}

# Airtable
@app.post('/integrations/airtable/authorize')
async def authorize_airtable_integration(user_id: str = Form(...), org_id: str = Form(...)):
    return await authorize_airtable(user_id, org_id)

@app.get('/integrations/airtable/oauth2callback')
async def oauth2callback_airtable_integration(request: Request):
    return await oauth2callback_airtable(request)

@app.post('/integrations/airtable/credentials')
async def get_airtable_credentials_integration(user_id: str = Form(...), org_id: str = Form(...)):
    return await get_airtable_credentials(user_id, org_id)

@app.post('/integrations/airtable/load')
async def get_airtable_items(credentials: str = Form(...)):
    items = await get_items_airtable(credentials)
    return [item.__dict__ for item in items]

# Notion
@app.post('/integrations/notion/authorize')
async def authorize_notion_integration(user_id: str = Form(...), org_id: str = Form(...)):
    return await authorize_notion(user_id, org_id)

@app.get('/integrations/notion/oauth2callback')
async def oauth2callback_notion_integration(request: Request):
    return await oauth2callback_notion(request)

@app.post('/integrations/notion/credentials')
async def get_notion_credentials_integration(user_id: str = Form(...), org_id: str = Form(...)):
    return await get_notion_credentials(user_id, org_id)

@app.post('/integrations/notion/load')
async def get_notion_items(credentials: str = Form(...)):
    items = await get_items_notion(credentials)
    return [item.__dict__ for item in items]

# HubSpot
@app.post('/integrations/hubspot/authorize')
async def authorize_hubspot_integration(user_id: str = Form(...), org_id: str = Form(...)):
    return await authorize_hubspot(user_id, org_id)

@app.get('/integrations/hubspot/oauth2callback')
async def oauth2callback_hubspot_integration(request: Request):
    return await oauth2callback_hubspot(request)

@app.post('/integrations/hubspot/credentials')
async def get_hubspot_credentials_integration(user_id: str = Form(...), org_id: str = Form(...)):
    return await get_hubspot_credentials(user_id, org_id)

@app.post('/integrations/hubspot/load')
async def get_hubspot_items_integration(credentials: str = Form(...)):
    items = await get_items_hubspot(credentials)
    return [item.__dict__ for item in items]

# Slack
@app.post('/integrations/slack/authorize')
async def authorize_slack_integration(user_id: str = Form(...), org_id: str = Form(...)):
    return await authorize_slack(user_id, org_id)

@app.get('/integrations/slack/oauth2callback')
async def oauth2callback_slack_integration(request: Request):
    return await oauth2callback_slack(request)

@app.post('/integrations/slack/credentials')
async def get_slack_credentials_integration(user_id: str = Form(...), org_id: str = Form(...)):
    return await get_slack_credentials(user_id, org_id)

@app.post('/integrations/slack/load')
async def get_slack_items_integration(credentials: str = Form(...)):
    items = await get_items_slack(credentials)
    return [item.__dict__ for item in items]

# Google Authentication
@app.get('/auth/google/url')
async def get_google_auth_url():
    auth_url = await google_auth_url()
    return {"url": auth_url}

@app.get('/auth/google/callback')
async def google_callback(request: Request):
    return await google_auth_callback(request)

@app.get('/auth/google/user')
async def get_user_info(token: str):
    return await get_google_user_info(token)
