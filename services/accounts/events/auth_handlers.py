"""Handlers for auth service events in the accounts service.

These handlers respond to auth events to maintain data consistency
across services (e.g., creating default accounts when users register).
"""

import logging
from typing import Any

from shared.events.base import DomainEvent
from shared.events.handlers import EventHandler

logger = logging.getLogger(__name__)


# Auth event types we're interested in
AUTH_USER_REGISTERED = "auth.user.registered"
AUTH_USER_DELETED = "auth.user.deleted"


class UserRegisteredHandler(EventHandler[Any]):
    """Handler for user registration events from auth service.

    When a new user registers, this handler can:
    - Create default account structures
    - Initialize user preferences
    - Set up any required account-related data
    """

    def can_handle(self, event_type: str) -> bool:
        """Check if this handler processes the given event type."""
        return event_type == AUTH_USER_REGISTERED

    async def handle(self, event: DomainEvent[Any]) -> None:
        """Process user registration event.

        Args:
            event: The domain event containing user registration data
        """
        payload = event.payload
        user_id = payload.get("user_id") if isinstance(payload, dict) else getattr(payload, "user_id", None)
        email = payload.get("email") if isinstance(payload, dict) else getattr(payload, "email", None)
        username = payload.get("username") if isinstance(payload, dict) else getattr(payload, "username", None)

        logger.info(
            f"Processing user registration event: "
            f"user_id={user_id}, email={email}, username={username}"
        )

        
        # TODO:
        # - Create a default checking account for the user
        # - Initialize account preferences
        # - Set up account notifications


        logger.info(f"Completed processing registration for user: {user_id}")


class UserDeletedHandler(EventHandler[Any]):
    """Handler for user deletion events from auth service.

    When a user is deleted, this handler can:
    - Archive or delete user accounts
    - Clean up associated data
    - Handle any required compliance actions
    """

    def can_handle(self, event_type: str) -> bool:
        """Check if this handler processes the given event type."""
        return event_type == AUTH_USER_DELETED

    async def handle(self, event: DomainEvent[Any]) -> None:
        """Process user deletion event.

        Args:
            event: The domain event containing user deletion data
        """
        payload = event.payload
        user_id = payload.get("user_id") if isinstance(payload, dict) else getattr(payload, "user_id", None)

        logger.info(f"Processing user deletion event: user_id={user_id}")

        # TODO:
        # - Soft-delete or archive all user accounts
        # - Generate audit records
        # - Handle data retention compliance

        logger.info(f"Completed processing deletion for user: {user_id}")


class UserLoggedInHandler(EventHandler[Any]):
    """Handler for user login events (optional - for audit/analytics)."""

    def can_handle(self, event_type: str) -> bool:
        """Check if this handler processes the given event type."""
        return event_type == "auth.user.logged_in"

    async def handle(self, event: DomainEvent[Any]) -> None:
        """Process user login event.

        Args:
            event: The domain event containing login data
        """
        payload = event.payload
        user_id = payload.get("user_id") if isinstance(payload, dict) else getattr(payload, "user_id", None)

        logger.debug(f"User logged in: {user_id}")
        # Could update last_activity timestamp, etc.

