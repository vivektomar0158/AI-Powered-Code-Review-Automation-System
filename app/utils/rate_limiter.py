import time
from app.utils.cache import cache_service
from app.core.config import settings

class RateLimiter:
    """Token bucket style rate limiter using Redis."""
    
    async def is_rate_limited(self, identifier: str, limit: int, window: int) -> bool:
        """
        Check if the identifier has exceeded the limit within the window.
        Returns True if limited.
        """
        current_time = int(time.time())
        window_start = current_time - window
        
        key = f"rate_limit:{identifier}"
        
        # We would use Redis sorted sets or simple counters here.
        # For MVP, simple counter with expiry.
        count = await cache_service.get(key) or 0
        if count >= limit:
            return True
            
        await cache_service.set(key, count + 1, ttl=window)
        return False
        
rate_limiter = RateLimiter()
