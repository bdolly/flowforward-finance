"""Tests for user registration endpoint."""

import pytest
from fastapi.testclient import TestClient


class TestUserRegistration:
    """Test cases for POST /api/v1/auth/register endpoint."""

    def test_register_user_success(self, client: TestClient, user_data: dict[str, str]):
        """Test successful user registration."""
        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert "id" in data
        assert data["is_active"] is True
        assert data["is_superuser"] is False
        assert "created_at" in data
        assert "updated_at" in data
        # Password should not be returned
        assert "password" not in data
        assert "hashed_password" not in data

    def test_register_user_duplicate_email(self, client: TestClient, create_user):
        """Test registration fails with duplicate email."""
        # Create first user
        create_user(email="duplicate@example.com", username="user1")

        # Try to create second user with same email
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "username": "user2",
                "password": "anotherpassword123",
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered"

    def test_register_user_duplicate_username(self, client: TestClient, create_user):
        """Test registration fails with duplicate username."""
        # Create first user
        create_user(email="user1@example.com", username="duplicateuser")

        # Try to create second user with same username
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "user2@example.com",
                "username": "duplicateuser",
                "password": "anotherpassword123",
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Username already taken"

    def test_register_user_invalid_email(self, client: TestClient):
        """Test registration fails with invalid email format."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "username": "testuser",
                "password": "securepassword123",
            },
        )

        assert response.status_code == 422  # Validation error

    def test_register_user_short_password(self, client: TestClient):
        """Test registration fails with password too short."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "short",  # Less than 8 characters
            },
        )

        assert response.status_code == 422  # Validation error

    def test_register_user_short_username(self, client: TestClient):
        """Test registration fails with username too short."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "ab",  # Less than 3 characters
                "password": "securepassword123",
            },
        )

        assert response.status_code == 422  # Validation error

    def test_register_user_missing_fields(self, client: TestClient):
        """Test registration fails with missing required fields."""
        # Missing email
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "password": "securepassword123",
            },
        )
        assert response.status_code == 422

        # Missing username
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "securepassword123",
            },
        )
        assert response.status_code == 422

        # Missing password
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
            },
        )
        assert response.status_code == 422

    def test_register_multiple_users(self, client: TestClient):
        """Test registering multiple unique users succeeds."""
        users = [
            {"email": f"user{i}@example.com", "username": f"user{i}", "password": "password123"}
            for i in range(3)
        ]

        for user in users:
            response = client.post("/api/v1/auth/register", json=user)
            assert response.status_code == 201
            assert response.json()["email"] == user["email"]

