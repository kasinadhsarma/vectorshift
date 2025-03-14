"""Dashboard routes for handling user-specific dashboard data."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
import json
from cassandra_client import CassandraClient
from redis_client import get_value_redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()
cassandra = CassandraClient()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Validate user token and return user data."""
    try:
        token = credentials.credentials
        user_data = await get_value_redis(f"user_token:{token}")
        
        if not user_data:
            logger.error(f"Invalid token: {token}")
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Parse JSON string if needed
        if isinstance(user_data, str):
            try:
                user_data = json.loads(user_data)
            except json.JSONDecodeError:
                logger.error(f"Invalid user data format: {user_data}")
                raise HTTPException(
                    status_code=500,
                    detail="Invalid user data format"
                )
                
        if not isinstance(user_data, dict):
            logger.error(f"User data is not a dictionary: {type(user_data)}")
            raise HTTPException(
                status_code=500,
                detail="Invalid user data structure"
            )
            
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_current_user: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during authentication"
        )

@router.get("/users/{hashed_id}/dashboard")
async def get_user_dashboard(
    hashed_id: str,
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """Get user-specific dashboard data."""
    try:
        logger.info(f"Fetching dashboard data for hashed_id: {hashed_id}")
        
        # Get original user ID from email
        email = current_user.get("email")
        if not email:
            logger.error("No email found in user data")
            raise HTTPException(status_code=400, detail="Invalid user data: missing email")
            
        original_user_id = email.split("@")[0]
        
        # Check if hashed ID matches
        if hashed_id != cassandra.hash_user_id(original_user_id):
            logger.error(f"Unauthorized dashboard access attempt for user: {original_user_id}")
            raise HTTPException(status_code=403, detail="Not authorized to access this dashboard")

        # Get user's integrations from database
        integrations = await cassandra.get_user_integrations(original_user_id)
        if integrations is None:
            logger.info(f"No integrations found for user: {original_user_id}")
            integrations = []

        # Calculate statistics
        now = datetime.now()
        total_integrations = len(integrations)
        active_integrations = sum(1 for i in integrations if i.get("status") == "active")
        
        # Get last month's data (with safety checks)
        last_month_total = max(0, total_integrations - 2)
        last_month_active = max(0, active_integrations - 1)
        
        # Get sync data (mock data for now)
        total_syncs = 28
        last_week_syncs = 20
        
        # Format active integrations for frontend
        formatted_integrations = []
        for integration in integrations:
            if integration.get("status") == "active":
                last_sync = integration.get("last_sync")
                if isinstance(last_sync, datetime):
                    last_sync_iso = last_sync.isoformat()
                else:
                    last_sync_iso = now.isoformat()
                    
                formatted_integrations.append({
                    "name": integration.get("name", "Unknown"),
                    "status": integration.get("status", "inactive"),
                    "lastSync": last_sync_iso,
                    "details": f"{integration.get('workspace_count', 0)} workspaces"
                })
        
        response_data = {
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
        
        logger.info(f"Successfully fetched dashboard data for user: {original_user_id}")
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_user_dashboard: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch dashboard data: {str(e)}"
        )

@router.post("/users/{hashed_id}/dashboard/refresh")
async def refresh_dashboard_data(
    hashed_id: str,
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """Refresh user's dashboard data."""
    try:
        logger.info(f"Refreshing dashboard data for hashed_id: {hashed_id}")
        
        # Get original user ID from email
        email = current_user.get("email")
        if not email:
            logger.error("No email found in user data")
            raise HTTPException(status_code=400, detail="Invalid user data: missing email")
            
        original_user_id = email.split("@")[0]
        
        # Verify authorization
        if hashed_id != cassandra.hash_user_id(original_user_id):
            logger.error(f"Unauthorized dashboard refresh attempt for user: {original_user_id}")
            raise HTTPException(status_code=403, detail="Not authorized to refresh this dashboard")
        
        # TODO: Implement refresh logic here
        # This could involve re-fetching data from integrated services
        
        logger.info(f"Successfully refreshed dashboard data for user: {original_user_id}")
        return {
            "message": "Dashboard data refreshed successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in refresh_dashboard_data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh dashboard data: {str(e)}"
        )
