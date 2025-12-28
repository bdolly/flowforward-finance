"""Auth service event publishing.

Provides a facade for publishing auth domain events to SNS.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from shared.events.base import DomainEvent, EventMetadata
from shared.events.sns_publisher import SNSPublisher

from events.payloads import (
    LoginFailedPayload,
    TokenRefreshedPayload,
    UserLoggedInPayload,
    UserLoggedOutPayload,
    UserRegisteredPayload,
)
from events.types import AuthEventType

logger = logging.getLogger(__name__)


class AuthEventPublisher:
    """Facade for publishing auth service events.

    Provides typed methods for each auth event type, handling
    payload construction and metadata.

    Example:
        >>> publisher = AuthEventPublisher(sns_publisher, topic_arn)
        >>> await publisher.publish_user_registered(
        ...     user_id="123",
        ...     email="user@example.com",
        ...     username="johndoe",
        ... )
    """

    def __init__(
        self,
        sns_publisher: SNSPublisher,
        source: str = "auth-service",
    ) -> None:
        """Initialize the auth event publisher.

        Args:
            sns_publisher: The underlying SNS publisher
            source: Source identifier for events
        """
        self._publisher = sns_publisher
        self._source = source

    async def publish_user_registered(
        self,
        user_id: str,
        email: str,
        username: str,
        correlation_id: str | None = None,
    ) -> None:
        """Publish a user registered event.

        Args:
            user_id: The new user's ID
            email: The user's email
            username: The user's username
            correlation_id: Optional correlation ID for tracing
        """
        payload = UserRegisteredPayload(
            user_id=user_id,
            email=email,
            username=username,
            registered_at=datetime.now(timezone.utc),
        )

        event = DomainEvent(
            event_type=AuthEventType.USER_REGISTERED,
            payload=payload,
            metadata=EventMetadata(
                source=self._source,
                correlation_id=correlation_id,
            ),
        )

        await self._publisher.publish(event)
        logger.info(f"Published USER_REGISTERED event for user {user_id}")

    async def publish_user_logged_in(
        self,
        user_id: str,
        username: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Publish a user logged in event.

        Args:
            user_id: The user's ID
            username: The user's username
            ip_address: Optional client IP address
            user_agent: Optional client user agent
            correlation_id: Optional correlation ID for tracing
        """
        payload = UserLoggedInPayload(
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            logged_in_at=datetime.now(timezone.utc),
        )

        event = DomainEvent(
            event_type=AuthEventType.USER_LOGGED_IN,
            payload=payload,
            metadata=EventMetadata(
                source=self._source,
                correlation_id=correlation_id,
            ),
        )

        await self._publisher.publish(event)
        logger.debug(f"Published USER_LOGGED_IN event for user {user_id}")

    async def publish_user_logged_out(
        self,
        user_id: str,
        logout_all_devices: bool = False,
        correlation_id: str | None = None,
    ) -> None:
        """Publish a user logged out event.

        Args:
            user_id: The user's ID
            logout_all_devices: Whether user logged out from all devices
            correlation_id: Optional correlation ID for tracing
        """
        payload = UserLoggedOutPayload(
            user_id=user_id,
            logout_all_devices=logout_all_devices,
            logged_out_at=datetime.now(timezone.utc),
        )

        event_type = (
            AuthEventType.USER_LOGGED_OUT_ALL
            if logout_all_devices
            else AuthEventType.USER_LOGGED_OUT
        )

        event = DomainEvent(
            event_type=event_type,
            payload=payload,
            metadata=EventMetadata(
                source=self._source,
                correlation_id=correlation_id,
            ),
        )

        await self._publisher.publish(event)
        logger.debug(f"Published {event_type} event for user {user_id}")

    async def publish_login_failed(
        self,
        username: str,
        reason: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Publish a login failed event.

        Args:
            username: The attempted username
            reason: Reason for failure (invalid_credentials, inactive_user)
            ip_address: Optional client IP address
            user_agent: Optional client user agent
            correlation_id: Optional correlation ID for tracing
        """
        payload = LoginFailedPayload(
            username=username,
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent,
            attempted_at=datetime.now(timezone.utc),
        )

        event = DomainEvent(
            event_type=AuthEventType.LOGIN_FAILED,
            payload=payload,
            metadata=EventMetadata(
                source=self._source,
                correlation_id=correlation_id,
            ),
        )

        await self._publisher.publish(event)
        logger.debug(f"Published LOGIN_FAILED event for username {username}")

    async def publish_token_refreshed(
        self,
        user_id: str,
        old_token_id: str,
        new_token_id: str,
        correlation_id: str | None = None,
    ) -> None:
        """Publish a token refreshed event.

        Args:
            user_id: The user's ID
            old_token_id: ID of the revoked token
            new_token_id: ID of the new token
            correlation_id: Optional correlation ID for tracing
        """
        payload = TokenRefreshedPayload(
            user_id=user_id,
            old_token_id=old_token_id,
            new_token_id=new_token_id,
            refreshed_at=datetime.now(timezone.utc),
        )

        event = DomainEvent(
            event_type=AuthEventType.TOKEN_REFRESHED,
            payload=payload,
            metadata=EventMetadata(
                source=self._source,
                correlation_id=correlation_id,
            ),
        )

        await self._publisher.publish(event)
        logger.debug(f"Published TOKEN_REFRESHED event for user {user_id}")

