from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func

from app.db.session import Base


class User(Base):
    """User model stored in PostgreSQL."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    project_id = Column(Integer, index=True, nullable=True)
    role_id = Column(Integer, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())