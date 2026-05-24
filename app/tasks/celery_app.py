from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "ai_code_reviewer",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.review_tasks", "app.tasks.analytics_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "app.tasks.review_tasks.*": {"queue": "reviews"},
        "app.tasks.analytics_tasks.*": {"queue": "analytics"},
    },
    task_time_limit=settings.REVIEW_TIMEOUT_SECONDS + 60,
    task_soft_time_limit=settings.REVIEW_TIMEOUT_SECONDS
)
