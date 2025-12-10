"""Tests for health check endpoints."""


def test_health_check(client):
    """Test health check endpoint returns healthy status."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "accounts-service"
    assert data["version"] == "0.1.0"


def test_root_endpoint(client):
    """Test root endpoint returns service information."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "FlowForward Accounts Service"
    assert data["version"] == "0.1.0"
    assert data["docs"] == "/docs"

