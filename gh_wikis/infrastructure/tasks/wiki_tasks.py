"""Celery tasks for wiki processing."""
import asyncio
from uuid import UUID

from celery import Task, shared_task
from sqlalchemy.ext.asyncio import AsyncSession

from gh_wikis.application.commands.wiki_job_commands import (
    FailWikiJob,
    FailWikiJobHandler,
    StartWikiJob,
    StartWikiJobHandler,
)
from gh_wikis.application.services.wiki_processor import WikiProcessor
from gh_wikis.infrastructure.celery_app import celery_app
from gh_wikis.infrastructure.db.database import Database
from gh_wikis.infrastructure.db.repositories import (
    SQLAlchemyExportFileRepository,
    SQLAlchemyWikiJobRepository,
)
from gh_wikis.infrastructure.events.redis_publisher import RedisEventPublisher
from gh_wikis.infrastructure.services.github_service_impl import GitHubServiceImpl
from gh_wikis.infrastructure.services.minio_storage import MinioStorageService


class DatabaseTask(Task):
    """Base task with database session handling."""

    _db = None

    @property
    def db(self) -> Database:
        """Get the database instance."""
        if self._db is None:
            self._db = Database()
        return self._db

    async def get_session(self) -> AsyncSession:
        """Get a database session."""
        async with self.db.session() as session:
            return session
            
    def after_return(self, *args, **kwargs):
        """Clean up after task execution."""
        # Clear any remaining connections to avoid issues with
        # "another operation is in progress" errors
        if self._db is not None:
            self._db = None


@shared_task(bind=True, base=DatabaseTask, name="process_wiki")
def process_wiki(self, job_id: str) -> None:
    """Process a wiki job."""
    job_uuid = UUID(job_id)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_process_wiki_async(self, job_uuid))
    finally:
        loop.close()


async def _process_wiki_async(task: DatabaseTask, job_id: UUID) -> None:
    """Process a wiki job asynchronously."""
    async with task.db.session() as session:
        event_publisher = RedisEventPublisher()

        # Set up repositories and service
        job_repo = SQLAlchemyWikiJobRepository(session)
        file_repo = SQLAlchemyExportFileRepository(session)
        github_service = GitHubServiceImpl()
        file_storage = MinioStorageService()

        # Create start job command handler
        start_handler = StartWikiJobHandler(job_repo, event_publisher)
        start_command = StartWikiJob(job_id=job_id)

        # Start the job
        try:
            await start_handler.handle(start_command)
            await session.commit()  # Commit after starting job

            # Process the wiki
            processor = WikiProcessor(
                github_service=github_service,
                file_storage=file_storage,
                wiki_job_repository=job_repo,
                export_file_repository=file_repo,
                event_publisher=event_publisher,
            )
            await processor.process_wiki(job_id)
            await session.commit()  # Commit after processing
        except Exception as e:
            # Handle any exceptions
            fail_handler = FailWikiJobHandler(job_repo, event_publisher)
            fail_command = FailWikiJob(job_id=job_id, error_message=str(e))
            await fail_handler.handle(fail_command)
            await session.commit()  # Commit after handling failure