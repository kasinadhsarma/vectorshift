from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Optional, List
<<<<<<< HEAD
from pydantic import BaseModel, Field
from datetime import datetime

router = APIRouter()

class UserInfo(BaseModel):
    id: str
    name: str
    email: str

class Integration(BaseModel):
    type: str
    status: str

class Activity(BaseModel):
    id: int
    type: str
    integration: Optional[str] = None
    timestamp: str

class UserDashboardResponse(BaseModel):
    integrations: Dict[str, int]
    dataSyncs: Dict[str, int]
    usage: int
    activeIntegrations: List[Dict[str, str]]

@router.get("/{user_id}/dashboard", response_model=UserDashboardResponse)
async def get_user_dashboard(user_id: str):
    """
    Get user dashboard information including integrations and activity.
    """
    try:
        # Mock data structure matching the frontend requirements
        dashboard_data = {
            "integrations": {
                "total": 3,
                "active": 1,
                "lastMonthTotal": 2,
                "lastMonthActive": 1
            },
            "dataSyncs": {
                "total": 28,
                "lastWeekTotal": 20
            },
            "usage": 65,
            "activeIntegrations": [
                {
                    "name": "Notion",
                    "status": "active",
                    "lastSync": datetime.utcnow().isoformat(),
                    "details": "2 workspaces"
                }
            ]
        }
        
        return dashboard_data
        
    except Exception as e:
        print(f"Error in get_user_dashboard: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch dashboard data: {str(e)}"
        )
=======
from pydantic import BaseModel

router = APIRouter()

class UserDashboardResponse(BaseModel):
    user: Dict
    integrations: List[Dict]
    recentActivity: List[Dict]

@router.get("/{user_id}/dashboard")
async def get_user_dashboard(user_id: str):
    try:
        # In a real application, you would fetch this data from a database
        # For this example, we'll return mock data
        return {
            "user": {
                "id": user_id,
                "name": "Test User",
                "email": "test@example.com"
            },
            "integrations": [
                {"type": "notion", "status": "active"},
                {"type": "airtable", "status": "inactive"},
                {"type": "hubspot", "status": "inactive"}
            ],
            "recentActivity": [
                {"id": 1, "type": "login", "timestamp": "2023-05-15T10:30:00Z"},
                {"id": 2, "type": "integration_connected", "integration": "notion", "timestamp": "2023-05-15T10:35:00Z"}
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

>>>>>>> origin/main
