import logging
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task
def compute_daily_metrics(repo_id: int = None):
    """
    Periodic task to compute analytics and store them.
    If repo_id is provided, compute for that repo only.
    Otherwise, compute for all active repos.
    """
    logger.info(f"Computing daily metrics for repo_id={repo_id}")
    # MVP: placeholder
    pass
