"""Tests for logout endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestLogout:
    """Test cases for POST /api/v1/auth/logout endpoint."""

    def test_logout_success(self, client: TestClient, authenticated_user, auth_headers):
        """Test successful logout revokes refresh token."""
        response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": authenticated_user["refresh_token"]},
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"

        # Verify refresh token is revoked
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": authenticated_user["refresh_token"]},
        )
        assert response.status_code == 401

    def test_logout_without_auth(self, client: TestClient, authenticated_user):
        """Test logout requires authentication."""
        response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": authenticated_user["refresh_token"]},
        )

        assert response.status_code == 401

    def test_logout_invalid_token(self, client: TestClient, auth_headers):
        """Test logout with invalid refresh token still returns success."""
        # Logout with non-existent token should still return success (idempotent)
        response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": "invalid-refresh-token"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"

    def test_logout_other_users_token(
        self, client: TestClient, create_user, authenticated_user, auth_headers
    ):
        """Test that user cannot logout with another user's refresh token."""
        # Create and login as another user
        other_user = create_user(
            email="other@example.com",
            username="otheruser",
            password="otherpassword123",
        )
        other_response = client.post(
            "/api/v1/auth/login",
            data={"username": other_user["username"], "password": other_user["password"]},
        )
        other_tokens = other_response.json()

        # Try to logout with other user's token using first user's auth
        response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": other_tokens["refresh_token"]},
            headers=auth_headers,
        )

        # Should succeed but not actually revoke the other user's token
        assert response.status_code == 200

        # Other user's token should still work
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": other_tokens["refresh_token"]},
        )
        assert response.status_code == 200


class TestLogoutAll:
    """Test cases for POST /api/v1/auth/logout/all endpoint."""

    def test_logout_all_success(self, client: TestClient, authenticated_user, auth_headers):
        """Test logout all revokes all refresh tokens for user."""
        # Login again to create another refresh token
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": authenticated_user["username"],
                "password": authenticated_user["password"],
            },
        )
        second_tokens = response.json()

        # Logout all
        response = client.post(
            "/api/v1/auth/logout/all",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out from all devices"

        # Both refresh tokens should be revoked
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": authenticated_user["refresh_token"]},
        )
        assert response.status_code == 401

        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": second_tokens["refresh_token"]},
        )
        assert response.status_code == 401

    def test_logout_all_without_auth(self, client: TestClient):
        """Test logout all requires authentication."""
        response = client.post("/api/v1/auth/logout/all")

        assert response.status_code == 401

    def test_logout_all_does_not_affect_other_users(
        self, client: TestClient, create_user, authenticated_user, auth_headers
    ):
        """Test logout all only affects the current user."""
        # Create and login as another user
        other_user = create_user(
            email="other@example.com",
            username="otheruser",
            password="otherpassword123",
        )
        other_response = client.post(
            "/api/v1/auth/login",
            data={"username": other_user["username"], "password": other_user["password"]},
        )
        other_tokens = other_response.json()

        # Logout all for first user
        response = client.post(
            "/api/v1/auth/logout/all",
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Other user's token should still work
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": other_tokens["refresh_token"]},
        )
        assert response.status_code == 200

