"""File storage service interface."""
from abc import ABC, abstractmethod
from typing import BinaryIO, Optional, Tuple
from uuid import UUID


class FileStorageService(ABC):
    """Interface for file storage service."""

    @abstractmethod
    async def store_file(self, file_content: bytes, filename: str, job_id: UUID) -> Tuple[str, int]:
        """
        Store a file in the storage system.

        Args:
            file_content: The content of the file to store
            filename: The name of the file
            job_id: The ID of the job this file belongs to

        Returns:
            Tuple containing the storage path and file size in bytes
        """
        pass

    @abstractmethod
    async def get_file(self, storage_path: str) -> Optional[bytes]:
        """
        Retrieve a file from storage.

        Args:
            storage_path: Path to the file in storage

        Returns:
            File content as bytes if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_download_url(self, storage_path: str, expires_in_seconds: int = 3600) -> str:
        """
        Generate a pre-signed URL for downloading a file.

        Args:
            storage_path: Path to the file in storage
            expires_in_seconds: How long the URL should be valid for

        Returns:
            Pre-signed URL for downloading the file
        """
        pass

    @abstractmethod
    async def delete_file(self, storage_path: str) -> bool:
        """
        Delete a file from storage.

        Args:
            storage_path: Path to the file in storage

        Returns:
            True if the file was deleted, False otherwise
        """
        pass