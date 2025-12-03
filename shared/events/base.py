"""Base event models for domain events.

Provides the foundation for all domain events in the system using Pydantic
for validation and serialization.
"""

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class EventMetadata(BaseModel):
    """Metadata associated with every domain event.

    Attributes:
        event_id: Unique identifier for this event instance
        timestamp: When the event occurred (UTC)
        version: Schema version for the event
        correlation_id: ID to trace related events across services
        causation_id: ID of the event that caused this event
        source: Service/component that produced the event
    """

    model_config = ConfigDict(frozen=True)

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = "1.0"
    correlation_id: str | None = None
    causation_id: str | None = None
    source: str = "unknown"


PayloadT = TypeVar("PayloadT", bound=BaseModel)


class DomainEvent(BaseModel, Generic[PayloadT]):
    """Base class for all domain events.

    Domain events represent something that happened in the domain that other
    parts of the system might be interested in. They are immutable records
    of facts.

    Attributes:
        event_type: String identifier for the event type
        metadata: Event metadata (id, timestamp, correlation, etc.)
        payload: The event-specific data

    Example:
        >>> class UserData(BaseModel):
        ...     user_id: str
        ...     email: str
        ...
        >>> event = DomainEvent[UserData](
        ...     event_type="auth.user.registered",
        ...     payload=UserData(user_id="123", email="test@example.com"),
        ...     metadata=EventMetadata(source="auth-service"),
        ... )
    """

    model_config = ConfigDict(frozen=True)

    event_type: str
    metadata: EventMetadata = Field(default_factory=EventMetadata)
    payload: PayloadT

    def to_dict(self) -> dict[str, Any]:
        """Serialize event to dictionary for transport."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DomainEvent[PayloadT]":
        """Deserialize event from dictionary."""
        return cls.model_validate(data)

    def with_correlation(self, correlation_id: str) -> "DomainEvent[PayloadT]":
        """Create a copy of this event with a correlation ID set."""
        new_metadata = EventMetadata(
            event_id=self.metadata.event_id,
            timestamp=self.metadata.timestamp,
            version=self.metadata.version,
            correlation_id=correlation_id,
            causation_id=self.metadata.causation_id,
            source=self.metadata.source,
        )
        return self.model_copy(update={"metadata": new_metadata})

    def with_causation(self, causation_id: str) -> "DomainEvent[PayloadT]":
        """Create a copy of this event with a causation ID set."""
        new_metadata = EventMetadata(
            event_id=self.metadata.event_id,
            timestamp=self.metadata.timestamp,
            version=self.metadata.version,
            correlation_id=self.metadata.correlation_id,
            causation_id=causation_id,
            source=self.metadata.source,
        )
        return self.model_copy(update={"metadata": new_metadata})

