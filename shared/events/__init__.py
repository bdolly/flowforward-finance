"""Shared events library for FlowForward Finance microservices.

This module provides a common event-driven architecture foundation including:
- Base event models with Pydantic validation
- Event type definitions for domain events
- Publisher abstraction (Strategy pattern for different backends)
- Subscriber abstraction for consuming events
- Event payloads for typed domain events
"""

from shared.events.base import DomainEvent, EventMetadata
from shared.events.handlers import CompositeEventHandler, EventHandler
from shared.events.payloads.auth import (
    LoginFailedPayload,
    PasswordChangedPayload,
    TokenRefreshedPayload,
    UserLoggedInPayload,
    UserLoggedOutPayload,
    UserRegisteredPayload,
    UserUpdatedPayload,
)
from shared.events.publisher import EventPublisher, InMemoryPublisher, PublishError
from shared.events.subscriber import EventSubscriber, InMemorySubscriber, SubscriptionError
from shared.events.types import AuthEventType, EventType

__all__ = [
    # Base models
    "DomainEvent",
    "EventMetadata",
    # Event types
    "EventType",
    "AuthEventType",
    # Publisher
    "EventPublisher",
    "InMemoryPublisher",
    "PublishError",
    # Subscriber
    "EventSubscriber",
    "InMemorySubscriber",
    "SubscriptionError",
    # Handlers
    "EventHandler",
    "CompositeEventHandler",
    # Auth payloads
    "UserRegisteredPayload",
    "UserLoggedInPayload",
    "UserLoggedOutPayload",
    "LoginFailedPayload",
    "TokenRefreshedPayload",
    "PasswordChangedPayload",
    "UserUpdatedPayload",
]

