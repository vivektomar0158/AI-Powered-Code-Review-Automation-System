import logging
from typing import List

logger = logging.getLogger(__name__)

class FeedbackDetector:
    """
    Detects if a developer accepted or rejected an AI suggestion by analyzing
    subsequent commits on the same PR.
    """
    
    def detect_feedback(self, previous_comments: List[dict], new_diff: str) -> None:
        """
        MVP implementation: simple string matching.
        If the suggested code snippet appears in the new diff's additions,
        it's considered accepted.
        """
        for comment in previous_comments:
            if not comment.get("suggestion"):
                continue
                
            suggestion = comment["suggestion"].strip()
            if not suggestion:
                continue
                
            # Basic matching logic: is the exact suggestion text added in the new diff?
            # A real implementation would parse ASTs or use fuzzier diff matching.
            if f"+{suggestion}" in new_diff.replace(" ", ""):
                logger.info(f"Detected accepted suggestion for comment {comment.get('id')}")
                # Trigger pattern vote update...
                # pattern_matcher.update_votes(vector_id, accepted=True)
                
feedback_detector = FeedbackDetector()
