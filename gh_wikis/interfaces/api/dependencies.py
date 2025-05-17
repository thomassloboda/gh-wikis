"""FastAPI dependencies."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from gh_wikis.application.commands.wiki_job_commands import (
    CreateWikiJobHandler,
    DeleteExportFileHandler,
    DeleteWikiJobHandler,
    FailWikiJobHandler,
    StartWikiJobHandler,
    UpdateWikiJobProgressHandler,
)
from gh_wikis.application.events.publisher import EventPublisher
from gh_wikis.application.queries.wiki_job_queries import (
    GetExportFileHandler,
    GetExportFilesHandler,
    GetWikiJobHandler,
    ListWikiJobsHandler,
)
from gh_wikis.application.services.wiki_processor import WikiProcessor
from gh_wikis.domain.repositories.wiki_job_repository import (
    ExportFileRepository,
    WikiJobRepository,
)
from gh_wikis.domain.services.file_storage import FileStorageService
from gh_wikis.domain.services.github_service import GitHubService
from gh_wikis.infrastructure.db.database import Database
from gh_wikis.infrastructure.db.repositories import (
    SQLAlchemyExportFileRepository,
    SQLAlchemyWikiJobRepository,
)
from gh_wikis.infrastructure.events.redis_publisher import RedisEventPublisher
from gh_wikis.infrastructure.services.github_service_impl import GitHubServiceImpl
from gh_wikis.infrastructure.services.minio_storage import MinioStorageService

# Database session
db = Database()


async def get_session() -> AsyncSession:
    """Get a database session."""
    async with db.session() as session:
        yield session


# Services
def get_github_service() -> GitHubService:
    """Get the GitHub service implementation."""
    return GitHubServiceImpl()


def get_file_storage() -> FileStorageService:
    """Get the file storage service implementation."""
    return MinioStorageService()


def get_event_publisher() -> EventPublisher:
    """Get the event publisher implementation."""
    return RedisEventPublisher()


# Repositories
def get_wiki_job_repository(
    session: AsyncSession = Depends(get_session),
) -> WikiJobRepository:
    """Get the wiki job repository implementation."""
    return SQLAlchemyWikiJobRepository(session)


def get_export_file_repository(
    session: AsyncSession = Depends(get_session),
) -> ExportFileRepository:
    """Get the export file repository implementation."""
    return SQLAlchemyExportFileRepository(session)


# Command handlers
def get_create_wiki_job_handler(
    wiki_job_repository: WikiJobRepository = Depends(get_wiki_job_repository),
    event_publisher: EventPublisher = Depends(get_event_publisher),
) -> CreateWikiJobHandler:
    """Get the create wiki job command handler."""
    return CreateWikiJobHandler(wiki_job_repository, event_publisher)


def get_start_wiki_job_handler(
    wiki_job_repository: WikiJobRepository = Depends(get_wiki_job_repository),
    event_publisher: EventPublisher = Depends(get_event_publisher),
) -> StartWikiJobHandler:
    """Get the start wiki job command handler."""
    return StartWikiJobHandler(wiki_job_repository, event_publisher)


def get_update_wiki_job_progress_handler(
    wiki_job_repository: WikiJobRepository = Depends(get_wiki_job_repository),
    event_publisher: EventPublisher = Depends(get_event_publisher),
) -> UpdateWikiJobProgressHandler:
    """Get the update wiki job progress command handler."""
    return UpdateWikiJobProgressHandler(wiki_job_repository, event_publisher)


def get_fail_wiki_job_handler(
    wiki_job_repository: WikiJobRepository = Depends(get_wiki_job_repository),
    event_publisher: EventPublisher = Depends(get_event_publisher),
) -> FailWikiJobHandler:
    """Get the fail wiki job command handler."""
    return FailWikiJobHandler(wiki_job_repository, event_publisher)


# Query handlers
def get_wiki_job_handler(
    wiki_job_repository: WikiJobRepository = Depends(get_wiki_job_repository),
) -> GetWikiJobHandler:
    """Get the wiki job query handler."""
    return GetWikiJobHandler(wiki_job_repository)


def get_list_wiki_jobs_handler(
    wiki_job_repository: WikiJobRepository = Depends(get_wiki_job_repository),
) -> ListWikiJobsHandler:
    """Get the list wiki jobs query handler."""
    return ListWikiJobsHandler(wiki_job_repository)


def get_export_files_handler(
    export_file_repository: ExportFileRepository = Depends(get_export_file_repository),
) -> GetExportFilesHandler:
    """Get the export files query handler."""
    return GetExportFilesHandler(export_file_repository)


def get_export_file_handler(
    export_file_repository: ExportFileRepository = Depends(get_export_file_repository),
) -> GetExportFileHandler:
    """Get the export file query handler."""
    return GetExportFileHandler(export_file_repository)


# Handlers for deletion
def get_delete_wiki_job_handler(
    wiki_job_repository: WikiJobRepository = Depends(get_wiki_job_repository),
    export_file_repository: ExportFileRepository = Depends(get_export_file_repository),
    file_storage: FileStorageService = Depends(get_file_storage),
    event_publisher: EventPublisher = Depends(get_event_publisher),
) -> DeleteWikiJobHandler:
    """Get the delete wiki job handler."""
    return DeleteWikiJobHandler(wiki_job_repository, export_file_repository, file_storage, event_publisher)


def get_delete_export_file_handler(
    export_file_repository: ExportFileRepository = Depends(get_export_file_repository),
    file_storage: FileStorageService = Depends(get_file_storage),
    event_publisher: EventPublisher = Depends(get_event_publisher),
) -> DeleteExportFileHandler:
    """Get the delete export file handler."""
    return DeleteExportFileHandler(export_file_repository, file_storage, event_publisher)


# Services
def get_wiki_processor(
    github_service: GitHubService = Depends(get_github_service),
    file_storage: FileStorageService = Depends(get_file_storage),
    wiki_job_repository: WikiJobRepository = Depends(get_wiki_job_repository),
    export_file_repository: ExportFileRepository = Depends(get_export_file_repository),
    event_publisher: EventPublisher = Depends(get_event_publisher),
) -> WikiProcessor:
    """Get the wiki processor service."""
    return WikiProcessor(
        github_service, file_storage, wiki_job_repository, export_file_repository, event_publisher
    )