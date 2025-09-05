"""
Event model for Customer Health API
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base

class Event(Base):
    """
    Event model representing customer activity events
    """
    __tablename__ = "events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(Text, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(Text, nullable=False)  # login, feature_usage, support_ticket, etc.
    ts = Column(DateTime(timezone=True), server_default=func.now())
    event_metadata = Column(JSONB)  # Additional event data
    
    # Relationship to customer
    customer = relationship("Customer", back_populates="events")
    
    def __repr__(self):
        return f"<Event(id={self.id}, customer_id={self.customer_id}, type='{self.event_type}')>"
