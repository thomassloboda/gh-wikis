"""Domain model for wiki export jobs."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import List, Optional
from uuid import UUID, uuid4


class WikiJobStatus(Enum):
    """Status of a wiki export job."""

    PENDING = auto()
    PROCESSING = auto()
    COMPLETED = auto()
    FAILED = auto()


class FileFormat(Enum):
    """Available output formats."""

    MARKDOWN = auto()
    PDF = auto()
    EPUB = auto()


@dataclass
class WikiJob:
    """Domain entity representing a wiki export job."""

    id: UUID
    repository_url: str
    status: WikiJobStatus
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress_percentage: int = 0
    progress_message: str = ""

    @classmethod
    def create(cls, repository_url: str) -> "WikiJob":
        """Create a new wiki job."""
        now = datetime.utcnow()
        return cls(
            id=uuid4(),
            repository_url=repository_url,
            status=WikiJobStatus.PENDING,
            created_at=now,
            updated_at=now,
        )

    def start_processing(self) -> None:
        """Mark the job as processing."""
        self.status = WikiJobStatus.PROCESSING
        self.updated_at = datetime.utcnow()

    def update_progress(self, percentage: int, message: str) -> None:
        """Update job progress."""
        self.progress_percentage = percentage
        self.progress_message = message
        self.updated_at = datetime.utcnow()

    def complete(self) -> None:
        """Mark the job as completed."""
        self.status = WikiJobStatus.COMPLETED
        self.progress_percentage = 100
        self.progress_message = "Export completed successfully"
        self.completed_at = datetime.utcnow()
        self.updated_at = self.completed_at

    def fail(self, error_message: str) -> None:
        """Mark the job as failed."""
        self.status = WikiJobStatus.FAILED
        self.error_message = error_message
        self.updated_at = datetime.utcnow()


@dataclass
class ExportFile:
    """Domain entity representing an exported file."""

    id: UUID
    job_id: UUID
    format: FileFormat
    filename: str
    storage_path: str
    size_bytes: int
    created_at: datetime

    @classmethod
    def create(
        cls, job_id: UUID, format: FileFormat, filename: str, storage_path: str, size_bytes: int
    ) -> "ExportFile":
        """Create a new export file."""
        return cls(
            id=uuid4(),
            job_id=job_id,
            format=format,
            filename=filename,
            storage_path=storage_path,
            size_bytes=size_bytes,
            created_at=datetime.utcnow(),
        )