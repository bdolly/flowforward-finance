"""Auth service event definitions.

Contains event types and payloads specific to the authentication domain.
"""

from services.auth.events.payloads import (
    LoginFailedPayload,
    PasswordChangedPayload,
    TokenRefreshedPayload,
    UserLoggedInPayload,
    UserLoggedOutPayload,
    UserRegisteredPayload,
    UserUpdatedPayload,
)
from services.auth.events.types import AuthEventType

__all__ = [
    # Event types
    "AuthEventType",
    # Payloads
    "UserRegisteredPayload",
    "UserLoggedInPayload",
    "UserLoggedOutPayload",
    "LoginFailedPayload",
    "TokenRefreshedPayload",
    "PasswordChangedPayload",
    "UserUpdatedPayload",
]

