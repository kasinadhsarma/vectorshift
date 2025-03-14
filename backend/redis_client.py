"""Redis client module for handling credentials and state storage."""
import os
import json
import logging
from typing import Optional, Any
from redis.asyncio import Redis
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Redis connection configuration
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

async def add_key_value_redis(key: str, value: Any, expire: Optional[int] = None) -> bool:
    """Store a key-value pair in Redis with optional expiration"""
    try:
        value_str = json.dumps(value) if not isinstance(value, str) else value
        await redis.set(key, value_str)
        if expire:
            await redis.expire(key, expire)
        logger.info(f"Successfully stored key: {key}")
        return True
    except Exception as e:
        logger.error(f"Failed to store key {key}: {str(e)}")
        return False

async def get_value_redis(key: str) -> Optional[Any]:
    """Get value from Redis by key"""
    try:
        value = await redis.get(key)
        if value:
            try:
                parsed_value = json.loads(value)
                logger.info(f"Successfully retrieved key: {key}")
                return parsed_value
            except json.JSONDecodeError:
                return value
        logger.info(f"No value found for key: {key}")
        return None
    except Exception as e:
        logger.error(f"Failed to retrieve key {key}: {str(e)}")
        return None

async def delete_key_redis(key: str) -> bool:
    """Delete a key from Redis"""
    try:
        deleted = await redis.delete(key)
        if deleted:
            logger.info(f"Successfully deleted key: {key}")
        else:
            logger.info(f"Key not found for deletion: {key}")
        return bool(deleted)
    except Exception as e:
        logger.error(f"Failed to delete key {key}: {str(e)}")
        return False

async def close_redis():
    """Close Redis connection"""
    await redis.close()
    logger.info("Redis connection closed")

async def store_user_token(user_id: str, token_data: dict, expire: int = 3600) -> bool:
    """Store user token data in Redis."""
    try:
        token_key = f'user_token:{user_id}'
        await add_key_value_redis(token_key, token_data, expire)
        return True
    except Exception as e:
        logger.error(f"Error storing user token: {str(e)}")
        return False

async def get_credentials(service: str, user_id: str, org_id: str) -> dict:
    """Get standardized credentials response."""
    try:
        logger.info(f"\n=== Getting {service} credentials ===")
        logger.info(f"User ID: {user_id}")
        logger.info(f"Org ID: {org_id}")

        redis_key = f'{service}_credentials:{org_id}:{user_id}'
        logger.info(f"Redis key: {redis_key}")

        credentials_data = await get_value_redis(redis_key)
        if not credentials_data:
            logger.info("No credentials found in Redis")
            return {
                'isConnected': False,
                'status': 'inactive',
                'credentials': None
            }

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
