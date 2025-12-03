"""Tests for token refresh endpoint."""

import pytest
from fastapi.testclient import TestClient


class TestTokenRefresh:
    """Test cases for POST /api/v1/auth/refresh endpoint."""

    def test_refresh_token_success(self, client: TestClient, authenticated_user):
        """Test successful token refresh."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": authenticated_user["refresh_token"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        # New tokens should be different from original
        assert data["refresh_token"] != authenticated_user["refresh_token"]

    def test_refresh_token_invalid(self, client: TestClient):
        """Test refresh fails with invalid token."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid refresh token"

    def test_refresh_token_rotation(self, client: TestClient, authenticated_user):
        """Test that old refresh token is invalidated after refresh (token rotation)."""
        old_refresh_token = authenticated_user["refresh_token"]

        # First refresh should succeed
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh_token},
        )
        assert response.status_code == 200

        # Second refresh with same token should fail (token was rotated/revoked)
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh_token},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Refresh token has been revoked"

    def test_refresh_token_chain(self, client: TestClient, authenticated_user):
        """Test that new refresh tokens work correctly in a chain."""
        current_token = authenticated_user["refresh_token"]

        # Refresh multiple times
        for _ in range(3):
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": current_token},
            )
            assert response.status_code == 200
            data = response.json()
            # Update to new refresh token
            current_token = data["refresh_token"]

    def test_refresh_token_inactive_user(
        self, client: TestClient, authenticated_user, db_session
    ):
        """Test refresh fails if user becomes inactive."""
        from models import User

        # Deactivate the user
        db_user = (
            db_session.query(User)
            .filter(User.username == authenticated_user["username"])
            .first()
        )
        db_user.is_active = False
        db_session.commit()

        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": authenticated_user["refresh_token"]},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "User not found or inactive"

    def test_refresh_token_missing_field(self, client: TestClient):
        """Test refresh fails with missing refresh_token field."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={},
        )

        assert response.status_code == 422

