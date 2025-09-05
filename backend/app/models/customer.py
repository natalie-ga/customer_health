"""
Customer model for Customer Health API
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base

class Customer(Base):
    """
    Customer model representing a business customer
    """
    __tablename__ = "customers"
    
    id = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)
    segment = Column(Text, nullable=False)  # enterprise, smb, startup, mid-market
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to events
    events = relationship("Event", back_populates="customer", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.name}', segment='{self.segment}')>"
