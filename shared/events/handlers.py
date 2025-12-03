"""Event handler protocol and base implementations.

Defines the contract for event handlers following the Strategy pattern.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel

from shared.events.base import DomainEvent

PayloadT = TypeVar("PayloadT", bound=BaseModel)


class EventHandler(ABC, Generic[PayloadT]):
    """Abstract base class for event handlers.

    Implement this protocol to create handlers for specific event types.
    Each handler should focus on a single responsibility.

    Example:
        >>> class UserRegisteredHandler(EventHandler[UserRegisteredPayload]):
        ...     async def handle(self, event: DomainEvent[UserRegisteredPayload]) -> None:
        ...         # Send welcome email, update analytics, etc.
        ...         pass
        ...
        ...     def can_handle(self, event_type: str) -> bool:
        ...         return event_type == AuthEventType.USER_REGISTERED
    """

    @abstractmethod
    async def handle(self, event: DomainEvent[PayloadT]) -> None:
        """Process the domain event.

        Args:
            event: The domain event to process

        Raises:
            Exception: If event processing fails
        """
        pass

    @abstractmethod
    def can_handle(self, event_type: str) -> bool:
        """Check if this handler can process the given event type.

        Args:
            event_type: The event type string to check

        Returns:
            True if this handler can process the event type
        """
        pass


class CompositeEventHandler(EventHandler[PayloadT]):
    """Composite handler that delegates to multiple handlers.

    Implements the Composite pattern to allow multiple handlers
    to process the same event type.
    """

    def __init__(self) -> None:
        """Initialize with empty handler list."""
        self._handlers: list[EventHandler[PayloadT]] = []

    def add_handler(self, handler: EventHandler[PayloadT]) -> None:
        """Add a handler to the composite.

        Args:
            handler: Handler to add
        """
        self._handlers.append(handler)

    def remove_handler(self, handler: EventHandler[PayloadT]) -> None:
        """Remove a handler from the composite.

        Args:
            handler: Handler to remove
        """
        self._handlers.remove(handler)

    async def handle(self, event: DomainEvent[PayloadT]) -> None:
        """Delegate event to all registered handlers.

        Args:
            event: The domain event to process
        """
        for handler in self._handlers:
            if handler.can_handle(event.event_type):
                await handler.handle(event)

    def can_handle(self, event_type: str) -> bool:
        """Check if any registered handler can process the event type.

        Args:
            event_type: The event type string to check

        Returns:
            True if any handler can process the event type
        """
        return any(h.can_handle(event_type) for h in self._handlers)

