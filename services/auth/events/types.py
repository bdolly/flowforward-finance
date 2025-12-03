"""Authentication service event type definitions."""

from enum import StrEnum


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

