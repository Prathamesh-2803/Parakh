"""Tests for user feedback submission and storage."""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_submit_feedback_positive():
    response = client.post(
        "/feedback",
        json={
            "request_id": "req-12345",
            "session_id": "sess-67890",
            "question": "What is the standard for helmets?",
            "answer": "IS 4151 applies to two-wheeler helmets.",
            "rating": "positive",
            "comment": "Very accurate, helped me find the right standard!",
            "language": "en"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["feedback_id"] > 0
    assert "successfully" in data["message"]


def test_submit_feedback_negative():
    response = client.post(
        "/feedback",
        json={
            "question": "IS 99999",
            "answer": "Not found in database.",
            "rating": "negative",
            "comment": "Didn't explain why standard wasn't found",
            "language": "hi"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["feedback_id"] > 0


def test_submit_feedback_invalid_rating():
    response = client.post(
        "/feedback",
        json={
            "question": "test question",
            "answer": "test answer",
            "rating": "invalid_rating"
        }
    )
    assert response.status_code == 422
