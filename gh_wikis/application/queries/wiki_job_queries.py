"""Query handlers for wiki job operations."""
from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from gh_wikis.domain.model.wiki_job import ExportFile, WikiJob
from gh_wikis.domain.repositories.wiki_job_repository import (
    ExportFileRepository,
    WikiJobRepository,
)


@dataclass
class GetWikiJobQuery:
    """Query to get a wiki job by ID."""

    job_id: UUID


class GetWikiJobHandler:
    """Handler for GetWikiJobQuery."""

    def __init__(self, wiki_job_repository: WikiJobRepository):
        """Initialize the handler."""
        self.wiki_job_repository = wiki_job_repository

    async def handle(self, query: GetWikiJobQuery) -> Optional[WikiJob]:
        """Handle the query."""
        return await self.wiki_job_repository.get(query.job_id)


@dataclass
class ListWikiJobsQuery:
    """Query to list wiki jobs."""

    limit: int = 100
    offset: int = 0


class ListWikiJobsHandler:
    """Handler for ListWikiJobsQuery."""

    def __init__(self, wiki_job_repository: WikiJobRepository):
        """Initialize the handler."""
        self.wiki_job_repository = wiki_job_repository

    async def handle(self, query: ListWikiJobsQuery) -> List[WikiJob]:
        """Handle the query."""
        return await self.wiki_job_repository.list_all(query.limit, query.offset)


@dataclass
class GetExportFilesQuery:
    """Query to get export files for a job."""

    job_id: UUID


class GetExportFilesHandler:
    """Handler for GetExportFilesQuery."""

    def __init__(self, export_file_repository: ExportFileRepository):
        """Initialize the handler."""
        self.export_file_repository = export_file_repository

    async def handle(self, query: GetExportFilesQuery) -> List[ExportFile]:
        """Handle the query."""
        return await self.export_file_repository.list_by_job(query.job_id)


@dataclass
class GetExportFileQuery:
    """Query to get an export file by ID."""

    file_id: UUID


class GetExportFileHandler:
    """Handler for GetExportFileQuery."""

    def __init__(self, export_file_repository: ExportFileRepository):
        """Initialize the handler."""
        self.export_file_repository = export_file_repository

    async def handle(self, query: GetExportFileQuery) -> Optional[ExportFile]:
        """Handle the query."""
        return await self.export_file_repository.get(query.file_id)