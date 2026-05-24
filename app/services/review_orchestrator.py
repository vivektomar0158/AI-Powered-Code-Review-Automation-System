import logging
import time
from typing import Dict, Any

from app.services.github_service import github_service
from app.services.diff_parser import DiffParser
from app.graph.review_graph import review_workflow
# from app.services.pattern_matcher import pattern_matcher  # To be implemented
from app.db.session import async_session_maker
from app.models.review import Review
from app.models.comment import Comment

logger = logging.getLogger(__name__)

class ReviewOrchestrator:
    def __init__(self):
        self.diff_parser = DiffParser()

    async def process_pr(self, repo_full_name: str, pr_number: int, event_data: dict) -> bool:
        """
        Main orchestration loop:
        1. Fetch Diff
        2. Parse Diff
        3. Build State
        4. Run Graph
        5. Store Results
        6. Post to GitHub
        """
        start_time = time.time()
        logger.info(f"Starting review orchestration for {repo_full_name}#{pr_number}")
        
        try:
            # 1. Fetch data
            pr_data = await github_service.fetch_pull_request(repo_full_name, pr_number)
            raw_diff = await github_service.fetch_diff(repo_full_name, pr_number)
            
            # 2. Parse diff
            parsed_files = self.diff_parser.parse(raw_diff)
            formatted_diff = self.diff_parser.format_for_llm(parsed_files)
            
            if not formatted_diff.strip():
                logger.info(f"No valid files to review for {repo_full_name}#{pr_number}")
                return True
                
            # 3. Retrieve similar patterns (Mocked for now until Pinecone is implemented)
            # similar_patterns = await pattern_matcher.find_similar(formatted_diff, "python", 1)
            similar_patterns = []

            # 4. Build State
            initial_state = {
                "pr_number": pr_number,
                "repository": repo_full_name,
                "diff_content": formatted_diff,
                "files_changed": len(parsed_files),
                "repo_config": {},  # Would load from .ai-review.yml
                "similar_patterns": similar_patterns,
                "issues": []
            }
            
            # 5. Run Graph
            result_state = await review_workflow.run(initial_state)
            
            final_review = result_state.get("final_review", {})
            issues = final_review.get("issues", [])
            markdown_body = final_review.get("markdown", "No issues found.")
            stats = final_review.get("stats", {})
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # 6. Post to GitHub
            try:
                review_url = await github_service.post_review(repo_full_name, pr_number, markdown_body)
                logger.info(f"Posted review to GitHub: {review_url}")
            except Exception as e:
                logger.error(f"Failed to post to GitHub: {e}")
                # We don't fail the whole process if GitHub post fails, still save to DB
                
            # 7. Store in Database
            await self._store_results(
                repo_full_name=repo_full_name,
                pr_number=pr_number,
                pr_data=pr_data,
                issues=issues,
                stats=stats,
                processing_time_ms=processing_time
            )
            
            logger.info(f"Completed review orchestration for {repo_full_name}#{pr_number} in {processing_time}ms")
            return True
            
        except Exception as e:
            logger.error(f"Review orchestration failed for {repo_full_name}#{pr_number}: {e}", exc_info=True)
            return False

    async def _store_results(self, repo_full_name: str, pr_number: int, pr_data: dict, issues: list, stats: dict, processing_time_ms: int):
        # We need the pull_request_id and repository_id from our DB.
        # This requires querying our DB. In a robust system we'd sync these, 
        # but for simplicity let's assume they are synced or we sync them here.
        
        async with async_session_maker() as session:
            # Mock DB storage logic for MVP orchestration. 
            # Real implementation would look up repository, then pull_request, then insert Review + Comments.
            pass

review_orchestrator = ReviewOrchestrator()
