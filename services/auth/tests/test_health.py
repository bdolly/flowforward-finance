"""Tests for health and root endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Test cases for health check endpoints."""

    def test_health_check(self, client: TestClient):
        """Test health check returns healthy status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "auth-service"
        assert data["version"] == "0.1.0"

    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint returns service info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "FlowForward Auth Service"
        assert data["version"] == "0.1.0"
        assert data["docs"] == "/docs"

