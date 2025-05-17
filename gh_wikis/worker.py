"""Celery worker entry point."""
from gh_wikis.infrastructure.celery_app import celery_app
from gh_wikis.infrastructure.tasks import wiki_tasks  # noqa