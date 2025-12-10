"""Configuration management for Auth Service using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Get project root (two levels up from services/auth/config.py)
_PROJECT_ROOT = Path(__file__).parent.parent.parent
_ROOT_ENV_FILE = _PROJECT_ROOT / ".env"
# Service-specific .env (one level up from config.py)
_SERVICE_DIR = Path(__file__).parent
_SERVICE_ENV_FILE = _SERVICE_DIR / ".env"

# Build list of env files: root first, then service-specific
# (service overrides root)
_env_files = []
if _ROOT_ENV_FILE.exists():
    _env_files.append(str(_ROOT_ENV_FILE))
if _SERVICE_ENV_FILE.exists():
    _env_files.append(str(_SERVICE_ENV_FILE))


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=_env_files if _env_files else None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database Configuration
    auth_db_user: str = "auth_user"
    auth_db_password: str = "auth_password"
    auth_db_name: str = "auth_db"
    auth_db_host: str = "localhost"
    auth_db_port: int = 5432

    # JWT Configuration
    auth_jwt_secret_key: str = "your-super-secret-key-change-in-production"
    auth_jwt_algorithm: str = "HS256"
    auth_access_token_expire_minutes: int = 30
    auth_refresh_token_expire_days: int = 7

    # AWS Configuration
    aws_region: str = "us-east-1"
    aws_endpoint_url: str = "http://localhost:4566"
    aws_account_id: str = "000000000000"
    aws_auth_sns_topic_name: str = "auth-events-topic"
    aws_auth_sqs: str = "flowforward-auth-events"

    # Application Configuration
    app_name: str = "FlowForward Auth Service"
    debug: bool = False

    @property
    def database_url(self) -> str:
        """Construct the database URL from individual components."""
        return (
            f"postgresql://{self.auth_db_user}:{self.auth_db_password}"
            f"@{self.auth_db_host}:{self.auth_db_port}/{self.auth_db_name}"
        )

    @property
    def async_database_url(self) -> str:
        """Construct the async database URL for async SQLAlchemy."""
        return (
            f"postgresql+asyncpg://{self.auth_db_user}:{self.auth_db_password}"
            f"@{self.auth_db_host}:{self.auth_db_port}/{self.auth_db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
