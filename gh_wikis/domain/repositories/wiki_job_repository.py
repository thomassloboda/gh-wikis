"""Repository interface for wiki jobs."""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from gh_wikis.domain.model.wiki_job import ExportFile, WikiJob


class WikiJobRepository(ABC):
    """Repository interface for wiki jobs."""

    @abstractmethod
    async def add(self, wiki_job: WikiJob) -> None:
        """Add a new wiki job to the repository."""
        pass

    @abstractmethod
    async def get(self, job_id: UUID) -> Optional[WikiJob]:
        """Get a wiki job by ID."""
        pass

    @abstractmethod
    async def update(self, wiki_job: WikiJob) -> None:
        """Update a wiki job."""
        pass

    @abstractmethod
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[WikiJob]:
        """List all wiki jobs."""
        pass
        
    @abstractmethod
    async def delete(self, job_id: UUID) -> None:
        """Delete a wiki job."""
        pass


class ExportFileRepository(ABC):
    """Repository interface for export files."""

    @abstractmethod
    async def add(self, export_file: ExportFile) -> None:
        """Add a new export file to the repository."""
        pass

    @abstractmethod
    async def get(self, file_id: UUID) -> Optional[ExportFile]:
        """Get an export file by ID."""
        pass

    @abstractmethod
    async def list_by_job(self, job_id: UUID) -> List[ExportFile]:
        """List all export files for a job."""
        pass

    @abstractmethod
    async def delete(self, file_id: UUID) -> None:
        """Delete an export file."""
        pass