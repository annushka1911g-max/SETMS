"""
SETMS — Security: password hashing and JWT token management.
Uses Argon2id via argon2-cffi (best-practice password hashing algorithm).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from jose import JWTError, jwt

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Argon2id hasher — default parameters are OWASP-recommended
_hasher = PasswordHasher(
    time_cost=2,        # iterations
    memory_cost=65536,  # 64 MB
    parallelism=2,
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2id."""
    return _hasher.hash(password)


def verify_password(plaintext: str, hashed: str) -> bool:
    """
    Verify a plaintext password against an Argon2id hash.
    Returns False on any mismatch; never leaks timing info.
    """
    try:
        return _hasher.verify(hashed, plaintext)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(hashed: str) -> bool:
    """Return True if the hash uses outdated parameters and should be rehashed."""
    return _hasher.check_needs_rehash(hashed)


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------

def _get_jwt_settings():
    s = get_settings()
    return s.jwt_secret_key, s.jwt_algorithm


def create_access_token(
    subject: str,
    role: str,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a signed JWT access token.
    subject: user ID (UUID string)
    role: UserRole string value
    """
    settings = get_settings()
    secret, algorithm = _get_jwt_settings()

    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": expire,
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, secret, algorithm=algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT access token.
    Raises JWTError on invalid or expired tokens.
    """
    secret, algorithm = _get_jwt_settings()
    return jwt.decode(token, secret, algorithms=[algorithm])
