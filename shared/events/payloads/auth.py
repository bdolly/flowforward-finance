"""Authentication event payload definitions.

Typed payload models for auth service domain events.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserRegisteredPayload(BaseModel):
    """Payload for user registration events."""

    model_config = ConfigDict(frozen=True)

    user_id: str
    email: str
    username: str
    registered_at: datetime


class UserLoggedInPayload(BaseModel):
    """Payload for user login events."""

    model_config = ConfigDict(frozen=True)

    user_id: str
    username: str
    ip_address: str | None = None
    user_agent: str | None = None
    logged_in_at: datetime


class UserLoggedOutPayload(BaseModel):
    """Payload for user logout events."""

    model_config = ConfigDict(frozen=True)

    user_id: str
    logout_all_devices: bool = False
    logged_out_at: datetime


class LoginFailedPayload(BaseModel):
    """Payload for failed login attempt events."""

    model_config = ConfigDict(frozen=True)

    username: str
    reason: str = Field(..., description="Reason for failure: invalid_credentials, inactive_user")
    ip_address: str | None = None
    user_agent: str | None = None
    attempted_at: datetime


class TokenRefreshedPayload(BaseModel):
    """Payload for token refresh events."""

    model_config = ConfigDict(frozen=True)

    user_id: str
    old_token_id: str
    new_token_id: str
    refreshed_at: datetime


class PasswordChangedPayload(BaseModel):
    """Payload for password change events."""

    model_config = ConfigDict(frozen=True)

    user_id: str
    changed_at: datetime


class UserUpdatedPayload(BaseModel):
    """Payload for user profile update events."""

    model_config = ConfigDict(frozen=True)

    user_id: str
    updated_fields: list[str] = Field(
        ..., description="List of field names that were updated"
    )
    updated_at: datetime

