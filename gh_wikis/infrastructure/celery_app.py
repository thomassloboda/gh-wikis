"""Celery application configuration."""
from celery import Celery

from gh_wikis.infrastructure.config import settings

celery_app = Celery(
    "gh-wikis",
    broker=settings.broker_url,
    backend=settings.broker_url,
)

celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.task_track_started = True
celery_app.conf.task_routes = {
    "gh_wikis.infrastructure.tasks.wiki_tasks.*": {"queue": "wiki_tasks"},
}