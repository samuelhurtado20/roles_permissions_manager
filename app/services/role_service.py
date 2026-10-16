from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.role import Role
from app.schemas.role import RoleCreate, RoleOut


class RoleService:
    """Service layer for role-related database operations."""

    def __init__(self):
        # Create a new database session when service is instantiated
        self.db: Session = SessionLocal()

    def __del__(self):
        # Ensure the session is closed when service is destroyed
        if hasattr(self, 'db'):
            self.db.close()

    def create(self, role_data: RoleCreate) -> RoleOut:
        """Create a new role."""
        # Check if role with same name already exists
        existing = self.db.query(Role).filter(Role.name == role_data.name).first()
        if existing:
            raise ValueError("Role name already exists")

        db_role = Role(
            name=role_data.name,
            description=role_data.description,
            is_active=role_data.is_active,
        )

        self.db.add(db_role)
        self.db.commit()
        self.db.refresh(db_role)

        return RoleOut(
            id=db_role.id,
            name=db_role.name,
            description=db_role.description,
            is_active=db_role.is_active,
            created_at=db_role.created_at,
            updated_at=db_role.updated_at,
        )

    def get(self, role_id: int) -> Optional[RoleOut]:
        """Get a role by ID."""
        db_role = self.db.query(Role).filter(Role.id == role_id).first()
        if not db_role:
            return None

        return RoleOut(
            id=db_role.id,
            name=db_role.name,
            description=db_role.description,
            is_active=db_role.is_active,
            created_at=db_role.created_at,
            updated_at=db_role.updated_at,
        )

    def get_by_name(self, name: str) -> Optional[RoleOut]:
        """Get a role by name."""
        db_role = self.db.query(Role).filter(Role.name == name).first()
        if not db_role:
            return None

        return RoleOut(
            id=db_role.id,
            name=db_role.name,
            description=db_role.description,
            is_active=db_role.is_active,
            created_at=db_role.created_at,
            updated_at=db_role.updated_at,
        )

    def list(self, skip: int = 0, limit: int = 100) -> List[RoleOut]:
        """List roles with pagination."""
        db_roles = self.db.query(Role).offset(skip).limit(limit).all()

        return [
            RoleOut(
                id=role.id,
                name=role.name,
                description=role.description,
                is_active=role.is_active,
                created_at=role.created_at,
                updated_at=role.updated_at,
            )
            for role in db_roles
        ]

    def update(self, role_id: int, role_data: RoleCreate) -> Optional[RoleOut]:
        """Update a role."""
        db_role = self.db.query(Role).filter(Role.id == role_id).first()
        if not db_role:
            return None

        # Check if name is being changed and already exists
        if role_data.name != db_role.name:
            existing = self.db.query(Role).filter(Role.name == role_data.name).first()
            if existing:
                raise ValueError("Role name already exists")

        db_role.name = role_data.name
        db_role.description = role_data.description
        db_role.is_active = role_data.is_active

        self.db.commit()
        self.db.refresh(db_role)

        return RoleOut(
            id=db_role.id,
            name=db_role.name,
            description=db_role.description,
            is_active=db_role.is_active,
            created_at=db_role.created_at,
            updated_at=db_role.updated_at,
        )

    def delete(self, role_id: int) -> bool:
        """Delete a role."""
        db_role = self.db.query(Role).filter(Role.id == role_id).first()
        if not db_role:
            return False

        self.db.delete(db_role)
        self.db.commit()
        return True