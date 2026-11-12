import os
from pathlib import Path

import psycopg
import pytest

# Database usa e getta: va impostato prima di importare l'app.
TEST_DSN = os.environ.get("TEST_DATABASE_DSN", "postgresql://postgres@localhost:5432/ripostiglio_test")
os.environ["DATABASE_URL"] = TEST_DSN.replace("postgresql://", "postgresql+psycopg://", 1)
os.environ["JWT_SECRET"] = "segreto-solo-per-i-test-abbastanza-lungo"

from fastapi.testclient import TestClient  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.main import app, throttle  # noqa: E402
from app.models import User  # noqa: E402
from app.security import hash_password  # noqa: E402

ROOT = Path(__file__).parent.parent


@pytest.fixture()
def client():
    with psycopg.connect(TEST_DSN, autocommit=True) as conn:
        conn.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
        conn.execute((ROOT / "db" / "schema.sql").read_text())
    with SessionLocal() as db:
        db.add(User(username="mario", email="mario@example.com", password_hash=hash_password("password123")))
        db.commit()
    throttle._failures.clear()
    return TestClient(app)


@pytest.fixture()
def auth(client):
    token = client.post("/auth/login", json={"username": "mario", "password": "password123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
