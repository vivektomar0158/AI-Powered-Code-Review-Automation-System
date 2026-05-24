from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Import all models here so Alembic can find them easily
from app.models.repository import Repository
from app.models.pull_request import PullRequest
from app.models.review import Review
from app.models.comment import Comment
from app.models.pattern import Pattern
from app.models.webhook_event import WebhookEvent

__all__ = [
    "Base",
    "Repository",
    "PullRequest",
    "Review",
    "Comment",
    "Pattern",
    "WebhookEvent"
]
