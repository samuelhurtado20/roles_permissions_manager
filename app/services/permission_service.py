from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.permission import Permission
from app.schemas.permission import PermissionCreate, PermissionOut


class PermissionService:
    """Service layer for permission-related database operations."""

    def __init__(self):
        # Create a new database session when service is instantiated
        self.db: Session = SessionLocal()

    def __del__(self):
        # Ensure the session is closed when service is destroyed
        if hasattr(self, 'db'):
            self.db.close()

    def create(self, permission_data: PermissionCreate) -> PermissionOut:
        """Create a new permission."""
        # Check if permission with same name already exists
        existing = self.db.query(Permission).filter(Permission.name == permission_data.name).first()
        if existing:
            raise ValueError("Permission name already exists")

        db_permission = Permission(
            name=permission_data.name,
            description=permission_data.description,
            category=permission_data.category,
            is_active=permission_data.is_active,
        )

        self.db.add(db_permission)
        self.db.commit()
        self.db.refresh(db_permission)

        return PermissionOut(
            id=db_permission.id,
            name=db_permission.name,
            description=db_permission.description,
            category=db_permission.category,
            is_active=db_permission.is_active,
            created_at=db_permission.created_at,
            updated_at=db_permission.updated_at,
        )

    def get(self, permission_id: int) -> Optional[PermissionOut]:
        """Get a permission by ID."""
        db_permission = self.db.query(Permission).filter(Permission.id == permission_id).first()
        if not db_permission:
            return None

        return PermissionOut(
            id=db_permission.id,
            name=db_permission.name,
            description=db_permission.description,
            category=db_permission.category,
            is_active=db_permission.is_active,
            created_at=db_permission.created_at,
            updated_at=db_permission.updated_at,
        )

    def get_by_name(self, name: str) -> Optional[PermissionOut]:
        """Get a permission by name."""
        db_permission = self.db.query(Permission).filter(Permission.name == name).first()
        if not db_permission:
            return None

        return PermissionOut(
            id=db_permission.id,
            name=db_permission.name,
            description=db_permission.description,
            category=db_permission.category,
            is_active=db_permission.is_active,
            created_at=db_permission.created_at,
            updated_at=db_permission.updated_at,
        )

    def list(self, skip: int = 0, limit: int = 100) -> List[PermissionOut]:
        """List permissions with pagination."""
        db_permissions = self.db.query(Permission).offset(skip).limit(limit).all()

        return [
            PermissionOut(
                id=permission.id,
                name=permission.name,
                description=permission.description,
                category=permission.category,
                is_active=permission.is_active,
                created_at=permission.created_at,
                updated_at=permission.updated_at,
            )
            for permission in db_permissions
        ]

    def update(self, permission_id: int, permission_data: PermissionCreate) -> Optional[PermissionOut]:
        """Update a permission."""
        db_permission = self.db.query(Permission).filter(Permission.id == permission_id).first()
        if not db_permission:
            return None

        # Check if name is being changed and already exists
        if permission_data.name != db_permission.name:
            existing = self.db.query(Permission).filter(Permission.name == permission_data.name).first()
            if existing:
                raise ValueError("Permission name already exists")

        db_permission.name = permission_data.name
        db_permission.description = permission_data.description
        db_permission.category = permission_data.category
        db_permission.is_active = permission_data.is_active

        self.db.commit()
        self.db.refresh(db_permission)

        return PermissionOut(
            id=db_permission.id,
            name=db_permission.name,
            description=db_permission.description,
            category=db_permission.category,
            is_active=db_permission.is_active,
            created_at=db_permission.created_at,
            updated_at=db_permission.updated_at,
        )

    def delete(self, permission_id: int) -> bool:
        """Delete a permission."""
        db_permission = self.db.query(Permission).filter(Permission.id == permission_id).first()
        if not db_permission:
            return False

        self.db.delete(db_permission)
        self.db.commit()
        return True
