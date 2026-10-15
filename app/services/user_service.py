from typing import List, Optional
from contextlib import contextmanager

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate, UserOut


class UserService:
    """Service layer for user-related database operations."""

    def __init__(self):
        # Create a new database session when service is instantiated
        self.db: Session = SessionLocal()

    def __del__(self):
        # Ensure the session is closed when service is destroyed
        if hasattr(self, 'db'):
            self.db.close()

    @contextmanager
    def get_db(self):
        """Context manager for database session."""
        try:
            yield self.db
        finally:
            self.db.close()

    def create(self, user_data: UserCreate) -> UserOut:
        """Create a new user."""
        # Check if user with same email already exists
        existing = self.db.query(User).filter(User.email == user_data.email).first()
        if existing:
            raise ValueError("Email already registered")

        # Hash the password
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed_password = pwd_context.hash(user_data.password)

        # Build the user model
        db_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            name=user_data.name,
            is_active=user_data.is_active,
            project_id=user_data.project_id,
            role_id=user_data.role_id,
        )

        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)

        return UserOut(
            id=db_user.id,
            email=db_user.email,
            name=db_user.name,
            is_active=db_user.is_active,
            project_id=db_user.project_id,
            role_id=db_user.role_id,
            created_at=db_user.created_at,
        )

    def get(self, user_id: int) -> Optional[UserOut]:
        """Get a user by ID."""
        db_user = self.db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return None

        return UserOut(
            id=db_user.id,
            email=db_user.email,
            name=db_user.name,
            is_active=db_user.is_active,
            project_id=db_user.project_id,
            role_id=db_user.role_id,
            created_at=db_user.created_at,
        )

    def list(self, skip: int = 0, limit: int = 100) -> List[UserOut]:
        """List users with pagination."""
        db_users = self.db.query(User).offset(skip).limit(limit).all()

        return [
            UserOut(
                id=user.id,
                email=user.email,
                name=user.name,
                is_active=user.is_active,
                project_id=user.project_id,
                role_id=user.role_id,
                created_at=user.created_at,
            )
            for user in db_users
        ]

    def update(self, user_id: int, user_data: UserCreate) -> Optional[UserOut]:
        """Update a user."""
        db_user = self.db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return None

        # Check if email is being changed and already exists
        if user_data.email != db_user.email:
            existing = self.db.query(User).filter(User.email == user_data.email).first()
            if existing:
                raise ValueError("Email already registered")

        # Update user fields
        db_user.email = user_data.email
        db_user.name = user_data.name
        db_user.is_active = user_data.is_active
        db_user.project_id = user_data.project_id
        db_user.role_id = user_data.role_id

        # Hash new password if provided
        if user_data.password:
            from passlib.context import CryptContext

            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            db_user.hashed_password = pwd_context.hash(user_data.password)

        self.db.commit()
        self.db.refresh(db_user)

        return UserOut(
            id=db_user.id,
            email=db_user.email,
            name=db_user.name,
            is_active=db_user.is_active,
            project_id=db_user.project_id,
            role_id=db_user.role_id,
            created_at=db_user.created_at,
        )

    def delete(self, user_id: int) -> bool:
        """Delete a user."""
        db_user = self.db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return False

        self.db.delete(db_user)
        self.db.commit()
        return True