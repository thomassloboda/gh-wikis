"""MinIO implementation of file storage service."""
import io
from typing import BinaryIO, Optional, Tuple
from uuid import UUID

from minio import Minio
from minio.error import S3Error

from gh_wikis.domain.services.file_storage import FileStorageService
from gh_wikis.infrastructure.config import settings


class MinioStorageService(FileStorageService):
    """MinIO implementation of file storage service."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        bucket_name: Optional[str] = None,
        secure: bool = False,
    ):
        """Initialize the service."""
        self.endpoint = endpoint or f"{settings.minio_host}:{settings.minio_port}"
        self.access_key = access_key or settings.minio_root_user
        self.secret_key = secret_key or settings.minio_root_password
        self.bucket_name = bucket_name or settings.minio_bucket_name
        self.secure = secure

        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure,
        )

        # Ensure the bucket exists
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Ensure the bucket exists."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except S3Error as e:
            raise ValueError(f"Error ensuring bucket exists: {str(e)}")

    async def store_file(self, file_content: bytes, filename: str, job_id: UUID) -> Tuple[str, int]:
        """Store a file in MinIO."""
        try:
            # Create an in-memory file-like object
            file_data = io.BytesIO(file_content)
            file_size = len(file_content)

            # Generate the storage path
            storage_path = f"{job_id}/{filename}"

            # Upload the file
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=storage_path,
                data=file_data,
                length=file_size,
                content_type="application/octet-stream",
            )

            return storage_path, file_size
        except S3Error as e:
            raise ValueError(f"Error storing file: {str(e)}")

    async def get_file(self, storage_path: str) -> Optional[bytes]:
        """Retrieve a file from MinIO."""
        try:
            response = self.client.get_object(self.bucket_name, storage_path)
            content = response.read()
            response.close()
            response.release_conn()
            return content
        except S3Error:
            return None

    async def get_download_url(self, storage_path: str, expires_in_seconds: int = 3600) -> str:
        """Generate a pre-signed URL for downloading a file."""
        try:
            # Generate a presigned URL for GET
            from datetime import timedelta
            
            # Convert seconds to timedelta for minio API
            expires = timedelta(seconds=expires_in_seconds)
            
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=storage_path,
                expires=expires,
            )
            
            # Replace internal Docker host with external host for browser access
            # This is a workaround for the URLs that contain minio:9000 which is only accessible inside Docker network
            return f"/api/files/{storage_path.split('/')[-2]}/download"
        except S3Error as e:
            raise ValueError(f"Error generating download URL: {str(e)}")

    async def delete_file(self, storage_path: str) -> bool:
        """Delete a file from MinIO."""
        try:
            self.client.remove_object(self.bucket_name, storage_path)
            return True
        except S3Error:
            return False