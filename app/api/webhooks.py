import logging
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Header
from typing import Optional

from app.core.security import verify_webhook_signature
from app.core.config import settings
from app.services.review_orchestrator import review_orchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])

@router.post("/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: Optional[str] = Header(None),
    x_github_event: Optional[str] = Header(None),
):
    """Handle GitHub App Webhooks."""
    # Read raw body FIRST before any parsing
    raw_body = await request.body()
    
    logger.info(f"Received GitHub webhook: event={x_github_event}, signature_present={bool(x_hub_signature_256)}")
    logger.debug(f"Raw body preview: {raw_body[:200]}")

    # Verify signature
    if not verify_webhook_signature(raw_body, x_hub_signature_256, settings.GITHUB_WEBHOOK_SECRET):
        if settings.GITHUB_WEBHOOK_SECRET == "generate-with-openssl-rand-hex-32":
            logger.warning("Using default dummy webhook secret — skipping signature validation.")
        else:
            logger.error(f"Webhook signature mismatch! header={x_hub_signature_256}")
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Parse JSON manually (since we already consumed raw_body)
    import json
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse webhook JSON: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    action = payload.get("action", "")
    event_type = x_github_event or ""
    
    logger.info(f"Webhook event={event_type} action={action}")

    # Handle pull_request events
    if event_type == "pull_request" and action in ["opened", "synchronize", "reopened", "ready_for_review"]:
        pr = payload.get("pull_request", {})
        repo = payload.get("repository", {})
        
        pr_number = pr.get("number")
        repo_full_name = repo.get("full_name")
        
        if not pr_number or not repo_full_name:
            logger.error("Missing pr_number or repo_full_name in payload")
            raise HTTPException(status_code=400, detail="Missing PR number or repo name")

        logger.info(f"Queueing review for {repo_full_name}#{pr_number}")
        
        background_tasks.add_task(
            review_orchestrator.process_pr,
            repo_full_name,
            pr_number,
            payload
        )
        
        return {"status": "queued", "message": f"Review initiated for {repo_full_name}#{pr_number}"}

    logger.info(f"Ignoring event={event_type} action={action}")
    return {"status": "ignored", "message": f"Event {event_type}.{action} not handled"}
