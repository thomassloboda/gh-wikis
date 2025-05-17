"""API schemas for data validation and serialization."""
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class WikiJobStatusSchema(str, Enum):
    """Wiki job status schema."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FileFormatSchema(str, Enum):
    """File format schema."""

    MARKDOWN = "markdown"
    PDF = "pdf"
    EPUB = "epub"


class CreateWikiJobRequest(BaseModel):
    """Schema for creating a new wiki job."""

    repository_url: HttpUrl = Field(..., description="GitHub repository URL")


class WikiJobResponse(BaseModel):
    """Schema for wiki job response."""

    id: UUID
    repository_url: str
    status: WikiJobStatusSchema
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress_percentage: int
    progress_message: str

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class WikiJobListResponse(BaseModel):
    """Schema for list of wiki jobs."""

    jobs: List[WikiJobResponse]
    total: int


class ExportFileResponse(BaseModel):
    """Schema for export file response."""

    id: UUID
    job_id: UUID
    format: FileFormatSchema
    filename: str
    size_bytes: int
    created_at: datetime
    download_url: str

    class Config:
        """Pydantic configuration."""

        from_attributes = True