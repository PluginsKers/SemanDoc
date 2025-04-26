from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from lib.db.database import Base


def generate_api_key():
    """Generate API Key"""
    return str(uuid.uuid4())


class APIKey(Base):
    """API Key Model"""

    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, index=True, default=generate_api_key)
    name = Column(String, index=True)
    key = Column(String, unique=True, index=True, default=generate_api_key)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    user_id = Column(String, nullable=True)

    def __repr__(self):
        return f"<APIKey(name={self.name}, is_active={self.is_active})>"
