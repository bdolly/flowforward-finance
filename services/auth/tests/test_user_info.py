"""Tests for user info endpoint."""

import pytest
from fastapi.testclient import TestClient


class TestUserInfo:
    """Test cases for GET /api/v1/auth/me endpoint."""

    def test_get_current_user_success(
        self, client: TestClient, authenticated_user, auth_headers
    ):
        """Test getting current user info with valid token."""
        response = client.get(
            "/api/v1/auth/me",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == authenticated_user["email"]
        assert data["username"] == authenticated_user["username"]
        assert data["id"] == authenticated_user["id"]
        assert data["is_active"] is True
        assert data["is_superuser"] is False
        assert "created_at" in data
        assert "updated_at" in data
        # Password should not be returned
        assert "password" not in data
        assert "hashed_password" not in data

    def test_get_current_user_no_token(self, client: TestClient):
        """Test getting user info without token fails."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting user info with invalid token fails."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401

    def test_get_current_user_expired_token(
        self, client: TestClient, create_user, test_settings
    ):
        """Test getting user info with expired token fails."""
        from datetime import datetime, timedelta, timezone

        from jose import jwt

        user = create_user()

        # Create an expired token
        expire = datetime.now(timezone.utc) - timedelta(minutes=1)
        to_encode = {
            "sub": user["id"],
            "exp": expire,
            "type": "access",
            "iat": datetime.now(timezone.utc) - timedelta(minutes=30),
        }
        expired_token = jwt.encode(
            to_encode,
            test_settings.auth_jwt_secret_key,
            algorithm=test_settings.auth_jwt_algorithm,
        )

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )

        assert response.status_code == 401

    def test_get_current_user_with_refresh_token(
        self, client: TestClient, authenticated_user
    ):
        """Test getting user info with refresh token fails."""
        # Using refresh token instead of access token should fail
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {authenticated_user['refresh_token']}"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid token type"

    def test_get_current_user_inactive_user(
        self, client: TestClient, authenticated_user, auth_headers, db_session
    ):
        """Test getting user info for inactive user fails."""
        from models import User

        # Deactivate the user after getting the token
        db_user = (
            db_session.query(User)
            .filter(User.username == authenticated_user["username"])
            .first()
        )
        db_user.is_active = False
        db_session.commit()

        response = client.get(
            "/api/v1/auth/me",
            headers=auth_headers,
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "Inactive user"

    def test_get_current_user_deleted_user(
        self, client: TestClient, authenticated_user, auth_headers, db_session
    ):
        """Test getting user info for deleted user fails."""
        from models import User

        # Delete the user after getting the token
        db_user = (
            db_session.query(User)
            .filter(User.username == authenticated_user["username"])
            .first()
        )
        db_session.delete(db_user)
        db_session.commit()

        response = client.get(
            "/api/v1/auth/me",
            headers=auth_headers,
        )

        assert response.status_code == 401

