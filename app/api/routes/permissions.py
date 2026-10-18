from typing import List
from fastapi import APIRouter, HTTPException, status

from app.services.permission_service import PermissionService
from app.schemas.permission import PermissionCreate, PermissionOut

router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.post("/", response_model=PermissionOut, status_code=status.HTTP_201_CREATED)
def create_permission(permission: PermissionCreate):
    """Create a new permission."""
    service = PermissionService()
    return service.create(permission)


@router.get("/", response_model=List[PermissionOut])
def list_permissions(skip: int = 0, limit: int = 100):
    """List permissions."""
    service = PermissionService()
    return service.list(skip=skip, limit=limit)


@router.get("/{permission_id}", response_model=PermissionOut)
def get_permission(permission_id: int):
    """Get a permission by ID."""
    service = PermissionService()
    permission = service.get(permission_id=permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )
    return permission


@router.get("/name/{permission_name}", response_model=PermissionOut)
def get_permission_by_name(permission_name: str):
    """Get a permission by name."""
    service = PermissionService()
    permission = service.get_by_name(name=permission_name)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )
    return permission


@router.put("/{permission_id}", response_model=PermissionOut)
def update_permission(permission_id: int, permission: PermissionCreate):
    """Update a permission."""
    service = PermissionService()
    updated = service.update(permission_id=permission_id, permission_data=permission)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )
    return updated


@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_permission(permission_id: int):
    """Delete a permission."""
    service = PermissionService()
    deleted = service.delete(permission_id=permission_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )
    return None