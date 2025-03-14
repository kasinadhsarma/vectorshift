from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, List
from datetime import datetime, timedelta
from cassandra_client import CassandraClient
from redis_client import get_value_redis
import json

router = APIRouter()
security = HTTPBearer()
cassandra = CassandraClient()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    user_data = await get_value_redis(f"user_token:{token}")
    if not user_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Parse JSON string if needed
    if isinstance(user_data, str):
        try:
            user_data = json.loads(user_data)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500,
                detail="Invalid user data format"
            )
    return user_data

@router.get("/api/users/{hashed_id}/dashboard")
async def get_user_dashboard(hashed_id: str, current_user: Dict = Depends(get_current_user)):
    """Get user-specific dashboard data"""
    try:
        # Get original user ID from email
        if not isinstance(current_user, dict):
            raise HTTPException(status_code=500, detail="Invalid user data format")
            
        original_user_id = current_user.get("email", "").split("@")[0]
        
        # Check if hashed ID matches
        if hashed_id != cassandra.hash_user_id(original_user_id):
            raise HTTPException(status_code=403, detail="Not authorized to access this dashboard")

        # Get user's integrations from database
        integrations = await cassandra.get_user_integrations(original_user_id)
        
        # Calculate statistics
        now = datetime.now()
        total_integrations = len(integrations)
        active_integrations = sum(1 for i in integrations if i.get("status") == "active")
        
        # Get last month's data
        last_month_total = max(0, total_integrations - 2)  # Ensure non-negative
        last_month_active = max(0, active_integrations - 1)  # Ensure non-negative
        
        # Get sync data
        total_syncs = 28  # Mock data
        last_week_syncs = 20  # Mock data
        
        # Format active integrations for frontend
        formatted_integrations = []
        for integration in integrations:
            if integration.get("status") == "active":
                formatted_integrations.append({
                    "name": integration.get("name", "Unknown"),
                    "status": integration.get("status", "inactive"),
                    "lastSync": integration.get("last_sync", now).isoformat() if integration.get("last_sync") else now.isoformat(),
                    "details": f"{integration.get('workspace_count', 0)} workspaces"
                })
        
        return {
            "integrations": {
                "total": total_integrations,
                "active": active_integrations,
                "lastMonthTotal": last_month_total,
                "lastMonthActive": last_month_active
            },
            "dataSyncs": {
                "total": total_syncs,
                "lastWeekTotal": last_week_syncs
            },
            "usage": 65,  # Mock usage percentage
            "activeIntegrations": formatted_integrations
        }
        
    except Exception as e:
        print(f"Error in get_user_dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard data: {str(e)}")

@router.post("/api/users/{hashed_id}/dashboard/refresh")
async def refresh_dashboard_data(hashed_id: str, current_user: Dict = Depends(get_current_user)):
    """Refresh user's dashboard data"""
    try:
        if not isinstance(current_user, dict):
            raise HTTPException(status_code=500, detail="Invalid user data format")
            
        original_user_id = current_user.get("email", "").split("@")[0]
        
        if hashed_id != cassandra.hash_user_id(original_user_id):
            raise HTTPException(status_code=403, detail="Not authorized to refresh this dashboard")
            
        # Implement refresh logic here
        # This could involve re-fetching data from integrated services
        
        return {"message": "Dashboard data refreshed successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh dashboard data: {str(e)}")
