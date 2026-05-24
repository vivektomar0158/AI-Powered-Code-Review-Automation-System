from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, DateTime, Text, func
from app.models.repository import Base

class PullRequest(Base):
    __tablename__ = "pull_requests"

    id = Column(Integer, primary_key=True, index=True)
    github_id = Column(BigInteger, unique=True, index=True, nullable=False)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    
    number = Column(Integer, nullable=False)
    title = Column(String(512))
    author = Column(String(255))
    state = Column(String(50), nullable=False, index=True)  # open, closed, merged
    
    base_branch = Column(String(255))
    head_branch = Column(String(255))
    diff_url = Column(Text)
    
    files_changed = Column(Integer, default=0)
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
