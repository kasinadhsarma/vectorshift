from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import Dict, Optional, List
from pydantic import BaseModel
from integrations import notion, airtable, hubspot, slack

router = APIRouter(prefix="/integrations")

class AuthorizeRequest(BaseModel):
    userId: str
    orgId: Optional[str] = None

    class Config:
        populate_by_name = True
        alias_generator = lambda string: string.replace('Id', '_id')

class DataRequest(BaseModel):
    credentials: Dict
    userId: str
    orgId: Optional[str] = None

    class Config:
        populate_by_name = True
        alias_generator = lambda string: string.replace('Id', '_id')

# Notion routes
@router.post("/notion/authorize")
async def authorize_notion(request: AuthorizeRequest):
    try:
        print(f"Authorizing Notion with userId: {request.userId}, orgId: {request.orgId}")
        response = await notion.authorize_notion(request.userId, request.orgId)
        print(f"Notion authorization response: {response}")
        return response
    except Exception as e:
        import traceback
        error_details = f"Error authorizing Notion: {str(e)}\n{traceback.format_exc()}"
        print(error_details)
        raise HTTPException(status_code=500, detail=error_details)

@router.get("/notion/oauthCallback", include_in_schema=False)
async def notion_callback(request: Request):
    try:
        return await notion.oauth2callback_notion(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notion/status")
async def get_notion_status(user_id: str = Query(..., alias="userId"), org_id: str = Query(None, alias="orgId")):
    try:
        credentials = await notion.get_notion_credentials(user_id, org_id)
        return {
            "isConnected": credentials is not None,
            "status": "active" if credentials else "inactive",
            "credentials": credentials
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/notion/data")
async def get_notion_data(request: DataRequest):
    try:
        data = await notion.get_items_notion(request.credentials)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Airtable routes
@router.post("/airtable/authorize")
async def authorize_airtable(request: AuthorizeRequest):
    try:
        auth_url = await airtable.authorize_airtable(request.userId, request.orgId)
        return {"url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/airtable/oauth2callback")
async def airtable_callback(request: Request):
    try:
        return await airtable.oauth2callback_airtable(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/airtable/status")
async def get_airtable_status(user_id: str = Query(..., alias="userId"), org_id: str = Query(None, alias="orgId")):
    try:
        credentials = await airtable.get_airtable_credentials(user_id, org_id)
        return {
            "isConnected": credentials is not None,
            "status": "active" if credentials else "inactive",
            "credentials": credentials
        }
    except Exception as e:
        if isinstance(e, HTTPException) and e.status_code == 404:
            return {
                "isConnected": False,
                "status": "inactive"
            }
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/airtable/data")
async def get_airtable_data(request: DataRequest):
    try:
        items = await airtable.get_items_airtable(request.credentials, request.userId, request.orgId)
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# HubSpot routes
@router.post("/hubspot/authorize")
async def authorize_hubspot(request: AuthorizeRequest):
    try:
        result = await hubspot.authorize_hubspot(request.userId, request.orgId)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hubspot/oauth2callback")
async def hubspot_callback(request: Request):
    try:
        return await hubspot.oauth2callback_hubspot(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hubspot/status")
async def get_hubspot_status(user_id: str = Query(..., alias="userId"), org_id: str = Query(None, alias="orgId")):
    try:
        credentials = await hubspot.get_hubspot_credentials(user_id, org_id)
        return {
            "isConnected": credentials is not None,
            "status": "active" if credentials else "inactive",
            "credentials": credentials
        }
    except Exception as e:
        if isinstance(e, HTTPException) and e.status_code == 404:
            return {
                "isConnected": False,
                "status": "inactive"
            }
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/hubspot/data")
async def get_hubspot_data(request: DataRequest):
    try:
        items = await hubspot.get_items_hubspot(request.userId, request.orgId)
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Slack routes
@router.post("/slack/authorize")
async def authorize_slack(request: AuthorizeRequest):
    try:
        auth_url = await slack.authorize_slack(request.userId, request.orgId)
        return {"auth_url": auth_url}
    except HTTPException as e:
        if e.status_code == 400 and "invalid_scope" in e.detail:
            return {"detail": "Invalid scope provided for Slack authorization"}, 400
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/slack/oauth2callback")
async def slack_callback(request: Request):
    try:
        return await slack.oauth2callback_slack(request)
    except HTTPException as e:
        if e.status_code == 400 and "invalid_scope" in e.detail:
            return {"detail": "Invalid scope provided for Slack authorization"}, 400
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/slack/status")
async def get_slack_status(user_id: str = Query(..., alias="userId"), org_id: str = Query(None, alias="orgId")):
    try:
        credentials = await slack.get_slack_credentials(user_id, org_id)
        return {
            "isConnected": credentials is not None,
            "status": "active" if credentials else "inactive",
            "credentials": credentials
        }
    except HTTPException as e:
        if e.status_code == 400 and "invalid_scope" in e.detail:
            return {"detail": "Invalid scope provided for Slack authorization"}, 400
        raise e
    except Exception as e:
        if isinstance(e, HTTPException) and e.status_code == 404:
            return {
                "isConnected": False,
                "status": "inactive"
            }
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/slack/data")
async def get_slack_data(request: DataRequest):
    try:
        data = await slack.get_items_slack(request.credentials, request.userId, request.orgId)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
