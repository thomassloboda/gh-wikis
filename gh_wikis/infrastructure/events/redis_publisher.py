"""Redis-based event publisher."""
import json
from dataclasses import asdict
from datetime import datetime
from uuid import UUID

import redis.asyncio as redis

from gh_wikis.application.events.publisher import EventPublisher
from gh_wikis.domain.events.wiki_job_events import Event
from gh_wikis.domain.model.wiki_job import FileFormat
from gh_wikis.infrastructure.config import settings


class UUIDEncoder(json.JSONEncoder):
    """JSON encoder that handles UUIDs."""

    def default(self, obj):
        """Convert UUID objects to strings."""
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, FileFormat):
            return obj.name
        return super().default(obj)


class RedisEventPublisher(EventPublisher):
    """Redis implementation of the event publisher."""

    def __init__(self, redis_url: str = None):
        """Initialize the publisher."""
        self.redis_url = redis_url or settings.broker_url
        self.client = redis.from_url(self.redis_url)

    async def publish(self, event: Event) -> None:
        """Publish an event to Redis."""
        # Convert the event to a serializable format
        event_type = event.__class__.__name__
        event_data = asdict(event)

        # Add event type to the data
        event_data["event_type"] = event_type

        # Serialize the event
        serialized_event = json.dumps(event_data, cls=UUIDEncoder)

        # Publish to a channel based on the event type
        channel = f"events:{event_type}"
        await self.client.publish(channel, serialized_event)

        # Also publish to a general events channel
        await self.client.publish("events:all", serialized_event)