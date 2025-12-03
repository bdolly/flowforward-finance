"""System-level event type definitions.

Domain-specific event types should be defined in their respective services.
"""

from enum import StrEnum


class EventType(StrEnum):
    """System-level event types applicable across all domains."""

    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_HEALTH_CHECK = "system.health_check"
