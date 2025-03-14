"""Integration routes module."""
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict

from integrations.notion import (
    authorize_notion, oauth2callback_notion, get_notion_credentials, get_items_notion
)
from integrations.airtable import (
    authorize_airtable, oauth2callback_airtable, get_airtable_credentials, get_items_airtable
)
from integrations.hubspot import (
    authorize_hubspot, oauth2callback_hubspot, get_hubspot_credentials, get_items_hubspot
)
from integrations.slack import (
    authorize_slack, oauth2callback_slack, get_slack_credentials, get_items_slack
)

router = APIRouter(prefix="/api/integrations", tags=["integrations"])

async def get_status_response(creds_result: Dict) -> Dict:
    """Format status response consistently."""
    if not creds_result:
        return {
            "isConnected": False,
            "status": "inactive",
            "credentials": None
        }
    
    return {
        "isConnected": creds_result.get('isConnected', False),
        "status": creds_result.get('status', 'inactive'),
        "credentials": creds_result.get('credentials')
    }

# Notion routes
@router.post("/notion/authorize")
async def notion_authorize(request: Request):
    data = await request.json()
    return await authorize_notion(data.get('userId'), data.get('orgId'))

@router.get("/notion/oauth2callback")
async def notion_callback(request: Request):
    return await oauth2callback_notion(request)

@router.get("/notion/status")
async def notion_status(userId: str, orgId: str = None):
    try:
        creds = await get_notion_credentials(userId, orgId)
        return await get_status_response(creds)
    except Exception as e:
        return {
            "isConnected": False,
            "status": "error",
            "credentials": None,
            "error": str(e)
        }

# Airtable routes
@router.post("/airtable/authorize")
async def airtable_authorize(request: Request):
    data = await request.json()
    return await authorize_airtable(data.get('userId'), data.get('orgId'))

@router.get("/airtable/oauth2callback")
async def airtable_callback(request: Request):
    return await oauth2callback_airtable(request)

@router.get("/airtable/status")
async def airtable_status(userId: str, orgId: str = None):
    try:
        creds = await get_airtable_credentials(userId, orgId)
        return await get_status_response(creds)
    except Exception as e:
        return {
            "isConnected": False,
            "status": "error",
            "credentials": None,
            "error": str(e)
        }

# HubSpot routes
@router.post("/hubspot/authorize")
async def hubspot_authorize(request: Request):
    data = await request.json()
    return await authorize_hubspot(data.get('userId'), data.get('orgId'))

@router.get("/hubspot/oauth2callback")
async def hubspot_callback(request: Request):
    return await oauth2callback_hubspot(request)

@router.get("/hubspot/status")
async def hubspot_status(userId: str, orgId: str = None):
    try:
        creds = await get_hubspot_credentials(userId, orgId)
        return await get_status_response(creds)
    except Exception as e:
        return {
            "isConnected": False,
            "status": "error",
            "credentials": None,
            "error": str(e)
        }

# Slack routes
@router.post("/slack/authorize")
async def slack_authorize(request: Request):
    data = await request.json()
    return await authorize_slack(data.get('userId'), data.get('orgId'))

@router.get("/slack/oauth2callback")
async def slack_callback(request: Request):
    return await oauth2callback_slack(request)

@router.get("/slack/status")
async def slack_status(userId: str, orgId: str = None):
    try:
        creds = await get_slack_credentials(userId, orgId)
        return await get_status_response(creds)
    except Exception as e:
        return {
            "isConnected": False,
            "status": "error",
            "credentials": None,
            "error": str(e)
        }

# Data fetching routes
@router.get("/notion/data")
async def notion_data(userId: str, orgId: str = None):
    creds = await get_notion_credentials(userId, orgId)
    if not creds or not creds.get('credentials'):
        raise HTTPException(status_code=401, detail="Not connected to Notion")
    return await get_items_notion(creds['credentials'])

@router.get("/airtable/data")
async def airtable_data(userId: str, orgId: str = None):
    creds = await get_airtable_credentials(userId, orgId)
    if not creds or not creds.get('credentials'):
        raise HTTPException(status_code=401, detail="Not connected to Airtable")
    return await get_items_airtable(creds['credentials'])

@router.get("/hubspot/data")
async def hubspot_data(userId: str, orgId: str = None):
    creds = await get_hubspot_credentials(userId, orgId)
    if not creds or not creds.get('credentials'):
        raise HTTPException(status_code=401, detail="Not connected to HubSpot")
    return await get_items_hubspot(creds['credentials'])

@router.get("/slack/data")
async def slack_data(userId: str, orgId: str = None):
    creds = await get_slack_credentials(userId, orgId)
    if not creds or not creds.get('credentials'):
        raise HTTPException(status_code=401, detail="Not connected to Slack")
    return await get_items_slack(creds['credentials'])
