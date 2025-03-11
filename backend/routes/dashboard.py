from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, List
from datetime import datetime, timedelta
from cassandra_client import CassandraClient
from redis_client import get_value_redis

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
    return user_data

@router.get("/api/users/{user_id}/dashboard")
async def get_user_dashboard(user_id: str, current_user: Dict = Depends(get_current_user)):
    """Get user-specific dashboard data"""
    try:
        # Verify user has access to this dashboard
        if user_id != current_user.get("email", "").split("@")[0]:
            raise HTTPException(status_code=403, detail="Not authorized to access this dashboard")

        # Get user's integrations from database
        integrations = await cassandra.get_user_integrations(user_id)
        
        # Calculate statistics
        now = datetime.now()
        total_integrations = len(integrations)
        active_integrations = sum(1 for i in integrations if i["status"] == "active")
        
        # Get last month's data (mock data for now)
        last_month_total = total_integrations - 2
        last_month_active = active_integrations - 1
        
        # Get sync data (mock data for now)
        total_syncs = 28
        last_week_syncs = 20
        
        # Format active integrations for frontend
        formatted_integrations = [
            {
                "name": integration["name"],
                "status": integration["status"],
                "lastSync": integration["last_sync"].isoformat() if integration.get("last_sync") else None,
                "details": f"{integration.get('workspace_count', 0)} workspaces"
            }
            for integration in integrations
            if integration["status"] == "active"
        ]
        
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
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard data: {str(e)}")

@router.post("/api/users/{user_id}/dashboard/refresh")
async def refresh_dashboard_data(user_id: str, current_user: Dict = Depends(get_current_user)):
    """Refresh user's dashboard data"""
    try:
        if user_id != current_user.get("email", "").split("@")[0]:
            raise HTTPException(status_code=403, detail="Not authorized to refresh this dashboard")
            
        # Implement refresh logic here
        # This could involve re-fetching data from integrated services
        
        return {"message": "Dashboard data refreshed successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh dashboard data: {str(e)}")
