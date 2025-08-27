# tests/test_ask.py

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# -------------------------------
# Mocking services for testing
# -------------------------------
@pytest.fixture(autouse=True)
def mock_services(monkeypatch):
    # Mock Gemini AI response
    async def mock_process_user_query(query):
        if "gold price" in query.lower():
            return {
                "query": query,
                "source": "gemini",
                "category": "gold",
                "answer": "Gold is a safe investment.",
                "meta": {"confidence": 0.95},
            }
        elif "crypto" in query.lower():
            return {
                "query": query,
                "source": "gemini",
                "category": "finance",
                "answer": "Crypto investments are under development.",
                "meta": {"confidence": 0.85},
            }
        else:
            return {
                "query": query,
                "source": "gemini",
                "category": "irrelevant",
                "answer": "Redirecting to finance/gold topic.",
                "meta": {"confidence": 0.1},
            }

    # Mock GoldAPI
    async def mock_get_live_gold_price():
        return 2400.0

    monkeypatch.setattr(
        "services.gemini_client.process_user_query", mock_process_user_query
    )
    monkeypatch.setattr(
        "services.gold_price.get_live_gold_price", mock_get_live_gold_price
    )


# -------------------------------
# Test Cases
# -------------------------------
def test_gold_query_with_price():
    response = client.post("/api/ask/", json={"query": "What is gold price today?"})
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "gold"
    assert "2400.0" in str(data["answer"])
    assert data["meta"]["gold_price"] == 2400.0


def test_gold_query_without_price():
    response = client.post("/api/ask/", json={"query": "Should I buy gold?"})
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "gold"
    assert "Gold is a safe investment." in data["answer"]
    assert "gold_price" not in data["meta"]


def test_finance_query():
    response = client.post("/api/ask/", json={"query": "I want to invest in crypto"})
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "finance"
    assert "under development" in data["answer"]


def test_irrelevant_query():
    response = client.post("/api/ask/", json={"query": "Golden retriever dog price?"})
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "irrelevant"
    assert "Redirecting" in data["answer"]


def test_invalid_request():
    response = client.post("/api/ask/", json={})
    assert response.status_code == 422  # validation error
