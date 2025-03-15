import os
import logging
import redis.asyncio as redis
from kombu.utils.url import safequote
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        self.redis_host = safequote(os.environ.get('REDIS_HOST', 'localhost'))
        self.redis_port = int(os.environ.get('REDIS_PORT', 6379))
        self.redis_db = int(os.environ.get('REDIS_DB', 0))
        self._client = None
        self._connect()

    def _connect(self):
        try:
            self._client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                decode_responses=True,
                socket_timeout=5,
                retry_on_timeout=True
            )
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise HTTPException(status_code=503, detail="Redis connection failed")

    async def check_connection(self):
        try:
            await self._client.ping()
            return True
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.error(f"Redis connection check failed: {str(e)}")
            self._connect()
            return False

    async def add_key_value_redis(self, key, value, expire=None):
        try:
            await self.check_connection()
            await self._client.set(key, value)
            if expire:
                await self._client.expire(key, expire)
        except Exception as e:
            logger.error(f"Error setting Redis key {key}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to store data in Redis")

    async def get_value_redis(self, key):
        try:
            await self.check_connection()
            value = await self._client.get(key)
            if value is None:
                logger.warning(f"No value found for key: {key}")
            return value
        except Exception as e:
            logger.error(f"Error getting Redis key {key}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to retrieve data from Redis")

    async def delete_key_redis(self, key):
        try:
            await self.check_connection()
            await self._client.delete(key)
        except Exception as e:
            logger.error(f"Error deleting Redis key {key}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to delete data from Redis")

# Create global redis client instance
redis_client = RedisClient()

# Export functions that use the client instance
async def add_key_value_redis(key, value, expire=None):
    await redis_client.add_key_value_redis(key, value, expire)

async def get_value_redis(key):
    return await redis_client.get_value_redis(key)

async def delete_key_redis(key):
    await redis_client.delete_key_redis(key)
