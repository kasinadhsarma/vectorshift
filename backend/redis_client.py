import redis
import os
import json
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB = int(os.getenv('REDIS_DB', '0'))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

# Create a single Redis connection pool
redis_pool = redis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=True,
    socket_timeout=5,
    retry_on_timeout=True
)

# Create a single Redis client instance
redis_client = redis.Redis(connection_pool=redis_pool)

def check_redis_connection():
    """Check if Redis connection is alive"""
    try:
        redis_client.ping()
        return True
    except (redis.ConnectionError, redis.RedisError) as e:
        print(f"Redis connection error: {str(e)}")
        return False

async def add_key_value_redis(key: str, value: str, expire: int = None):
    """Add a key-value pair to Redis with optional expiration."""
    if not check_redis_connection():
        raise HTTPException(status_code=500, detail="Redis connection failed")
    
    try:
        redis_client.set(key, value)
        if expire:
            redis_client.expire(key, expire)
        return True
    except redis.RedisError as e:
        print(f"Redis set error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Redis operation failed: {str(e)}")

async def get_value_redis(key: str) -> str:
    """Get a value from Redis by key."""
    if not check_redis_connection():
        raise HTTPException(status_code=500, detail="Redis connection failed")
    
    try:
        return redis_client.get(key)
    except redis.RedisError as e:
        print(f"Redis get error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Redis operation failed: {str(e)}")

async def delete_key_redis(key: str):
    """Delete a key from Redis."""
    if not check_redis_connection():
        raise HTTPException(status_code=500, detail="Redis connection failed")
    
    try:
        redis_client.delete(key)
        return True
    except redis.RedisError as e:
        print(f"Redis delete error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Redis operation failed: {str(e)}")

async def store_user_token(user_id: str, token_data: dict, expire: int = 3600):
    """Store user token data in Redis."""
    if not check_redis_connection():
        raise HTTPException(status_code=500, detail="Redis connection failed")
    
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    try:
        # Ensure token_data is serializable
        serialized_data = json.dumps(token_data)
        
        # Store with namespace to avoid conflicts
        key = f"user_token:{user_id}"
        
        # Use Redis transaction to ensure atomicity
        with redis_client.pipeline() as pipe:
            pipe.set(key, serialized_data)
            if expire:
                pipe.expire(key, expire)
            pipe.execute()
        
        # Verify storage
        stored_data = redis_client.get(key)
        if not stored_data:
            raise HTTPException(status_code=500, detail="Failed to verify token storage")
        
        return True
    except json.JSONDecodeError as e:
        print(f"JSON serialization error: {str(e)}")
        print(f"Token data: {token_data}")
        raise HTTPException(status_code=500, detail="Failed to serialize token data")
    except redis.RedisError as e:
        print(f"Redis error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to store token in Redis")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to store user session: {str(e)}")

def format_credentials_key(provider: str, org_id: str, user_id: str) -> str:
    """Format the Redis key for storing integration credentials."""
    return f"{provider}_credentials:{org_id}:{user_id}"

def format_state_key(provider: str, state: str) -> str:
    """Format the Redis key for storing OAuth state."""
    return f"{provider}_state:{state}"
