from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean, Numeric, BigInteger, func
from app.models.repository import Base

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, index=True)
    github_comment_id = Column(BigInteger)
    
    file_path = Column(String(1024), index=True)
    line_number = Column(Integer)
    
    agent_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    
    message = Column(Text, nullable=False)
    code_snippet = Column(Text)
    suggestion = Column(Text)
    
    accepted = Column(Boolean, index=True)
    confidence_score = Column(Numeric(3, 2))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
