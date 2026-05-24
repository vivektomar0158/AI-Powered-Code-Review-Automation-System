from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

from app.db.session import get_db
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["System"])

@router.get("")
async def health_check(db: AsyncSession = Depends(get_db)):
    """System health check."""
    health_status = {
        "status": "healthy",
        "database": "unknown",
        "redis": "unknown",
        "gemini": "configured" if settings.GEMINI_API_KEY else "missing",
        "github": "configured" if settings.get_github_private_key() else "missing",
    }
    
    # Check DB
    try:
        await db.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = "disconnected"
        health_status["status"] = "degraded"
        logger.error(f"DB health check failed: {e}")
        
    # Check Redis could be added here
    
    return health_status
