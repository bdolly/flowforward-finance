"""Event payload definitions for domain events.

Provides typed payload models for different event types.
"""

from shared.events.payloads.auth import (
    LoginFailedPayload,
    PasswordChangedPayload,
    TokenRefreshedPayload,
    UserLoggedInPayload,
    UserLoggedOutPayload,
    UserRegisteredPayload,
    UserUpdatedPayload,
)

__all__ = [
    # Auth payloads
    "UserRegisteredPayload",
    "UserLoggedInPayload",
    "UserLoggedOutPayload",
    "LoginFailedPayload",
    "TokenRefreshedPayload",
    "PasswordChangedPayload",
    "UserUpdatedPayload",
]

