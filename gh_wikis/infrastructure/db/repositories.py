"""SQLAlchemy implementations of repository interfaces."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gh_wikis.domain.model.wiki_job import ExportFile, FileFormat, WikiJob, WikiJobStatus
from gh_wikis.domain.repositories.wiki_job_repository import (
    ExportFileRepository,
    WikiJobRepository,
)
from gh_wikis.infrastructure.db.models import (
    ExportFileModel,
    FileFormatEnum,
    WikiJobModel,
    WikiJobStatusEnum,
)


def _map_job_status_to_enum(status: WikiJobStatus) -> WikiJobStatusEnum:
    """Map domain job status to database enum."""
    mapping = {
        WikiJobStatus.PENDING: WikiJobStatusEnum.PENDING,
        WikiJobStatus.PROCESSING: WikiJobStatusEnum.PROCESSING,
        WikiJobStatus.COMPLETED: WikiJobStatusEnum.COMPLETED,
        WikiJobStatus.FAILED: WikiJobStatusEnum.FAILED,
    }
    return mapping[status]


def _map_enum_to_job_status(status_enum: WikiJobStatusEnum) -> WikiJobStatus:
    """Map database enum to domain job status."""
    mapping = {
        WikiJobStatusEnum.PENDING: WikiJobStatus.PENDING,
        WikiJobStatusEnum.PROCESSING: WikiJobStatus.PROCESSING,
        WikiJobStatusEnum.COMPLETED: WikiJobStatus.COMPLETED,
        WikiJobStatusEnum.FAILED: WikiJobStatus.FAILED,
    }
    return mapping[status_enum]


def _map_file_format_to_enum(format: FileFormat) -> FileFormatEnum:
    """Map domain file format to database enum."""
    mapping = {
        FileFormat.MARKDOWN: FileFormatEnum.MARKDOWN,
        FileFormat.PDF: FileFormatEnum.PDF,
        FileFormat.EPUB: FileFormatEnum.EPUB,
    }
    return mapping[format]


def _map_enum_to_file_format(format_enum: FileFormatEnum) -> FileFormat:
    """Map database enum to domain file format."""
    mapping = {
        FileFormatEnum.MARKDOWN: FileFormat.MARKDOWN,
        FileFormatEnum.PDF: FileFormat.PDF,
        FileFormatEnum.EPUB: FileFormat.EPUB,
    }
    return mapping[format_enum]


def _map_model_to_job(model: WikiJobModel) -> WikiJob:
    """Map database model to domain entity."""
    return WikiJob(
        id=model.id,
        repository_url=model.repository_url,
        status=_map_enum_to_job_status(model.status),
        created_at=model.created_at,
        updated_at=model.updated_at,
        completed_at=model.completed_at,
        error_message=model.error_message,
        progress_percentage=model.progress_percentage,
        progress_message=model.progress_message,
    )


def _map_job_to_model(job: WikiJob, model: Optional[WikiJobModel] = None) -> WikiJobModel:
    """Map domain entity to database model."""
    if model is None:
        model = WikiJobModel(id=job.id)

    model.repository_url = job.repository_url
    model.status = _map_job_status_to_enum(job.status)
    model.created_at = job.created_at
    model.updated_at = job.updated_at
    model.completed_at = job.completed_at
    model.error_message = job.error_message
    model.progress_percentage = job.progress_percentage
    model.progress_message = job.progress_message

    return model


def _map_model_to_file(model: ExportFileModel) -> ExportFile:
    """Map database model to domain entity."""
    return ExportFile(
        id=model.id,
        job_id=model.job_id,
        format=_map_enum_to_file_format(model.format),
        filename=model.filename,
        storage_path=model.storage_path,
        size_bytes=model.size_bytes,
        created_at=model.created_at,
    )


def _map_file_to_model(file: ExportFile) -> ExportFileModel:
    """Map domain entity to database model."""
    return ExportFileModel(
        id=file.id,
        job_id=file.job_id,
        format=_map_file_format_to_enum(file.format),
        filename=file.filename,
        storage_path=file.storage_path,
        size_bytes=file.size_bytes,
        created_at=file.created_at,
    )


class SQLAlchemyWikiJobRepository(WikiJobRepository):
    """SQLAlchemy implementation of WikiJobRepository."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository."""
        self.session = session

    async def add(self, wiki_job: WikiJob) -> None:
        """Add a new wiki job to the repository."""
        model = _map_job_to_model(wiki_job)
        self.session.add(model)
        await self.session.flush()

    async def get(self, job_id: UUID) -> Optional[WikiJob]:
        """Get a wiki job by ID."""
        query = select(WikiJobModel).where(WikiJobModel.id == job_id)
        result = await self.session.execute(query)
        model = result.scalars().first()
        if model is None:
            return None
        return _map_model_to_job(model)

    async def update(self, wiki_job: WikiJob) -> None:
        """Update a wiki job."""
        query = select(WikiJobModel).where(WikiJobModel.id == wiki_job.id)
        result = await self.session.execute(query)
        model = result.scalars().first()
        if model is None:
            raise ValueError(f"Wiki job with ID {wiki_job.id} not found")
        _map_job_to_model(wiki_job, model)
        await self.session.flush()

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[WikiJob]:
        """List all wiki jobs."""
        query = (
            select(WikiJobModel)
            .order_by(WikiJobModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [_map_model_to_job(model) for model in models]
        
    async def delete(self, job_id: UUID) -> None:
        """Delete a wiki job."""
        query = select(WikiJobModel).where(WikiJobModel.id == job_id)
        result = await self.session.execute(query)
        model = result.scalars().first()
        if model is not None:
            await self.session.delete(model)
            await self.session.flush()


class SQLAlchemyExportFileRepository(ExportFileRepository):
    """SQLAlchemy implementation of ExportFileRepository."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository."""
        self.session = session

    async def add(self, export_file: ExportFile) -> None:
        """Add a new export file to the repository."""
        model = _map_file_to_model(export_file)
        self.session.add(model)
        await self.session.flush()

    async def get(self, file_id: UUID) -> Optional[ExportFile]:
        """Get an export file by ID."""
        query = select(ExportFileModel).where(ExportFileModel.id == file_id)
        result = await self.session.execute(query)
        model = result.scalars().first()
        if model is None:
            return None
        return _map_model_to_file(model)

    async def list_by_job(self, job_id: UUID) -> List[ExportFile]:
        """List all export files for a job."""
        query = select(ExportFileModel).where(ExportFileModel.job_id == job_id)
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [_map_model_to_file(model) for model in models]

    async def delete(self, file_id: UUID) -> None:
        """Delete an export file."""
        query = select(ExportFileModel).where(ExportFileModel.id == file_id)
        result = await self.session.execute(query)
        model = result.scalars().first()
        if model is not None:
            await self.session.delete(model)
            await self.session.flush()