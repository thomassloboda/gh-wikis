"""Application configuration."""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Application settings
    app_name: str = "gh-wikis"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False

    # Database settings
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "gh_wikis"
    postgres_user: str = "gh_wikis"
    postgres_password: str = Field(..., repr=False)

    # MinIO settings
    minio_host: str = "localhost"
    minio_port: int = 9000
    minio_root_user: str = Field(default="minioadmin", repr=False)
    minio_root_password: str = Field(..., repr=False)
    minio_bucket_name: str = "gh-wikis"

    # GitHub API settings
    github_token: str = Field(default="", repr=False)

    # Celery settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    broker_url: str = Field(default="redis://localhost:6379/0", repr=False)

    # Model configuration
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def __init__(self, **data):
        """Override init to set calculated values."""
        super().__init__(**data)

    @property
    def database_url(self) -> str:
        """Get the database URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        """Get the database URL for synchronous connections (used by Alembic)."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()  # type: ignore