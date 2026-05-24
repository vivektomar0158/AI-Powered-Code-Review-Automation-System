from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from app.models.repository import Base

class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    payload = Column(JSONB, nullable=False)
    signature = Column(String(255))
    
    processed = Column(Boolean, default=False, index=True)
    error_message = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
