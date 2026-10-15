from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.db.session import Base


class User(Base):
    """User model stored in PostgreSQL."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())