"""Event publisher abstraction with Strategy pattern.

Provides a pluggable publisher interface that can be implemented
for different message brokers (Kafka, Redis, RabbitMQ, etc.).
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Callable, Coroutine

from pydantic import BaseModel

from shared.events.base import DomainEvent

logger = logging.getLogger(__name__)

PayloadT = BaseModel


class EventPublisher(ABC):
    """Abstract base class for event publishers.

    Implement this interface to create publishers for different
    message broker backends (Strategy pattern).

    Example:
        >>> publisher = KafkaPublisher(bootstrap_servers="localhost:9092")
        >>> await publisher.publish(event, topic="auth-events")
    """

    @abstractmethod
    async def publish(
        self,
        event: DomainEvent[PayloadT],
        topic: str | None = None,
    ) -> None:
        """Publish a domain event.

        Args:
            event: The domain event to publish
            topic: Optional topic/channel override (implementation specific)

        Raises:
            PublishError: If publishing fails
        """
        pass

    @abstractmethod
    async def publish_batch(
        self,
        events: list[DomainEvent[PayloadT]],
        topic: str | None = None,
    ) -> None:
        """Publish multiple events in a batch.

        Args:
            events: List of domain events to publish
            topic: Optional topic/channel override

        Raises:
            PublishError: If publishing fails
        """
        pass

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the message broker."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the message broker."""
        pass


# Type alias for event callbacks
EventCallback = Callable[[DomainEvent[Any]], Coroutine[Any, Any, None]]


class InMemoryPublisher(EventPublisher):
    """In-memory event publisher for testing and development.

    Stores events in memory and can notify registered callbacks.
    Useful for unit tests and local development without a message broker.
    """

    def __init__(self) -> None:
        """Initialize the in-memory publisher."""
        self._events: list[DomainEvent[Any]] = []
        self._callbacks: dict[str, list[EventCallback]] = defaultdict(list)
        self._connected = False

    @property
    def events(self) -> list[DomainEvent[Any]]:
        """Get all published events."""
        return self._events.copy()

    def clear(self) -> None:
        """Clear all stored events."""
        self._events.clear()

    def subscribe(self, event_type: str, callback: EventCallback) -> None:
        """Register a callback for an event type.

        Args:
            event_type: Event type to subscribe to
            callback: Async function to call when event is published
        """
        self._callbacks[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: EventCallback) -> None:
        """Unregister a callback for an event type.

        Args:
            event_type: Event type to unsubscribe from
            callback: The callback function to remove
        """
        if callback in self._callbacks[event_type]:
            self._callbacks[event_type].remove(callback)

    async def publish(
        self,
        event: DomainEvent[PayloadT],
        topic: str | None = None,
    ) -> None:
        """Publish event to in-memory store and notify callbacks.

        Args:
            event: The domain event to publish
            topic: Ignored for in-memory publisher
        """
        self._events.append(event)
        logger.debug(f"Published event: {event.event_type} (id={event.metadata.event_id})")

        # Notify all registered callbacks
        callbacks = self._callbacks.get(event.event_type, [])
        for callback in callbacks:
            try:
                await callback(event)
            except Exception as e:
                logger.error(f"Callback error for {event.event_type}: {e}")

    async def publish_batch(
        self,
        events: list[DomainEvent[PayloadT]],
        topic: str | None = None,
    ) -> None:
        """Publish multiple events.

        Args:
            events: List of domain events to publish
            topic: Ignored for in-memory publisher
        """
        await asyncio.gather(*[self.publish(event, topic) for event in events])

    async def connect(self) -> None:
        """No-op for in-memory publisher."""
        self._connected = True
        logger.debug("InMemoryPublisher connected")

    async def disconnect(self) -> None:
        """No-op for in-memory publisher."""
        self._connected = False
        logger.debug("InMemoryPublisher disconnected")

    def get_events_by_type(self, event_type: str) -> list[DomainEvent[Any]]:
        """Filter events by type.

        Args:
            event_type: The event type to filter by

        Returns:
            List of events matching the type
        """
        return [e for e in self._events if e.event_type == event_type]


class PublishError(Exception):
    """Exception raised when event publishing fails."""

    def __init__(self, message: str, event: DomainEvent[Any] | None = None) -> None:
        """Initialize publish error.

        Args:
            message: Error message
            event: The event that failed to publish
        """
        super().__init__(message)
        self.event = event
