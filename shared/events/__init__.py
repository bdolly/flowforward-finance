"""Shared events library for FlowForward Finance microservices.

This module provides a common event-driven architecture foundation including:
- Base event models with Pydantic validation
- Publisher abstraction (Strategy pattern for different backends)
- Subscriber abstraction for consuming events

Domain-specific event types and payloads should be defined in their
respective services (e.g., services/auth/events/).
"""

from shared.events.base import DomainEvent, EventMetadata
from shared.events.handlers import CompositeEventHandler, EventHandler
from shared.events.publisher import EventPublisher, InMemoryPublisher, PublishError
from shared.events.subscriber import EventSubscriber, InMemorySubscriber, SubscriptionError
from shared.events.types import EventType

__all__ = [
    # Base models
    "DomainEvent",
    "EventMetadata",
    # System event types
    "EventType",
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
]
