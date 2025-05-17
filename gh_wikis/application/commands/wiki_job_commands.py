"""Command handlers for wiki job operations."""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from gh_wikis.domain.events.wiki_job_events import (
    Event,
    ExportFileDeleted,
    WikiJobCreated,
    WikiJobDeleted,
    WikiJobFailed,
    WikiJobProgressUpdated,
    WikiJobStarted,
)
from gh_wikis.domain.model.wiki_job import WikiJob
from gh_wikis.domain.repositories.wiki_job_repository import ExportFileRepository, WikiJobRepository
from gh_wikis.domain.services.file_storage import FileStorageService


@dataclass
class CreateWikiJob:
    """Command to create a new wiki job."""

    repository_url: str


class CreateWikiJobHandler:
    """Handler for CreateWikiJob command."""

    def __init__(self, wiki_job_repository: WikiJobRepository, event_publisher: "EventPublisher"):
        """Initialize the handler."""
        self.wiki_job_repository = wiki_job_repository
        self.event_publisher = event_publisher

    async def handle(self, command: CreateWikiJob) -> UUID:
        """Handle the command."""
        wiki_job = WikiJob.create(command.repository_url)

        await self.wiki_job_repository.add(wiki_job)

        event = WikiJobCreated(
            id=uuid4(),
            timestamp=wiki_job.created_at,
            aggregate_id=wiki_job.id,
            repository_url=wiki_job.repository_url,
        )
        await self.event_publisher.publish(event)

        return wiki_job.id


@dataclass
class StartWikiJob:
    """Command to start processing a wiki job."""

    job_id: UUID


class StartWikiJobHandler:
    """Handler for StartWikiJob command."""

    def __init__(self, wiki_job_repository: WikiJobRepository, event_publisher: "EventPublisher"):
        """Initialize the handler."""
        self.wiki_job_repository = wiki_job_repository
        self.event_publisher = event_publisher

    async def handle(self, command: StartWikiJob) -> None:
        """Handle the command."""
        job = await self.wiki_job_repository.get(command.job_id)
        if job is None:
            raise ValueError(f"Wiki job with ID {command.job_id} not found")

        job.start_processing()
        await self.wiki_job_repository.update(job)

        event = WikiJobStarted(
            id=uuid4(),
            timestamp=job.updated_at,
            aggregate_id=job.id,
        )
        await self.event_publisher.publish(event)


@dataclass
class UpdateWikiJobProgress:
    """Command to update wiki job progress."""

    job_id: UUID
    percentage: int
    message: str


class UpdateWikiJobProgressHandler:
    """Handler for UpdateWikiJobProgress command."""

    def __init__(self, wiki_job_repository: WikiJobRepository, event_publisher: "EventPublisher"):
        """Initialize the handler."""
        self.wiki_job_repository = wiki_job_repository
        self.event_publisher = event_publisher

    async def handle(self, command: UpdateWikiJobProgress) -> None:
        """Handle the command."""
        job = await self.wiki_job_repository.get(command.job_id)
        if job is None:
            raise ValueError(f"Wiki job with ID {command.job_id} not found")

        job.update_progress(command.percentage, command.message)
        await self.wiki_job_repository.update(job)

        event = WikiJobProgressUpdated(
            id=uuid4(),
            timestamp=job.updated_at,
            aggregate_id=job.id,
            percentage=command.percentage,
            message=command.message,
        )
        await self.event_publisher.publish(event)


@dataclass
class FailWikiJob:
    """Command to mark a wiki job as failed."""

    job_id: UUID
    error_message: str


class FailWikiJobHandler:
    """Handler for FailWikiJob command."""

    def __init__(self, wiki_job_repository: WikiJobRepository, event_publisher: "EventPublisher"):
        """Initialize the handler."""
        self.wiki_job_repository = wiki_job_repository
        self.event_publisher = event_publisher

    async def handle(self, command: FailWikiJob) -> None:
        """Handle the command."""
        job = await self.wiki_job_repository.get(command.job_id)
        if job is None:
            raise ValueError(f"Wiki job with ID {command.job_id} not found")

        job.fail(command.error_message)
        await self.wiki_job_repository.update(job)

        event = WikiJobFailed(
            id=uuid4(),
            timestamp=job.updated_at,
            aggregate_id=job.id,
            error_message=command.error_message,
        )
        await self.event_publisher.publish(event)


@dataclass
class DeleteWikiJob:
    """Command to delete a wiki job."""

    job_id: UUID


class DeleteWikiJobHandler:
    """Handler for DeleteWikiJob command."""

    def __init__(
        self, 
        wiki_job_repository: WikiJobRepository, 
        export_file_repository: ExportFileRepository,
        file_storage: FileStorageService,
        event_publisher: "EventPublisher"
    ):
        """Initialize the handler."""
        self.wiki_job_repository = wiki_job_repository
        self.export_file_repository = export_file_repository
        self.file_storage = file_storage
        self.event_publisher = event_publisher

    async def handle(self, command: DeleteWikiJob) -> None:
        """Handle the command."""
        # Get the job to verify it exists
        job = await self.wiki_job_repository.get(command.job_id)
        if job is None:
            raise ValueError(f"Wiki job with ID {command.job_id} not found")

        # Get associated files to delete from storage
        files = await self.export_file_repository.list_by_job(command.job_id)
        
        # Delete files from storage
        for file in files:
            try:
                await self.file_storage.delete_file(file.storage_path)
            except Exception as e:
                # Log error but continue
                print(f"Error deleting file {file.storage_path}: {str(e)}")
        
        # Delete the job (this will cascade delete export files in DB)
        await self.wiki_job_repository.delete(command.job_id)
        
        # Publish event
        event = WikiJobDeleted(
            id=uuid4(),
            timestamp=datetime.utcnow(),
            aggregate_id=command.job_id,
        )
        await self.event_publisher.publish(event)


@dataclass
class DeleteExportFile:
    """Command to delete an export file."""

    file_id: UUID


class DeleteExportFileHandler:
    """Handler for DeleteExportFile command."""

    def __init__(
        self, 
        export_file_repository: ExportFileRepository, 
        file_storage: FileStorageService,
        event_publisher: "EventPublisher"
    ):
        """Initialize the handler."""
        self.export_file_repository = export_file_repository
        self.file_storage = file_storage
        self.event_publisher = event_publisher

    async def handle(self, command: DeleteExportFile) -> None:
        """Handle the command."""
        # Get the file to verify it exists and get storage path
        file = await self.export_file_repository.get(command.file_id)
        if file is None:
            raise ValueError(f"Export file with ID {command.file_id} not found")
        
        # Delete the file from storage
        try:
            await self.file_storage.delete_file(file.storage_path)
        except Exception as e:
            print(f"Error deleting file {file.storage_path}: {str(e)}")
        
        # Delete the file from database
        await self.export_file_repository.delete(command.file_id)
        
        # Publish event
        event = ExportFileDeleted(
            id=uuid4(),
            timestamp=datetime.utcnow(),
            aggregate_id=file.job_id,
            file_id=command.file_id,
            format=file.format,
            filename=file.filename,
        )
        await self.event_publisher.publish(event)