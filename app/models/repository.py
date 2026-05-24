from datetime import datetime
from sqlalchemy import Column, Integer, String, BigInteger, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB

# Need to import Base locally to avoid circular imports if needed, 
# or use a dedicated base.py. We'll use declarative_base directly or a base module.
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    github_id = Column(BigInteger, unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    full_name = Column(String(512), index=True, nullable=False)  # format: "owner/repo"
    owner = Column(String(255), nullable=False)
    
    config = Column(JSONB, default=lambda: {})
    is_active = Column(Boolean, default=True, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
