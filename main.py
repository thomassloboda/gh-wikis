"""Main entry point for the application."""
import os

import uvicorn
from dotenv import load_dotenv

from gh_wikis.infrastructure.config import settings
from gh_wikis.interfaces.app import create_app

# Load environment variables
load_dotenv()

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug",
    )