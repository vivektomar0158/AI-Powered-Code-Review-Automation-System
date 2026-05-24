import json
from typing import List
from app.agents.base_agent import BaseAgent, CodeContext, Issue
from app.services.llm_client import llm_client
import logging

logger = logging.getLogger(__name__)

class BugAgent(BaseAgent):
    def get_agent_type(self) -> str:
        return "bug"

    async def analyze(self, context: CodeContext) -> List[Issue]:
        logger.info(f"BugAgent analyzing PR {context.pr_number}...")
        
        system_prompt = """You are an AI Bug-Hunter Code Reviewer.
Your job is to identify logical bugs and runtime errors in the provided git diff. Look for:
- Null/None reference access
- Off-by-one errors
- Race conditions or concurrency bugs
- Missing or improper error handling
- Type mismatches and improper casts
- Edge cases not handled
Output your findings ONLY as a JSON object with a key 'issues' containing a list of objects.
Each object must have: file_path, line_number, severity ('critical', 'warning', or 'suggestion'), message, code_snippet, suggestion, confidence_score (float).
If there are no issues, return {"issues": []}.
"""

        prompt = f"""Review the following pull request diff for bugs.

Diff:
```diff
{context.diff_content}
```
"""
        try:
            result = await llm_client.analyze_code(prompt, system_prompt)
            if not result or 'issues' not in result:
                return []
                
            issues = []
            for item in result.get('issues', []):
                try:
                    confidence = self.calculate_confidence(
                        float(item.get('confidence_score', 0.8)), 
                        context.similar_patterns
                    )
                    
                    issues.append(Issue(
                        file_path=item['file_path'],
                        line_number=item.get('line_number'),
                        severity=item.get('severity', 'warning'),
                        message=item['message'],
                        code_snippet=item.get('code_snippet'),
                        suggestion=item.get('suggestion'),
                        confidence_score=confidence
                    ))
                except (KeyError, ValueError) as e:
                    logger.warning(f"Error parsing bug issue: {e}")
                    
            return issues
            
        except Exception as e:
            logger.error(f"BugAgent analysis failed: {e}")
            return []
