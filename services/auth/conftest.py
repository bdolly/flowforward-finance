"""
Pytest configuration and fixtures for Auth Service tests.

Uses a separate database schema (test_auth) for test isolation.
Each test function gets a fresh database transaction that is rolled back.
"""

import importlib.util
import os
import sys
from collections.abc import Generator
from pathlib import Path
from typing import Any

# Set test environment variables BEFORE importing modules that use settings
# These can be overridden by actual environment variables
_test_env_defaults = {
    "AUTH_DB_USER": "auth_user",
    "AUTH_DB_PASSWORD": "your-secure-db-password-here",
    "AUTH_DB_NAME": "auth_db",
    "AUTH_DB_HOST": "localhost",
    "AUTH_DB_PORT": "5432",
    "AUTH_JWT_SECRET_KEY": "test-secret-key-not-for-production",
    "AUTH_JWT_ALGORITHM": "HS256",
    "AUTH_ACCESS_TOKEN_EXPIRE_MINUTES": "30",
    "AUTH_REFRESH_TOKEN_EXPIRE_DAYS": "7",
    "DEBUG": "false",
}

# Set defaults only if not already set
for key, value in _test_env_defaults.items():
    if key not in os.environ:
        os.environ[key] = value

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Get the service directory
_service_dir = Path(__file__).parent


def _import_module(name: str, module_file: str):
    """Import a module from the service directory by file path."""
    module_path = _service_dir / module_file
    spec = importlib.util.spec_from_file_location(name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# Import modules with explicit file paths to avoid __init__.py shadowing
config_module = _import_module("config", "config.py")
database_module = _import_module("database", "database.py")
models_module = _import_module("models", "models.py")
schemas_module = _import_module("schemas", "schemas.py")
dependencies_module = _import_module("dependencies", "dependencies.py")
auth_module = _import_module("auth", "auth.py")
main_module = _import_module("main", "main.py")

# Import what we need
Settings = config_module.Settings
get_settings = config_module.get_settings
Base = database_module.Base
get_db = database_module.get_db
app = main_module.app


class TestSettings(Settings):
    """Test-specific settings with separate schema."""

    # Override database settings for tests
    auth_db_name: str = "auth_db"
    _test_schema: str = "test_auth"

    @property
    def database_url(self) -> str:
        """Construct the database URL for tests."""
        return (
            f"postgresql://{self.auth_db_user}:{self.auth_db_password}"
            f"@{self.auth_db_host}:{self.auth_db_port}/{self.auth_db_name}"
        )


def get_test_settings() -> TestSettings:
    """Get test settings instance."""
    return TestSettings()


# Test schema name
TEST_SCHEMA = "test_auth"


@pytest.fixture(scope="session")
def test_settings() -> TestSettings:
    """Provide test settings for the entire test session."""
    return get_test_settings()


@pytest.fixture(scope="session")
def test_engine(test_settings: TestSettings):
    """
    Create a test database engine with a separate schema.
    
    This fixture creates the test schema once per test session.
    """
    engine = create_engine(
        test_settings.database_url,
        pool_pre_ping=True,
        echo=False,
    )

    # Create the test schema if it doesn't exist
    with engine.connect() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE"))
        conn.execute(text(f"CREATE SCHEMA {TEST_SCHEMA}"))
        conn.commit()

    # Set the search path to use the test schema
    @pytest.fixture(autouse=True)
    def set_schema():
        with engine.connect() as conn:
            conn.execute(text(f"SET search_path TO {TEST_SCHEMA}"))
            conn.commit()

    # Create all tables in the test schema
    with engine.connect() as conn:
        conn.execute(text(f"SET search_path TO {TEST_SCHEMA}"))
        conn.commit()

    # Update engine to use test schema by default
    engine = create_engine(
        test_settings.database_url,
        pool_pre_ping=True,
        echo=False,
        connect_args={"options": f"-c search_path={TEST_SCHEMA}"},
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Cleanup: Drop the test schema after all tests
    cleanup_engine = create_engine(
        test_settings.database_url,
        pool_pre_ping=True,
    )
    with cleanup_engine.connect() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE"))
        conn.commit()
    cleanup_engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, Any, None]:
    """
    Provide an isolated database session for each test.
    
    Each test gets its own transaction that is rolled back after the test,
    ensuring complete isolation between tests.
    """
    connection = test_engine.connect()
    transaction = connection.begin()

    # Create a session bound to this connection
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=connection,
    )
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db_session: Session, test_settings: TestSettings) -> Generator[TestClient, Any, None]:
    """
    Provide a FastAPI test client with overridden dependencies.
    
    The database session and settings are overridden to use test versions.
    """
    from config import get_settings

    def override_get_db() -> Generator[Session, Any, None]:
        yield db_session

    def override_get_settings() -> Settings:
        return test_settings

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = override_get_settings

    with TestClient(app) as test_client:
        yield test_client

    # Clear overrides after test
    app.dependency_overrides.clear()


# --- Test Data Factories ---


@pytest.fixture
def user_data() -> dict[str, str]:
    """Provide default user registration data."""
    return {
        "email": "testuser@example.com",
        "username": "testuser",
        "password": "securepassword123",
    }


@pytest.fixture
def create_user(client: TestClient, user_data: dict[str, str]):
    """
    Factory fixture to create a user and return their data.
    
    Returns a function that creates users with optional custom data.
    """
    def _create_user(
        email: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ) -> dict[str, Any]:
        data = {
            "email": email or user_data["email"],
            "username": username or user_data["username"],
            "password": password or user_data["password"],
        }
        response = client.post("/api/v1/auth/register", json=data)
        assert response.status_code == 201
        return {**response.json(), "password": data["password"]}

    return _create_user


@pytest.fixture
def authenticated_user(create_user, client: TestClient) -> dict[str, Any]:
    """
    Create a user and authenticate them, returning user data with tokens.
    """
    user = create_user()
    
    # Login to get tokens
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": user["username"],
            "password": user["password"],
        },
    )
    assert response.status_code == 200
    tokens = response.json()
    
    return {
        **user,
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
    }


@pytest.fixture
def auth_headers(authenticated_user: dict[str, Any]) -> dict[str, str]:
    """Provide authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {authenticated_user['access_token']}"}

