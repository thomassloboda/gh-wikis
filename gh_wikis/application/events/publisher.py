"""Event publisher abstraction."""
from abc import ABC, abstractmethod
from typing import Generic, List, TypeVar

from gh_wikis.domain.events.wiki_job_events import Event

T = TypeVar("T", bound=Event)


class EventPublisher(ABC):
    """Interface for publishing events."""

    @abstractmethod
    async def publish(self, event: Event) -> None:
        """Publish an event."""
        pass


class EventHandler(Generic[T], ABC):
    """Base interface for event handlers."""

    @abstractmethod
    async def handle(self, event: T) -> None:
        """Handle an event."""
        pass


class EventBus:
    """Simple in-memory event bus implementation."""

    def __init__(self):
        """Initialize the event bus."""
        self._handlers: dict[type, List[EventHandler]] = {}

    def register(self, event_type: type, handler: EventHandler) -> None:
        """Register a handler for an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def publish(self, event: Event) -> None:
        """Publish an event to all registered handlers."""
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            await handler.handle(event)