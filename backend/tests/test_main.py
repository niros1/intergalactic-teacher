"""Test main application."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome to Intergalactic Teacher API" in response.json()["message"]


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code in [200, 503]  # 503 if services not available
    assert "status" in response.json()


def test_openapi_json():
    """Test OpenAPI JSON generation."""
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"


def test_docs_endpoint():
    """Test API documentation endpoint."""
    response = client.get("/api/v1/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]