### tests/test_auth.py
import pytest
from fastapi.testclient import TestClient
from app import create_app
from database.db import engine
from sqlmodel import SQLModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = TestClient(create_app())


@pytest.fixture(name="client")
def client_fixture(tmp_path):
    # Ensure fresh DB by dropping and recreating tables
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    app = create_app()
    return TestClient(app)


def test_signup_and_login(client):
    logger.info("Running test_signup_and_login...")
    # Signup
    resp = client.post(
        "/auth/signup",
        json={
            "name": "Test User",
            "email": "assignment@example.com",
            "password": "strongpass",
        },
    )
    logger.debug(f"Signup response: {resp.status_code}, {resp.json()}")
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data


# Duplicate signup
resp2 = client.post(
    "/auth/signup",
    json={
        "name": "Test User 2",
        "email": "assignment@example.com",
        "password": "strongpass",
    },
)
logger.debug(f"Duplicate signup response: {resp2.status_code}, {resp2.json()}")
assert resp2.status_code == 400


# Login success
resp3 = client.post(
    "/auth/login", json={"email": "assignment@example.com", "password": "strongpass"}
)
logger.debug(f"Login success response: {resp3.status_code}, {resp3.json()}")
assert resp3.status_code == 200
assert "access_token" in resp3.json()


# Login failure
resp4 = client.post(
    "/auth/login", json={"email": "assignment@example.com", "password": "wrongpass"}
)
logger.debug(f"Login failure response: {resp4.status_code}, {resp4.json()}")
assert resp4.status_code == 401
