"""SQLAlchemy models for the database."""
import enum
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Define naming convention for constraints
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)

Base = declarative_base(metadata=metadata)


class WikiJobStatusEnum(enum.Enum):
    """Database enum for wiki job status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FileFormatEnum(enum.Enum):
    """Database enum for file formats."""

    MARKDOWN = "markdown"
    PDF = "pdf"
    EPUB = "epub"


class WikiJobModel(Base):
    """SQLAlchemy model for wiki jobs."""

    __tablename__ = "wiki_jobs"

    id = Column(PGUUID, primary_key=True)
    repository_url = Column(String(255), nullable=False)
    status = Column(Enum(WikiJobStatusEnum), nullable=False, default=WikiJobStatusEnum.PENDING)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    progress_percentage = Column(Integer, nullable=False, default=0)
    progress_message = Column(String(255), nullable=False, default="")

    export_files = relationship("ExportFileModel", back_populates="wiki_job", cascade="all, delete")


class ExportFileModel(Base):
    """SQLAlchemy model for export files."""

    __tablename__ = "export_files"

    id = Column(PGUUID, primary_key=True)
    job_id = Column(PGUUID, ForeignKey("wiki_jobs.id"), nullable=False)
    format = Column(Enum(FileFormatEnum), nullable=False)
    filename = Column(String(255), nullable=False)
    storage_path = Column(String(255), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    wiki_job = relationship("WikiJobModel", back_populates="export_files")