from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, func
from sqlalchemy.dialects.postgresql import JSONB
from app.models.repository import Base

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    pull_request_id = Column(Integer, ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    
    status = Column(String(50), default="pending", nullable=False, index=True)
    
    total_issues = Column(Integer, default=0)
    critical_issues = Column(Integer, default=0)
    warnings = Column(Integer, default=0)
    suggestions = Column(Integer, default=0)
    
    processing_time_ms = Column(Integer)
    cost_usd = Column(Numeric(10, 4))
    agent_versions = Column(JSONB)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    completed_at = Column(DateTime(timezone=True))
