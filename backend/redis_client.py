"""Redis client module for handling credentials and state storage."""
import json
from redis import asyncio as aioredis
import os

redis = aioredis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=0,
    decode_responses=True
)

async def add_key_value_redis(key: str, value: str, expire: int = 3600) -> bool:
    """Add a key-value pair to Redis with expiration."""
    try:
        await redis.set(key, value, ex=expire)
        return True
    except Exception as e:
        print(f"Error adding to Redis: {str(e)}")
        return False

async def get_value_redis(key: str) -> str | None:
    """Get a value from Redis by key."""
    try:
        return await redis.get(key)
    except Exception as e:
        print(f"Error getting from Redis: {str(e)}")
        return None

async def delete_key_redis(key: str) -> bool:
    """Delete a key from Redis."""
    try:
        await redis.delete(key)
        return True
    except Exception as e:
        print(f"Error deleting from Redis: {str(e)}")
        return False

async def get_credentials(service: str, user_id: str, org_id: str) -> dict:
    """Get standardized credentials response."""
    try:
        raw_credentials = await get_value_redis(f'{service}_credentials:{org_id}:{user_id}')
        if not raw_credentials:
            return {
                'isConnected': False,
                'status': 'inactive',
                'credentials': None
            }
        
        try:
            credentials_data = json.loads(raw_credentials)
            await delete_key_redis(f'{service}_credentials:{org_id}:{user_id}')
            
            return {
                'isConnected': True,
                'status': 'active',
                'credentials': credentials_data
            }
        except json.JSONDecodeError:
            return {
                'isConnected': False,
                'status': 'error',
                'credentials': None,
                'error': 'Invalid credentials format'
            }
    except Exception as e:
        return {
            'isConnected': False,
            'status': 'error',
            'credentials': None,
            'error': str(e)
        }
