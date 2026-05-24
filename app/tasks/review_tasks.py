import asyncio
import logging
from app.tasks.celery_app import celery_app
from app.services.review_orchestrator import review_orchestrator

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3)
def process_pr_review(self, repo_full_name: str, pr_number: int, event_data: dict):
    """
    Celery task to process a PR review asynchronously.
    """
    logger.info(f"Celery task started for {repo_full_name}#{pr_number}")
    try:
        # Since review_orchestrator uses async/await, we need an event loop
        loop = asyncio.get_event_loop()
        success = loop.run_until_complete(
            review_orchestrator.process_pr(repo_full_name, pr_number, event_data)
        )
        if not success:
            logger.warning(f"Review orchestrator returned False for {repo_full_name}#{pr_number}")
    except Exception as exc:
        logger.error(f"Error processing PR review task: {exc}")
        # Exponential backoff for retries: 60s, 120s, 240s
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
