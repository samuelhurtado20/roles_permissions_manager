from typing import List
from fastapi import APIRouter, HTTPException, status

from app.services.role_service import RoleService
from app.schemas.role import RoleCreate, RoleOut

router = APIRouter(prefix="/roles", tags=["roles"])


@router.post("/", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
def create_role(role: RoleCreate):
    """Create a new role."""
    service = RoleService()
    return service.create(role)


@router.get("/", response_model=List[RoleOut])
def list_roles(skip: int = 0, limit: int = 100):
    """List roles."""
    service = RoleService()
    return service.list(skip=skip, limit=limit)


@router.get("/{role_id}", response_model=RoleOut)
def get_role(role_id: int):
    """Get a role by ID."""
    service = RoleService()
    role = service.get(role_id=role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    return role


@router.get("/name/{role_name}", response_model=RoleOut)
def get_role_by_name(role_name: str):
    """Get a role by name."""
    service = RoleService()
    role = service.get_by_name(name=role_name)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    return role


@router.put("/{role_id}", response_model=RoleOut)
def update_role(role_id: int, role: RoleCreate):
    """Update a role."""
    service = RoleService()
    updated = service.update(role_id=role_id, role_data=role)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    return updated


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(role_id: int):
    """Delete a role."""
    service = RoleService()
    deleted = service.delete(role_id=role_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    return None