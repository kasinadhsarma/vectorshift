from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Optional, List
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

