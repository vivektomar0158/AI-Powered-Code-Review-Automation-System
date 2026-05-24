from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
# from app.schemas.review import AnalyticsResponse

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/repository/{repo_id}/summary")
async def get_repo_summary(repo_id: int, db: AsyncSession = Depends(get_db)):
    """Aggregate stats for a repository."""
    return {
        "total_reviews": 0,
        "avg_processing_time_ms": 0.0,
        "total_cost_usd": 0.0,
        "issues_by_severity": {"critical": 0, "warning": 0, "suggestion": 0},
        "agent_performance": []
    }

@router.get("/costs")
async def get_costs(db: AsyncSession = Depends(get_db)):
    """Cost breakdown and budget status."""
    return {"total_cost_usd": 0.0}
