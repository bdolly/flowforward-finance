"""Event type definitions for domain events.

Defines enums and constants for all event types used across the platform.
Organized by domain/service for clarity.
"""

from enum import StrEnum


class EventType(StrEnum):
    """Base event types applicable across all domains."""

    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_HEALTH_CHECK = "system.health_check"


class AuthEventType(StrEnum):
    """Authentication service event types."""

    # User lifecycle events
    USER_REGISTERED = "auth.user.registered"
    USER_ACTIVATED = "auth.user.activated"
    USER_DEACTIVATED = "auth.user.deactivated"
    USER_DELETED = "auth.user.deleted"
    USER_UPDATED = "auth.user.updated"

    # Authentication events
    USER_LOGGED_IN = "auth.user.logged_in"
    USER_LOGGED_OUT = "auth.user.logged_out"
    USER_LOGGED_OUT_ALL = "auth.user.logged_out_all"
    LOGIN_FAILED = "auth.login.failed"

    # Token events
    TOKEN_REFRESHED = "auth.token.refreshed"
    TOKEN_REVOKED = "auth.token.revoked"

    # Password events
    PASSWORD_CHANGED = "auth.password.changed"
    PASSWORD_RESET_REQUESTED = "auth.password.reset_requested"
    PASSWORD_RESET_COMPLETED = "auth.password.reset_completed"


# Future domain event types can be added here as the platform grows
# Example:
#
# class TransactionEventType(StrEnum):
#     """Transaction service event types."""
#     TRANSACTION_CREATED = "transaction.created"
#     TRANSACTION_COMPLETED = "transaction.completed"
#     TRANSACTION_FAILED = "transaction.failed"

