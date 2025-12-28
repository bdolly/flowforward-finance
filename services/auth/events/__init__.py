"""Auth service event definitions.

Contains event types and payloads specific to the authentication domain.
"""

from events.payloads import (
    LoginFailedPayload,
    PasswordChangedPayload,
    TokenRefreshedPayload,
    UserLoggedInPayload,
    UserLoggedOutPayload,
    UserRegisteredPayload,
    UserUpdatedPayload,
)
from events.types import AuthEventType

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

