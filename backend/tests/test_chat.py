"""Tests for the /chat endpoint (mock mode)."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_chat_returns_answer():
    """POST /chat should return an answer in mock mode."""
    resp = client.post("/chat", json={"question": "What is IS 1239?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert len(data["answer"]) > 0


def test_chat_echoes_session_id():
    """Session ID should be echoed back if supplied."""
    resp = client.post(
        "/chat",
        json={"question": "Hello", "session_id": "test-session-42"},
    )
    data = resp.json()
    assert data["session_id"] == "test-session-42"


def test_chat_has_request_id():
    """Response must include a request_id."""
    resp = client.post("/chat", json={"question": "Test"})
    data = resp.json()
    assert data["request_id"] is not None
    # Also check the response header
    assert "X-Request-ID" in resp.headers


def test_chat_rejects_empty_question():
    """Empty question string should be rejected by validation."""
    resp = client.post("/chat", json={"question": ""})
    assert resp.status_code == 422


def test_chat_mock_response_content():
    """In mock mode with context the answer should contain the mock marker or grounded response."""
    resp = client.post("/chat", json={"question": "What is IS 1239?"})
    data = resp.json()
    assert "mock" in data["answer"].lower() or "MOCK" in data["answer"] or "is 1239" in data["answer"].lower()
