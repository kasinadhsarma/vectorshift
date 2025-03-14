<<<<<<< Updated upstream
=======
"""Redis client module for handling credentials and state storage."""
import json
import aioredis
import logging
from typing import Optional, Any
>>>>>>> Stashed changes
import os
import json
from typing import Optional, Any
from redis.asyncio import Redis
from dotenv import load_dotenv

<<<<<<< Updated upstream
load_dotenv()

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB = int(os.getenv('REDIS_DB', '0'))

# Create Redis client
redis = Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True
)

async def add_key_value_redis(key: str, value: Any, expire: int = None) -> bool:
    """Store a key-value pair in Redis with optional expiration"""
    try:
        value_str = json.dumps(value) if not isinstance(value, str) else value
        await redis.set(key, value_str)
        if expire:
            await redis.expire(key, expire)
=======
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis connection configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

redis_client = None

async def get_redis_client():
    global redis_client
    if redis_client is None:
        try:
            redis_client = await aioredis.create_redis_pool(
                f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}',
                encoding='utf-8'
            )
            logger.info("Successfully connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise
    return redis_client

async def add_key_value_redis(key: str, value: str, expire: Optional[int] = None) -> bool:
    """Add a key-value pair to Redis with optional expiration"""
    try:
        redis = await get_redis_client()
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        await redis.set(key, value, expire=expire)
        logger.info(f"Successfully stored key: {key}")
>>>>>>> Stashed changes
        return True
    except Exception as e:
        logger.error(f"Failed to store key {key}: {str(e)}")
        return False

<<<<<<< Updated upstream
async def get_value_redis(key: str) -> Optional[Any]:
    """Get value from Redis by key"""
    try:
        value = await redis.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
=======
async def get_value_redis(key: str) -> Optional[str]:
    """Get a value from Redis by key"""
    try:
        redis = await get_redis_client()
        value = await redis.get(key)
        if value:
            logger.info(f"Successfully retrieved key: {key}")
            return value
        logger.info(f"No value found for key: {key}")
>>>>>>> Stashed changes
        return None
    except Exception as e:
        logger.error(f"Failed to retrieve key {key}: {str(e)}")
        return None

async def delete_key_redis(key: str) -> bool:
    """Delete a key from Redis"""
    try:
        redis = await get_redis_client()
        deleted = await redis.delete(key)
        if deleted:
            logger.info(f"Successfully deleted key: {key}")
        else:
            logger.info(f"Key not found for deletion: {key}")
        return bool(deleted)
    except Exception as e:
        logger.error(f"Failed to delete key {key}: {str(e)}")
        return False

<<<<<<< Updated upstream
async def store_user_token(token: str, user_data: dict, expire: int = 3600) -> bool:
    """Store user token and data in Redis"""
    key = f"user_token:{token}"
    try:
        await add_key_value_redis(key, user_data, expire)
=======
async def close_redis():
    """Close Redis connection"""
    if redis_client is not None:
        redis_client.close()
        await redis_client.wait_closed()
        logger.info("Redis connection closed")

async def store_user_token(user_id: str, token_data: dict, expire: int = 3600) -> bool:
    """Store user token data in Redis."""
    try:
        token_key = f'user_token:{user_id}'
        await add_key_value_redis(token_key, json.dumps(token_data), expire)
>>>>>>> Stashed changes
        return True
    except Exception as e:
        logger.error(f"Error storing user token: {str(e)}")
        return False

<<<<<<< Updated upstream
async def get_user_by_token(token: str) -> Optional[dict]:
    """Get user data by token"""
    key = f"user_token:{token}"
    return await get_value_redis(key)
=======
async def get_credentials(service: str, user_id: str, org_id: str) -> dict:
    """Get standardized credentials response."""
    try:
        logger.info(f"\n=== Getting {service} credentials ===")
        logger.info(f"User ID: {user_id}")
        logger.info(f"Org ID: {org_id}")

        redis_key = f'{service}_credentials:{org_id}:{user_id}'
        logger.info(f"Redis key: {redis_key}")

        raw_credentials = await get_value_redis(redis_key)
        if not raw_credentials:
            logger.info("No credentials found in Redis")
            return {
                'isConnected': False,
                'status': 'inactive',
                'credentials': None
            }
        
        try:
            credentials_data = json.loads(raw_credentials)
            logger.info("Loaded credentials from Redis:")
            logger.info(json.dumps(credentials_data, indent=2))

            # Return credentials in a standardized format
            response = {
                'isConnected': True,
                'status': 'active',
                'credentials': {
                    'access_token': credentials_data.get('access_token'),
                    'token_type': credentials_data.get('token_type', 'Bearer'),
                    'workspace_name': credentials_data.get('workspace_name'),
                    'workspace_id': credentials_data.get('workspace_id')
                }
            }
            logger.info("Standardized response:")
            logger.info(json.dumps(response, indent=2))
            return response

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse credentials: {e}")
            return {
                'isConnected': False,
                'status': 'error',
                'credentials': None,
                'error': 'Invalid credentials format'
            }
    except Exception as e:
        logger.error(f"Error getting credentials: {e}")
        return {
            'isConnected': False,
            'status': 'error',
            'credentials': None,
            'error': str(e)
        }
    finally:
        logger.info("=== Credentials lookup complete ===\n")
>>>>>>> Stashed changes
