"""Event subscriber abstraction.

Provides a pluggable subscriber interface for consuming events
from different message brokers.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any

from pydantic import BaseModel

from shared.events.base import DomainEvent
from shared.events.handlers import EventHandler

logger = logging.getLogger(__name__)

PayloadT = BaseModel


class EventSubscriber(ABC):
    """Abstract base class for event subscribers.

    Implement this interface to create subscribers for different
    message broker backends (Strategy pattern).

    Example:
        >>> subscriber = KafkaSubscriber(bootstrap_servers="localhost:9092")
        >>> subscriber.register_handler(UserRegisteredHandler())
        >>> await subscriber.start(topics=["auth-events"])
    """

    def __init__(self) -> None:
        """Initialize with empty handler registry."""
        self._handlers: list[EventHandler[Any]] = []

    def register_handler(self, handler: EventHandler[Any]) -> None:
        """Register an event handler.

        Args:
            handler: The event handler to register
        """
        self._handlers.append(handler)
        logger.debug(f"Registered handler: {handler.__class__.__name__}")

    def unregister_handler(self, handler: EventHandler[Any]) -> None:
        """Unregister an event handler.

        Args:
            handler: The event handler to remove
        """
        self._handlers.remove(handler)
        logger.debug(f"Unregistered handler: {handler.__class__.__name__}")

    async def dispatch(self, event: DomainEvent[Any]) -> None:
        """Dispatch event to all registered handlers that can handle it.

        Args:
            event: The domain event to dispatch
        """
        for handler in self._handlers:
            if handler.can_handle(event.event_type):
                try:
                    await handler.handle(event)
                except Exception as e:
                    logger.error(
                        f"Handler {handler.__class__.__name__} failed "
                        f"for event {event.event_type}: {e}"
                    )

    @abstractmethod
    async def start(self, topics: list[str] | None = None) -> None:
        """Start consuming events.

        Args:
            topics: Optional list of topics to subscribe to
        """
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop consuming events."""
        pass

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the message broker."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the message broker."""
        pass


class InMemorySubscriber(EventSubscriber):
    """In-memory event subscriber for testing and development.

    Allows direct event injection for testing handlers without
    a message broker.
    """

    def __init__(self) -> None:
        """Initialize the in-memory subscriber."""
        super().__init__()
        self._running = False
        self._event_queue: asyncio.Queue[DomainEvent[Any]] = asyncio.Queue()
        self._consumer_task: asyncio.Task[None] | None = None
        self._processed_events: list[DomainEvent[Any]] = []

    @property
    def processed_events(self) -> list[DomainEvent[Any]]:
        """Get all processed events."""
        return self._processed_events.copy()

    def clear(self) -> None:
        """Clear processed events."""
        self._processed_events.clear()

    async def inject_event(self, event: DomainEvent[Any]) -> None:
        """Inject an event for processing (for testing).

        Args:
            event: The event to inject
        """
        await self._event_queue.put(event)

    async def process_event(self, event: DomainEvent[Any]) -> None:
        """Process a single event directly (for testing).

        Args:
            event: The event to process
        """
        self._processed_events.append(event)
        await self.dispatch(event)

    async def _consume(self) -> None:
        """Internal consumer loop."""
        while self._running:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=0.1)
                await self.process_event(event)
                self._event_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

    async def start(self, topics: list[str] | None = None) -> None:
        """Start the consumer loop.

        Args:
            topics: Ignored for in-memory subscriber
        """
        self._running = True
        self._consumer_task = asyncio.create_task(self._consume())
        logger.debug("InMemorySubscriber started")

    async def stop(self) -> None:
        """Stop the consumer loop."""
        self._running = False
        if self._consumer_task:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass
        logger.debug("InMemorySubscriber stopped")

    async def connect(self) -> None:
        """No-op for in-memory subscriber."""
        logger.debug("InMemorySubscriber connected")

    async def disconnect(self) -> None:
        """No-op for in-memory subscriber."""
        logger.debug("InMemorySubscriber disconnected")


class SubscriptionError(Exception):
    """Exception raised when subscription fails."""

    def __init__(self, message: str, topic: str | None = None) -> None:
        """Initialize subscription error.

        Args:
            message: Error message
            topic: The topic that failed
        """
        super().__init__(message)
        self.topic = topic

