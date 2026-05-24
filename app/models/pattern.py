from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, func
from app.models.repository import Base

class Pattern(Base):
    __tablename__ = "patterns"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    
    pattern_type = Column(String(50), nullable=False, index=True)
    description = Column(Text)
    example_code = Column(Text)
    
    vector_id = Column(String(255), unique=True, index=True)
    
    positive_votes = Column(Integer, default=0)
    negative_votes = Column(Integer, default=0)
    
    language = Column(String(50), index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
