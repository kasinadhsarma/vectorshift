import os
import json
from typing import Optional, Any
from redis.asyncio import Redis
from dotenv import load_dotenv

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
        return True
    except Exception as e:
        print(f"Error adding to Redis: {str(e)}")
        return False

async def get_value_redis(key: str) -> Optional[Any]:
    """Get value from Redis by key"""
    try:
        value = await redis.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    except Exception as e:
        print(f"Error getting from Redis: {str(e)}")
        return None

async def delete_key_redis(key: str) -> bool:
    """Delete a key from Redis"""
    try:
        await redis.delete(key)
        return True
    except Exception as e:
        print(f"Error deleting from Redis: {str(e)}")
        return False

async def store_user_token(token: str, user_data: dict, expire: int = 3600) -> bool:
    """Store user token and data in Redis"""
    key = f"user_token:{token}"
    try:
        await add_key_value_redis(key, user_data, expire)
        return True
    except Exception as e:
        print(f"Error storing user token: {str(e)}")
        return False

async def get_user_by_token(token: str) -> Optional[dict]:
    """Get user data by token"""
    key = f"user_token:{token}"
    return await get_value_redis(key)
