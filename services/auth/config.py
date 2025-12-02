"""Configuration management for Auth Service using Pydantic Settings."""

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


