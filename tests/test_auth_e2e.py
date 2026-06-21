"""End-to-end test of the auth journey through the FastAPI HTTP layer.

This drives the real app (router -> service -> security -> ORM) over HTTP via
TestClient as one continuous flow: a brand-new user registers, logs in with the
returned credentials, uses the issued bearer token to read their own profile,
and is rejected once that token is tampered with. Only the true external edge —
Postgres — is swapped for an in-memory SQLite engine (the `user` table is the
only model that compiles on SQLite); password hashing, JWT minting, and token
verification all run for real.

`tests/test_auth.py` covers each endpoint's success/failure cases in isolation;
this file proves the pieces compose into a working login flow.
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

CREDENTIALS = {"email": "journey@example.com", "password": "supersecret"}


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


def test_register_login_me_full_journey(client):
    # 1. Register: a fresh user is created and echoed back without any secret.
    register = client.post("/auth/register", json=CREDENTIALS)
    assert register.status_code == 201
    created = register.json()
    assert created["email"] == CREDENTIALS["email"]
    assert isinstance(created["id"], int)
    assert "password_hash" not in created
    assert "access_token" not in created

    # 2. Log in with the same credentials: a real bearer token is issued.
    login = client.post("/auth/login", json=CREDENTIALS)
    assert login.status_code == 200
    token = login.json()["access_token"]
    assert login.json()["token_type"] == "bearer"
    # The token genuinely carries this user's id as `sub`.
    decoded = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
    assert decoded["sub"] == str(created["id"])

    # 3. Use the token to read the current user: same identity comes back.
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    profile = me.json()
    assert profile["id"] == created["id"]
    assert profile["email"] == CREDENTIALS["email"]
    assert "password_hash" not in profile

    # 4. A tampered token from the same flow is rejected.
    tampered = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {token}corrupt"}
    )
    assert tampered.status_code == 401


def test_me_rejects_expired_token_from_real_login(client):
    register = client.post("/auth/register", json=CREDENTIALS)
    user_id = register.json()["id"]

    # An otherwise-valid token for this real user, but already expired.
    expired = jwt.encode(
        {"sub": str(user_id), "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        settings.jwt_secret,
        algorithm=settings.jwt_alg,
    )

    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert resp.status_code == 401
