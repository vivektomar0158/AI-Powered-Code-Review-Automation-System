import json
import logging
from typing import Any, Optional
import redis.asyncio as redis
from app.core.config import settings

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def get(self, key: str) -> Optional[Any]:
        try:
            val = await self.redis_client.get(key)
            if val:
                return json.loads(val)
            return None
        except Exception as e:
            logger.error(f"Redis get failed for {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        try:
            await self.redis_client.setex(key, ttl, json.dumps(value))
            return True
        except Exception as e:
            logger.error(f"Redis set failed for {key}: {e}")
            return False
            
    async def delete(self, key: str) -> bool:
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete failed for {key}: {e}")
            return False

cache_service = CacheService()
