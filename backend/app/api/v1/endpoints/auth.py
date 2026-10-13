"""
SETMS — Authentication API endpoints.
POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/me
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser
from app.core.security import create_access_token, hash_password, verify_password, needs_rehash
from app.db.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------

ALLOWED_SELF_REGISTRATION_ROLES = {
    UserRole.AMBULANCE_DRIVER,
    UserRole.HOSPITAL_OPERATOR,
    UserRole.VIEWER,
}


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.VIEWER

    @field_validator("role")
    @classmethod
    def no_admin_self_registration(cls, v: UserRole) -> UserRole:
        """Public registration cannot self-assign privileged roles."""
        if v not in ALLOWED_SELF_REGISTRATION_ROLES:
            raise ValueError(
                f"Role '{v}' cannot be self-assigned. Contact an administrator."
            )
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        errors = []
        if len(v) < 8:
            errors.append("at least 8 characters")
        if not any(c.isupper() for c in v):
            errors.append("one uppercase letter")
        if not any(c.isdigit() for c in v):
            errors.append("one digit")
        if errors:
            raise ValueError("Password must contain: " + ", ".join(errors))
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user_id: str
    role: str
    full_name: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    body: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Check for duplicate email (case-insensitive)
    existing = await db.execute(
        select(User).where(User.email == body.email.lower())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        email=body.email.lower(),
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
        role=body.role,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    await db.flush()

    logger.info("user_registered", user_id=user.id, role=user.role)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Obtain a JWT access token",
)
async def login(
    body: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    result = await db.execute(
        select(User).where(User.email == body.email.lower())
    )
    user = result.scalar_one_or_none()

    # Always run verify_password to prevent timing attacks
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact an administrator.",
        )

    # Rehash if Argon2 parameters have been updated
    if needs_rehash(user.hashed_password):
        user.hashed_password = hash_password(body.password)
        await db.flush()

    from app.core.config import get_settings
    settings = get_settings()

    token = create_access_token(subject=user.id, role=user.role)
    expires_in = settings.jwt_access_token_expire_minutes * 60

    logger.info(
        "user_login",
        user_id=user.id,
        role=user.role,
        ip=request.client.host if request.client else None,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
        user_id=user.id,
        role=user.role,
        full_name=user.full_name,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the currently authenticated user",
)
async def me(current_user: CurrentUser):
    return current_user
