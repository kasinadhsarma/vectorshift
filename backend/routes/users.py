"""User routes for handling user-specific data and dashboard information."""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class UserInfo(BaseModel):
    """User information model."""
    id: str
    name: str
    email: str

class Integration(BaseModel):
    """Integration status model."""
    type: str
    status: str
    lastSync: Optional[str] = None
    details: Optional[str] = None

class Activity(BaseModel):
    """User activity model."""
    id: int
    type: str
    integration: Optional[str] = None
    timestamp: str

class IntegrationStats(BaseModel):
    """Integration statistics model."""
    total: int
    active: int
    lastMonthTotal: int
    lastMonthActive: int

class DataSyncStats(BaseModel):
    """Data sync statistics model."""
    total: int
    lastWeekTotal: int

class UserDashboardResponse(BaseModel):
    """Complete dashboard response model."""
    user: UserInfo
    integrations: IntegrationStats
    dataSyncs: DataSyncStats
    usage: int
    activeIntegrations: List[Integration]
    recentActivity: List[Activity]

@router.get("/{user_id}/dashboard", response_model=UserDashboardResponse)
async def get_user_dashboard(user_id: str) -> UserDashboardResponse:
    """
    Get user dashboard information including user details, integrations, and activity.
    
    Args:
        user_id: The unique identifier of the user
        
    Returns:
        UserDashboardResponse: Complete dashboard information
        
    Raises:
        HTTPException: If there's an error fetching the dashboard data
    """
    try:
        logger.info(f"Fetching dashboard data for user: {user_id}")
        
        # Get current timestamp
        current_time = datetime.utcnow().isoformat()
        
        # Mock data structure matching the frontend requirements
        dashboard_data = {
            "user": {
                "id": user_id,
                "name": "Test User",
                "email": "test@example.com"
            },
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
                    "type": "notion",
                    "status": "active",
                    "lastSync": current_time,
                    "details": "2 workspaces"
                }
            ],
            "recentActivity": [
                {
                    "id": 1,
                    "type": "login",
                    "timestamp": current_time
                },
                {
                    "id": 2,
                    "type": "integration_connected",
                    "integration": "notion",
                    "timestamp": current_time
                }
            ]
        }
        
        logger.info(f"Successfully fetched dashboard data for user: {user_id}")
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error in get_user_dashboard: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch dashboard data: {str(e)}"
        )

@router.get("/{user_id}/activity")
async def get_user_activity(
    user_id: str,
    limit: Optional[int] = Query(default=10, le=100),
    offset: Optional[int] = Query(default=0, ge=0)
) -> List[Activity]:
    """
    Get user activity history with pagination.
    
    Args:
        user_id: The unique identifier of the user
        limit: Maximum number of activities to return
        offset: Number of activities to skip
        
    Returns:
        List[Activity]: List of user activities
        
    Raises:
        HTTPException: If there's an error fetching the activity data
    """
    try:
        logger.info(f"Fetching activity for user: {user_id} (limit: {limit}, offset: {offset})")
        
        # Mock activity data
        current_time = datetime.utcnow().isoformat()
        activities = [
            {
                "id": 1,
                "type": "login",
                "timestamp": current_time
            },
            {
                "id": 2,
                "type": "integration_connected",
                "integration": "notion",
                "timestamp": current_time
            }
        ]
        
        logger.info(f"Successfully fetched {len(activities)} activities for user: {user_id}")
        return activities
        
    except Exception as e:
        logger.error(f"Error in get_user_activity: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch activity data: {str(e)}"
        )
