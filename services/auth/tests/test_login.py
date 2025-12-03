"""Tests for login endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestFormLogin:
    """Test cases for POST /api/v1/auth/login endpoint (OAuth2 form)."""

    def test_login_success(self, client: TestClient, create_user):
        """Test successful login with valid credentials."""
        user = create_user()

        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": user["username"],
                "password": user["password"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_password(self, client: TestClient, create_user):
        """Test login fails with invalid password."""
        user = create_user()

        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": user["username"],
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect username or password"

    def test_login_invalid_username(self, client: TestClient):
        """Test login fails with non-existent username."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent",
                "password": "anypassword",
            },
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect username or password"

    def test_login_inactive_user(self, client: TestClient, create_user, db_session):
        """Test login fails for inactive user."""
        from models import User

        user = create_user()

        # Deactivate the user
        db_user = db_session.query(User).filter(User.username == user["username"]).first()
        db_user.is_active = False
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": user["username"],
                "password": user["password"],
            },
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "Inactive user"


class TestJsonLogin:
    """Test cases for POST /api/v1/auth/login/json endpoint."""

    def test_json_login_success(self, client: TestClient, create_user):
        """Test successful login with JSON body."""
        user = create_user()

        response = client.post(
            "/api/v1/auth/login/json",
            json={
                "username": user["username"],
                "password": user["password"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_json_login_invalid_password(self, client: TestClient, create_user):
        """Test JSON login fails with invalid password."""
        user = create_user()

        response = client.post(
            "/api/v1/auth/login/json",
            json={
                "username": user["username"],
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect username or password"

    def test_json_login_invalid_username(self, client: TestClient):
        """Test JSON login fails with non-existent username."""
        response = client.post(
            "/api/v1/auth/login/json",
            json={
                "username": "nonexistent",
                "password": "anypassword",
            },
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect username or password"

    def test_json_login_inactive_user(self, client: TestClient, create_user, db_session):
        """Test JSON login fails for inactive user."""
        from models import User

        user = create_user()

        # Deactivate the user
        db_user = db_session.query(User).filter(User.username == user["username"]).first()
        db_user.is_active = False
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login/json",
            json={
                "username": user["username"],
                "password": user["password"],
            },
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "Inactive user"

    def test_json_login_missing_fields(self, client: TestClient):
        """Test JSON login fails with missing fields."""
        # Missing password
        response = client.post(
            "/api/v1/auth/login/json",
            json={"username": "testuser"},
        )
        assert response.status_code == 422

        # Missing username
        response = client.post(
            "/api/v1/auth/login/json",
            json={"password": "testpassword"},
        )
        assert response.status_code == 422

