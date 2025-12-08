"""Configuration management for Accounts Service using Pydantic Settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
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

    @property
    def database_url(self) -> str:
        """Construct the database URL from individual components."""
        return (
            f"postgresql://{self.accounts_db_user}:{self.accounts_db_password}"
            f"@{self.accounts_db_host}:{self.accounts_db_port}/{self.accounts_db_name}"
        )

    @property
    def async_database_url(self) -> str:
        """Construct the async database URL for async SQLAlchemy."""
        return (
            f"postgresql+asyncpg://{self.accounts_db_user}:{self.accounts_db_password}"
            f"@{self.accounts_db_host}:{self.accounts_db_port}/{self.accounts_db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

