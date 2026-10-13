"""
SETMS — FastAPI dependency for current authenticated user.
Reads the Authorization: Bearer token, decodes it, and loads the user from DB.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.database import get_db
from app.models.enums import UserRole
from app.models.user import User

_bearer = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Decode the JWT and load the User from the database."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str = payload.get("sub", "")
        if not user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive"
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: UserRole):
    """
    Factory that returns a FastAPI dependency enforcing role-based access.
    Usage: Depends(require_roles(UserRole.ADMIN, UserRole.TRAFFIC_OPERATOR))
    """
    async def _check(current_user: CurrentUser) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' is not authorized for this operation.",
            )
        return current_user

    return _check


# Convenience type aliases for common role combinations
AdminUser = Annotated[User, Depends(require_roles(UserRole.ADMIN))]
OperatorUser = Annotated[
    User,
    Depends(require_roles(UserRole.ADMIN, UserRole.TRAFFIC_OPERATOR)),
]
