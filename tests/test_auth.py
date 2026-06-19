"""Auth endpoint tests.

These are the first tests that must hit the `user` table, so they deliberately
avoid requiring a live Postgres: an in-memory SQLite engine backs the schema
(created via Base.metadata.create_all), and the app's `get_db` dependency is
overridden to yield sessions bound to it. The app is driven via TestClient
*without* a `with` block so the lifespan (which would call create_all against the
real Postgres engine) never runs.
"""

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.auth.models import UserORM
from src.config import settings
from src.database import Base, get_db
from src.main import app

VALID = {"email": "alice@example.com", "password": "supersecret"}


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Only the user table: other models (e.g. VideoORM) use Postgres-only types
    # (JSONB) that SQLite can't compile.
    Base.metadata.create_all(bind=engine, tables=[UserORM.__table__])
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    # No `with` block: avoid triggering the lifespan create_all against real Postgres.
    yield TestClient(app)
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine, tables=[UserORM.__table__])


def test_register_returns_201_with_user_and_no_token(client):
    resp = client.post("/auth/register", json=VALID)

    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == VALID["email"]
    assert isinstance(body["id"], int)
    assert "created_at" in body
    assert "access_token" not in body
    assert "password_hash" not in body


def test_register_overlong_password_returns_422(client):
    # Longer than bcrypt's 72-byte limit: must fail validation, not 500 in bcrypt.
    resp = client.post(
        "/auth/register", json={"email": "bob@example.com", "password": "x" * 73}
    )

    assert resp.status_code == 422


def test_register_duplicate_email_returns_409(client):
    client.post("/auth/register", json=VALID)
    resp = client.post("/auth/register", json=VALID)

    assert resp.status_code == 409


def test_login_returns_bearer_token(client):
    client.post("/auth/register", json=VALID)
    resp = client.post("/auth/login", json=VALID)

    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert "password_hash" not in body


def test_login_bad_credentials_returns_401(client):
    client.post("/auth/register", json=VALID)
    resp = client.post(
        "/auth/login", json={"email": VALID["email"], "password": "wrongpassword"}
    )

    assert resp.status_code == 401


def test_login_unknown_email_returns_401(client):
    resp = client.post("/auth/login", json=VALID)

    assert resp.status_code == 401


def test_me_returns_user_for_valid_token(client):
    client.post("/auth/register", json=VALID)
    token = client.post("/auth/login", json=VALID).json()["access_token"]

    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == VALID["email"]
    assert "password_hash" not in body


def test_me_without_token_returns_401(client):
    resp = client.get("/auth/me")

    assert resp.status_code == 401


def test_me_with_invalid_token_returns_401(client):
    resp = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})

    assert resp.status_code == 401


def test_me_with_expired_token_returns_401(client):
    client.post("/auth/register", json=VALID)
    expired = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        settings.jwt_secret,
        algorithm=settings.jwt_alg,
    )

    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {expired}"})

    assert resp.status_code == 401
