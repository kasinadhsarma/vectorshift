"""Redis client module for handling credentials and state storage."""
import os
import json
import logging
from typing import Optional, Any, Union
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
    """Store a key-value pair in Redis with optional expiration."""
    try:
        logger.info(f"Storing key: {key}")
        value_str = json.dumps(value) if not isinstance(value, str) else value
        
        if expire:
            await redis.set(key, value_str, ex=expire)
        else:
            await redis.set(key, value_str)
            
        logger.info(f"Successfully stored key: {key}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to store key {key}: {str(e)}")
        return False

async def get_value_redis(key: str) -> Optional[Union[str, dict]]:
    """Get a value from Redis by key."""
    try:
        logger.info(f"Retrieving key: {key}")
        value = await redis.get(key)
        
        if not value:
            logger.info(f"No value found for key: {key}")
            return None
            
        try:
            # Try to parse JSON
            parsed_value = json.loads(value)
            logger.info(f"Successfully retrieved and parsed key: {key}")
            return parsed_value
        except json.JSONDecodeError:
            # Return raw value if not JSON
            logger.info(f"Successfully retrieved key: {key} (raw value)")
            return value
            
    except Exception as e:
        logger.error(f"Failed to retrieve key {key}: {str(e)}")
        return None

async def delete_key_redis(key: str) -> bool:
    """Delete a key from Redis."""
    try:
        logger.info(f"Deleting key: {key}")
        deleted = await redis.delete(key)
        
        if deleted:
            logger.info(f"Successfully deleted key: {key}")
        else:
            logger.info(f"Key not found for deletion: {key}")
            
        return bool(deleted)
        
    except Exception as e:
        logger.error(f"Failed to delete key {key}: {str(e)}")
        return False

async def close_redis() -> None:
    """Close Redis connection."""
    try:
        logger.info("Closing Redis connection")
        await redis.close()
        logger.info("Redis connection closed successfully")
        
    except Exception as e:
        logger.error(f"Error closing Redis connection: {str(e)}")

async def store_user_token(user_id: str, token_data: dict, expire: int = 3600) -> bool:
    """Store user token data in Redis."""
    try:
        logger.info(f"Storing token for user: {user_id}")
        token_key = f'user_token:{user_id}'
        return await add_key_value_redis(token_key, token_data, expire)
        
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
        
        raw_credentials = await get_value_redis(redis_key)
        if not raw_credentials:
            logger.info("No credentials found in Redis")
            return {
                'isConnected': False,
                'status': 'inactive',
                'credentials': None
            }
        
        # Format the response
        response = {
            'isConnected': True,
            'status': 'active',
            'credentials': raw_credentials
        }
        
        logger.info("Successfully retrieved credentials")
        return response
        
    except Exception as e:
        logger.error(f"Error getting credentials: {str(e)}")
        return {
            'isConnected': False,
            'status': 'error',
            'credentials': None,
            'error': str(e)
        }
    finally:
        logger.info("=== Credentials lookup complete ===\n")
