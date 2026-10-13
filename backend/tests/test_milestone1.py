"""
SETMS Backend — Test: Health, Auth, and Emergency lifecycle.
Run: cd backend && pytest tests/ -v
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text

# Use SQLite for tests
import os
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_setms.db"
os.environ["APP_ENV"] = "testing"
os.environ["JWT_SECRET_KEY"] = "test_jwt_secret_key_for_pytest"
os.environ["APP_SECRET_KEY"] = "test_app_secret_key_for_pytest"

from app.main import app
from app.db.database import create_tables, drop_tables


@pytest.fixture(scope="module", autouse=True)
async def setup_db():
    """Create tables before all tests in this module, drop after."""
    await create_tables()
    yield
    await drop_tables()
    # Clean up test DB file
    if os.path.exists("./test_setms.db"):
        os.remove("./test_setms.db")


@pytest.fixture
async def client():
    """HTTPX AsyncClient connected to the FastAPI ASGI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c


# =============================================================================
# Health endpoints
# =============================================================================

async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "setms-backend"
    assert "timestamp" in data


async def test_readiness_endpoint(client: AsyncClient):
    response = await client.get("/ready")
    # May be 200 or 503 depending on DB; we just check it responds
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "checks" in data


# =============================================================================
# Authentication
# =============================================================================

TEST_EMAIL = "testuser@setms.org"
TEST_PASSWORD = "TestPass1!"
TEST_NAME = "Test User"
_token: str = ""


async def test_register_user(client: AsyncClient):
    response = await client.post("/api/v1/auth/register", json={
        "email": TEST_EMAIL,
        "full_name": TEST_NAME,
        "password": TEST_PASSWORD,
        "role": "VIEWER",
    })
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["email"] == TEST_EMAIL
    assert data["role"] == "VIEWER"
    assert "hashed_password" not in data  # Never expose hash


async def test_register_duplicate_email(client: AsyncClient):
    response = await client.post("/api/v1/auth/register", json={
        "email": TEST_EMAIL,
        "full_name": "Another User",
        "password": TEST_PASSWORD,
        "role": "VIEWER",
    })
    assert response.status_code == 409


async def test_register_admin_role_denied(client: AsyncClient):
    """Public registration must not allow ADMIN self-assignment."""
    response = await client.post("/api/v1/auth/register", json={
        "email": "hacker@evil.com",
        "full_name": "Hacker",
        "password": TEST_PASSWORD,
        "role": "ADMIN",  # Must be rejected
    })
    assert response.status_code == 422, "ADMIN self-registration must be rejected"


async def test_register_traffic_operator_denied(client: AsyncClient):
    """TRAFFIC_OPERATOR also cannot be self-assigned."""
    response = await client.post("/api/v1/auth/register", json={
        "email": "badactor@evil.com",
        "full_name": "Bad Actor",
        "password": TEST_PASSWORD,
        "role": "TRAFFIC_OPERATOR",
    })
    assert response.status_code == 422


async def test_login_success(client: AsyncClient):
    global _token
    response = await client.post("/api/v1/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
    })
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "hashed_password" not in str(data)  # Never expose hash in token response
    _token = data["access_token"]


async def test_login_wrong_password(client: AsyncClient):
    response = await client.post("/api/v1/auth/login", json={
        "email": TEST_EMAIL,
        "password": "WrongPass999!",
    })
    assert response.status_code == 401


async def test_login_unknown_email(client: AsyncClient):
    response = await client.post("/api/v1/auth/login", json={
        "email": "nonexistent@setms.org",
        "password": TEST_PASSWORD,
    })
    assert response.status_code == 401


async def test_me_authenticated(client: AsyncClient):
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == TEST_EMAIL
    assert "hashed_password" not in data


async def test_me_no_token(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 403


async def test_me_invalid_token(client: AsyncClient):
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert response.status_code == 401


# =============================================================================
# Dashboard requires auth
# =============================================================================

async def test_dashboard_requires_auth(client: AsyncClient):
    response = await client.get("/api/v1/dashboard/summary")
    assert response.status_code == 403


async def test_dashboard_summary_authenticated(client: AsyncClient):
    response = await client.get(
        "/api/v1/dashboard/summary",
        headers={"Authorization": f"Bearer {_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "ambulances" in data
    assert "emergencies" in data
    assert "corridors" in data
    assert "signals" in data
    assert "hospitals" in data
    assert "analytics" in data


# =============================================================================
# Ambulances
# =============================================================================

async def test_list_ambulances(client: AsyncClient):
    response = await client.get(
        "/api/v1/ambulances",
        headers={"Authorization": f"Bearer {_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


async def test_create_ambulance_requires_admin(client: AsyncClient):
    """Ambulance creation requires ADMIN role; VIEWER should get 403."""
    response = await client.post(
        "/api/v1/ambulances",
        json={"registration_number": "MH99-TEST-001", "call_sign": "TEST-1"},
        headers={"Authorization": f"Bearer {_token}"},
    )
    assert response.status_code == 403


# =============================================================================
# Hospitals
# =============================================================================

async def test_list_hospitals(client: AsyncClient):
    response = await client.get(
        "/api/v1/hospitals",
        headers={"Authorization": f"Bearer {_token}"},
    )
    assert response.status_code == 200


# =============================================================================
# Analytics
# =============================================================================

async def test_analytics_summary(client: AsyncClient):
    response = await client.get(
        "/api/v1/analytics/summary",
        headers={"Authorization": f"Bearer {_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    # Verify time-saved metric is properly labeled
    assert "estimated_time_saved_minutes" in data
    ts = data["estimated_time_saved_minutes"]
    assert ts["label"] == "simulated_estimate"
    assert "definition" in ts


# =============================================================================
# Internal data exposure checks
# =============================================================================

async def test_no_password_hash_in_register_response(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "secure_check@setms.org",
        "full_name": "Secure Check",
        "password": "SecurePass1!",
        "role": "VIEWER",
    })
    body = resp.text
    assert "hashed_password" not in body
    assert "$argon2" not in body
    assert "argon" not in body.lower()
