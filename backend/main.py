from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
import redis
import logging
from cassandra.cluster import NoHostAvailable, Session, Cluster

from integrations.airtable import authorize_airtable, get_items_airtable, oauth2callback_airtable, get_airtable_credentials
from integrations.notion import authorize_notion, get_items_notion, oauth2callback_notion, get_notion_credentials
from integrations.hubspot import authorize_hubspot, get_hubspot_credentials, get_items_hubspot, oauth2callback_hubspot
from integrations.slack import authorize_slack, get_items_slack, oauth2callback_slack, get_slack_credentials
from redis_client import redis_client
from cassandra_client import cassandra_client, cassandra_session
from auth import router as auth_router, add_cassandra_connection

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def initialize_services():
    """Initialize required services"""
    services_status = {
        "redis": False,
        "cassandra": False
    }
    
    # Check Redis
    try:
        await redis_client.check_connection()
        services_status["redis"] = True
        logger.info("Redis connection successful")
    except Exception as e:
        logger.error(f"Redis connection failed: {str(e)}")
        
    # Check Cassandra
    try:
        cassandra_session.execute('SELECT now() FROM system.local')
        services_status["cassandra"] = True
        logger.info("Cassandra connection successful")
    except NoHostAvailable as e:
        logger.error(f"Cassandra connection failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected Cassandra error: {str(e)}")
    
    return services_status

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Initialize services
    services_status = await initialize_services()
    
    # Log startup status
    for service, status in services_status.items():
        if not status:
            logger.warning(f"{service.title()} service is not available")
    
    yield
    
    # Cleanup
    try:
        await cassandra_client.close()
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")

app = FastAPI(title="VectorShift API", lifespan=lifespan)
# Add Cassandra connection
add_cassandra_connection(app)

# Include auth router
app.include_router(auth_router, prefix="/auth", tags=["authentication"])

# CORS configuration
origins = [
    "http://localhost:3000",  # React app address
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/health')
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "services": {
            "redis": "healthy",
            "cassandra": "healthy",
            "api": "healthy"
        },
        "details": {}
    }
    
    # Check Redis
    try:
        await redis_client.check_connection()
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["services"]["redis"] = "unhealthy"
        health_status["details"]["redis"] = str(e)
    
    # Check Cassandra
    try:
        cassandra_session.execute('SELECT now() FROM system.local')
    except (NoHostAvailable, Exception) as e:
        health_status["status"] = "degraded"
        health_status["services"]["cassandra"] = "unhealthy"
        health_status["details"]["cassandra"] = str(e)
    
    return health_status

@app.get('/')
def read_root():
    """Root endpoint"""
    return {'status': 'ok', 'version': '1.0.0'}

# Integration status check helper
async def check_integration_status(
    user_id: str,
    org_id: str,
    get_credentials_fn,
    integration_name: str
):
    """Check integration status with proper error handling"""
    if not user_id or not org_id:
        return {
            "status": "error",
            "isConnected": False,
            "detail": "Missing required parameters",
            "requiredParams": ["userId", "orgId"]
        }
    
    try:
        # Check Redis health first
        try:
            await redis_client.check_connection()
        except Exception as e:
            logger.error(f"Redis error for {integration_name}: {str(e)}")
            return {
                "status": "error",
                "isConnected": False,
                "detail": "Redis connection failed",
                "error": str(e),
                "service": integration_name
            }

        # Check Cassandra health
        try:
            cassandra_session.execute('SELECT now() FROM system.local')
        except Exception as e:
            logger.error(f"Cassandra error for {integration_name}: {str(e)}")
            return {
                "status": "error",
                "isConnected": False,
                "detail": "Database connection failed",
                "error": str(e),
                "service": integration_name
            }

        # Get credentials
        credentials = await get_credentials_fn(user_id, org_id)
        return {
            "status": "success",
            "isConnected": bool(credentials),
            "credentials": credentials,
            "service": integration_name
        }
    except Exception as e:
        logger.error(f"Error checking {integration_name} status: {str(e)}")
        return {
            "status": "error",
            "isConnected": False,
            "detail": str(e),
            "service": integration_name
        }

# Integration endpoints
# Airtable endpoints
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
    return await get_items_airtable(credentials)

# Notion endpoints
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
    return await get_items_notion(credentials)

# Hubspot endpoints
@app.post('/integrations/hubspot/authorize')
async def authorize_hubspot_integration(user_id: str = Form(...), org_id: str = Form(...)):
    return await authorize_hubspot(user_id, org_id)

@app.get('/integrations/hubspot/oauth2callback')
async def oauth2callback_hubspot_integration(request: Request):
    return await oauth2callback_hubspot(request)

@app.post('/integrations/hubspot/credentials')
async def get_hubspot_credentials_integration(user_id: str = Form(...), org_id: str = Form(...)):
    return await get_hubspot_credentials(user_id, org_id)

# Slack endpoints
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
async def get_slack_items(credentials: str = Form(...)):
    return await get_items_slack(credentials)

# Status endpoints
@app.get('/integrations/airtable/status')
async def get_airtable_status(user_id: str = None, org_id: str = None):
    return await check_integration_status(user_id, org_id, get_airtable_credentials, "airtable")

@app.get('/integrations/notion/status')
async def get_notion_status(user_id: str = None, org_id: str = None):
    return await check_integration_status(user_id, org_id, get_notion_credentials, "notion")

@app.get('/integrations/slack/status')
async def get_slack_status(user_id: str = None, org_id: str = None):
    return await check_integration_status(user_id, org_id, get_slack_credentials, "slack")

@app.get('/integrations/hubspot/status')
async def get_hubspot_status(user_id: str = None, org_id: str = None):
    return await check_integration_status(user_id, org_id, get_hubspot_credentials, "hubspot")

@app.get('/integrations/status')
async def get_all_integrations_status(user_id: str = None, org_id: str = None):
    """Get status of all integrations"""
    if not user_id or not org_id:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "detail": "Missing required parameters",
                "requiredParams": ["userId", "orgId"]
            }
        )
    
    integrations = {
        "airtable": get_airtable_credentials,
        "notion": get_notion_credentials,
        "slack": get_slack_credentials,
        "hubspot": get_hubspot_credentials
    }
    
    results = {}
    overall_status = "success"
    
    for integration, get_credentials in integrations.items():
        status = await check_integration_status(user_id, org_id, get_credentials, integration)
        results[integration] = status
        if status["status"] == "error":
            overall_status = "degraded"
    
    return {
        "status": overall_status,
        "integrations": results
    }
