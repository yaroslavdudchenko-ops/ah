"""
Tests for JWT authentication and role-based access control.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def raw_client(db_session):
    """Unauthenticated client — no dependency overrides."""
    from app.core.database import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Login ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_admin_ok(raw_client):
    resp = await raw_client.post(
        "/api/v1/auth/token",
        data={"username": "admin", "password": "admin123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["role"] == "admin"
    assert "access_token" in body


@pytest.mark.asyncio
async def test_login_employee_ok(raw_client):
    resp = await raw_client.post(
        "/api/v1/auth/token",
        data={"username": "employee", "password": "employee123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "employee"


@pytest.mark.asyncio
async def test_login_auditor_ok(raw_client):
    resp = await raw_client.post(
        "/api/v1/auth/token",
        data={"username": "auditor", "password": "auditor123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "auditor"


@pytest.mark.asyncio
async def test_login_bad_password(raw_client):
    resp = await raw_client.post(
        "/api/v1/auth/token",
        data={"username": "admin", "password": "wrong"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_user(raw_client):
    resp = await raw_client.post(
        "/api/v1/auth/token",
        data={"username": "hacker", "password": "admin123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 401


# ── Unauthenticated access ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_unauthenticated_list_protocols(raw_client):
    resp = await raw_client.get("/api/v1/protocols")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_unauthenticated_create_protocol(raw_client):
    resp = await raw_client.post("/api/v1/protocols", json={})
    assert resp.status_code == 401


# ── Auditor read-only ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_auditor_can_list_protocols(auditor_client):
    resp = await auditor_client.get("/api/v1/protocols")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_auditor_cannot_create_protocol(auditor_client):
    resp = await auditor_client.post("/api/v1/protocols", json={"title": "X"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_auditor_cannot_delete_protocol(raw_client):
    """Auditor JWT → DELETE → 403 (real token, no dependency override)."""
    login = await raw_client.post(
        "/api/v1/auth/token",
        data={"username": "auditor", "password": "auditor123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login.json()["access_token"]
    resp = await raw_client.delete(
        "/api/v1/protocols/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


# ── /auth/me ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_whoami(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == "admin"
    assert body["role"] == "admin"
