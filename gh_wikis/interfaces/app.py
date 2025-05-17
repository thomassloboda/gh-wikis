"""FastAPI application setup."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from gh_wikis.infrastructure.config import settings
from gh_wikis.infrastructure.db.database import Database
from gh_wikis.interfaces.api.routes import router as api_router
from gh_wikis.interfaces.web.routes import router as web_router

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Initialize database
    db = Database()
    try:
        logger.info("Creating database tables")
        await db.create_tables()
        logger.info("Database tables created")
        yield
    finally:
        logger.info("Shutting down application")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        description="GitHub Wiki exporter application",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add static files
    app.mount(
        "/static", StaticFiles(directory="gh_wikis/interfaces/web/templates/static"), name="static"
    )

    # Include routers
    app.include_router(api_router)
    app.include_router(web_router)

    return app