"""Authentication and authorization utilities."""

import logging
import time
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from app.core.config import settings
from app.models.user import User
from app.models.role import Role

logger = logging.getLogger("auth")


def create_access_token(
    data: dict,
    expires_delta: Optional[int] = None,
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = time.time() + expires_delta
    else:
        expire = time.time() + settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError as exc:
        logger.warning("JWT decode error: %s", exc)
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db_session=None,
) -> User:
    """Extract and validate the current user from JWT token.

    This dependency extracts the JWT token from the Authorization header,
    decodes it, and retrieves the corresponding user from the database.
    For initial development, a test user is returned when no real auth is configured.
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: int = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    # In a real app, fetch user from DB
    # For now, create a test user with a role based on the token
    role_name = payload.get("role", "STANDARD")
    role = Role(id=1, name=role_name, description=f"Role: {role_name}")

    return User(
        id=user_id,
        name=payload.get("name", "Test User"),
        email=payload.get("email", "test@example.com"),
        hashed_password="",  # Not used in auth check
        is_active=True,
        project_id=payload.get("project_id"),
        role=role,
    )


def check_role(user: User, allowed_roles: list) -> bool:
    """Check if the user has one of the allowed roles.

    Args:
        user: The user to check
        allowed_roles: List of role names that are allowed

    Returns:
        True if user has one of the allowed roles, False otherwise
    """
    if user.role is None:
        return False
    return user.role.name in allowed_roles


def check_roles(
    user: User, required_roles: list[str],
) -> bool:
    """Check if the user has all of the required roles.

    This is useful for AND logic (user must have ALL specified roles).

    Args:
        user: The user to check
        required_roles: List of role names that must all be present

    Returns:
        True if user has all of the required roles, False otherwise
    """
    if user.role is None:
        return False
    # Handle comma-separated role names
    user_roles = user.role.name.split(",")
    return all(r.strip() in user_roles for r in required_roles)


def check_admin(user: User) -> bool:
    """Check if the user has Administrator role."""
    return check_roles(user, ["ADMIN"])