"""Domain events for wiki job processing."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from gh_wikis.domain.model.wiki_job import FileFormat


@dataclass
class Event:
    """Base event class."""

    id: UUID
    timestamp: datetime
    aggregate_id: UUID


@dataclass
class WikiJobCreated(Event):
    """Event emitted when a new wiki job is created."""

    repository_url: str


@dataclass
class WikiJobStarted(Event):
    """Event emitted when wiki job processing starts."""


@dataclass
class WikiJobProgressUpdated(Event):
    """Event emitted when wiki job progress is updated."""

    percentage: int
    message: str


@dataclass
class WikiJobCompleted(Event):
    """Event emitted when a wiki job is completed."""


@dataclass
class WikiJobFailed(Event):
    """Event emitted when a wiki job fails."""

    error_message: str


@dataclass
class ExportFileCreated(Event):
    """Event emitted when an export file is created."""

    file_id: UUID
    format: FileFormat
    filename: str
    storage_path: str
    size_bytes: int


@dataclass
class WikiJobDeleted(Event):
    """Event emitted when a wiki job is deleted."""
    pass


@dataclass
class ExportFileDeleted(Event):
    """Event emitted when an export file is deleted."""
    
    file_id: UUID
    format: Optional[FileFormat] = None
    filename: Optional[str] = None