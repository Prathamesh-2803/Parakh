"""Tests for the /health endpoint."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_returns_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["app"] == "Parakh"


def test_health_has_version():
    resp = client.get("/health")
    data = resp.json()
    assert "version" in data
