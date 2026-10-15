from typing import List
from fastapi import APIRouter, HTTPException, status

from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate):
    """Create a new user."""
    service = UserService()
    return service.create(user)


@router.get("/", response_model=List[UserOut])
def list_users(skip: int = 0, limit: int = 100):
    """List users."""
    service = UserService()
    return service.list(skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int):
    """Get a user by ID."""
    service = UserService()
    user = service.get(user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, user: UserCreate):
    """Update a user."""
    service = UserService()
    updated = service.update(user_id=user_id, user_data=user)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return updated


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int):
    """Delete a user."""
    service = UserService()
    deleted = service.delete(user_id=user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return None