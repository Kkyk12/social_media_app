import os

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.db import get_db
from database import SessionLocal


# Ensure encryption key is set for tests (used by app.core.crypto_util)
os.environ.setdefault(
    "CHAT_ENCRYPTION_KEY",
    "U8eYl3k3Q5L2m7JQe9ZfB3N1X4c2H8sKxR3vZ1yT0eI=",  # any valid Fernet key
)


def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
