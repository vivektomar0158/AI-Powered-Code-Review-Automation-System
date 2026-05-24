import logging
from datetime import datetime
from app.utils.cache import cache_service
from app.core.config import settings

logger = logging.getLogger(__name__)

class CostTracker:
    def __init__(self):
        # Rough estimation for Gemini 2.0 Flash
        self.input_cost_per_1k = 0.00015
        self.output_cost_per_1k = 0.0006

    async def add_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate and track cost for a request."""
        cost = (input_tokens / 1000) * self.input_cost_per_1k + \
               (output_tokens / 1000) * self.output_cost_per_1k
               
        today = datetime.utcnow().strftime("%Y-%m-%d")
        key = f"daily_cost:{today}"
        
        current_cost = await cache_service.get(key) or 0.0
        new_cost = current_cost + cost
        
        await cache_service.set(key, new_cost, ttl=86400 * 2)  # Keep for 2 days
        
        if new_cost >= settings.MAX_COST_PER_DAY_USD:
            logger.error(f"DAILY BUDGET EXCEEDED: ${new_cost}")
        elif new_cost >= (settings.MAX_COST_PER_DAY_USD * settings.COST_ALERT_THRESHOLD_PERCENT / 100):
            logger.warning(f"DAILY BUDGET ALERT: ${new_cost} consumed")
            
        return cost

cost_tracker = CostTracker()
