"""Configuration management for Accounts Service using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Get project root (two levels up from services/accounts/config.py)
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
    accounts_db_user: str = "accounts_user"
    accounts_db_password: str = "accounts_password"
    accounts_db_name: str = "accounts_db"
    accounts_db_host: str = "localhost"
    accounts_db_port: int = 5433

    # JWT Configuration (for validating tokens from auth service)
    auth_jwt_secret_key: str = "your-super-secret-key-change-in-production"
    auth_jwt_algorithm: str = "HS256"

    # Application Configuration
    app_name: str = "FlowForward Accounts Service"
    debug: bool = False

    # AWS Configuration
    aws_region: str = "us-east-1"
    aws_endpoint_url: str = "http://localhost:4566"
    aws_account_id: str = "000000000000"
    
    # Accounts service event publishing
    aws_accounts_sns_topic_name: str = "accounts-events-topic"
    aws_accounts_sqs_queue_url: str = "account-events"
    
    # Auth event subscription (SNS → SQS fan-out)
    aws_auth_sns_topic_name: str = "auth-events-topic"
    aws_accounts_auth_events_queue: str = "accounts-auth-events-queue"

    @property
    def auth_topic_arn(self) -> str:
        """Construct the auth SNS topic ARN."""
        return f"arn:aws:sns:{self.aws_region}:{self.aws_account_id}:{self.aws_auth_sns_topic_name}"

    @property
    def database_url(self) -> str:
        """Construct the database URL from individual components."""
        return (
            f"postgresql://{self.accounts_db_user}:"
            f"{self.accounts_db_password}@{self.accounts_db_host}:"
            f"{self.accounts_db_port}/{self.accounts_db_name}"
        )

    @property
    def async_database_url(self) -> str:
        """Construct the async database URL for async SQLAlchemy."""
        return (
            f"postgresql+asyncpg://{self.accounts_db_user}:"
            f"{self.accounts_db_password}@{self.accounts_db_host}:"
            f"{self.accounts_db_port}/{self.accounts_db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
