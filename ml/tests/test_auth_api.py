# ml/tests/test_auth_api.py
import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from ml.persistence import db, models
from ml.api.app import app

# Create in-memory SQLite engine for auth API testing
test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
test_sessionmaker = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

# Monkeypatch AsyncSessionLocal in auth_router & analytics_router modules
import ml.api.auth_router
import ml.api.analytics_router
ml.api.auth_router.AsyncSessionLocal = test_sessionmaker
ml.api.analytics_router.AsyncSessionLocal = test_sessionmaker

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        async def _init():
            async with test_engine.begin() as conn:
                await conn.run_sync(models.Base.metadata.drop_all)
                await conn.run_sync(models.Base.metadata.create_all)
        loop.run_until_complete(_init())
    finally:
        loop.close()

def test_auth_flow():
    # 1. Register
    reg_resp = client.post("/api/auth/register", json={
        "name": "Test User",
        "email": "test@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    assert reg_resp.status_code == 200, reg_resp.text
    data = reg_resp.json()
    assert data["name"] == "Test User"
    assert data["email"] == "test@example.com"
    assert "session" in reg_resp.cookies

    # 2. Get Me
    me_resp = client.get("/api/auth/me")
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "test@example.com"

    # 3. Logout
    logout_resp = client.post("/api/auth/logout")
    assert logout_resp.status_code == 200

    # 4. Get Me after logout should fail (401)
    unauth_me = client.get("/api/auth/me")
    assert unauth_me.status_code == 401

    # 5. Login
    login_resp = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "Password123!"
    })
    assert login_resp.status_code == 200
    assert "session" in login_resp.cookies

def test_duplicate_email():
    client.post("/api/auth/register", json={
        "name": "User One",
        "email": "dup@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    dup_resp = client.post("/api/auth/register", json={
        "name": "User Two",
        "email": "dup@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    assert dup_resp.status_code == 400
    assert "already registered" in dup_resp.json()["detail"].lower()

def test_wrong_password():
    client.post("/api/auth/register", json={
        "name": "User One",
        "email": "wrongpass@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    bad_login = client.post("/api/auth/login", json={
        "email": "wrongpass@example.com",
        "password": "WrongPassword!"
    })
    assert bad_login.status_code == 400
