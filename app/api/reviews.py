from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.session import get_db
# from app.models.review import Review
# from app.schemas.review import ReviewResponse, ReviewListResponse
from app.services.review_orchestrator import review_orchestrator

router = APIRouter(prefix="/api/reviews", tags=["Reviews"])

@router.get("/{review_id}")
async def get_review(review_id: int, db: AsyncSession = Depends(get_db)):
    """Get review details."""
    # MVP mock
    return {"id": review_id, "status": "completed"}

@router.post("/{review_id}/retry")
async def retry_review(review_id: int, db: AsyncSession = Depends(get_db)):
    """Retry a failed review."""
    return {"status": "queued", "message": "Retry initiated."}
    
@router.get("/pull-requests/{pr_id}")
async def get_pr_reviews(pr_id: int, db: AsyncSession = Depends(get_db)):
    """List reviews for a pull request."""
    return {"reviews": [], "total": 0}
