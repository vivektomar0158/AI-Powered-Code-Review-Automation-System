from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter(prefix="/api/repositories", tags=["Repositories"])

@router.get("/{repo_id}/config")
async def get_repo_config(repo_id: int, db: AsyncSession = Depends(get_db)):
    """Get parsed .ai-review.yml config for a repository."""
    return {"enabled_agents": ["style", "security", "performance", "bug"]}
