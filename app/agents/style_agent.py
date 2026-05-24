import json
from typing import List
from app.agents.base_agent import BaseAgent, CodeContext, Issue
from app.services.llm_client import llm_client
import logging

logger = logging.getLogger(__name__)

class StyleAgent(BaseAgent):
    def get_agent_type(self) -> str:
        return "style"

    async def analyze(self, context: CodeContext) -> List[Issue]:
        logger.info(f"StyleAgent analyzing PR {context.pr_number}...")
        
        system_prompt = """You are an AI Style Code Reviewer.
Your job is to analyze the provided git diff and identify issues related to coding style, naming conventions, formatting, docstrings, imports, and code complexity.
Output your findings ONLY as a JSON object with a key 'issues' containing a list of objects.
Each object must have: file_path (string), line_number (integer or null), severity (must be 'warning' or 'suggestion'), message (string), code_snippet (string), suggestion (string), confidence_score (float between 0.0 and 1.0).
Do not include conversational text, only the JSON. If there are no issues, return {"issues": []}.
"""

        prompt = f"""Review the following pull request diff for style issues.
Repository config: {json.dumps(context.repo_config)}

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
                        float(item.get('confidence_score', 0.7)), 
                        context.similar_patterns
                    )
                    
                    issues.append(Issue(
                        file_path=item['file_path'],
                        line_number=item.get('line_number'),
                        severity=item.get('severity', 'suggestion'),
                        message=item['message'],
                        code_snippet=item.get('code_snippet'),
                        suggestion=item.get('suggestion'),
                        confidence_score=confidence
                    ))
                except (KeyError, ValueError) as e:
                    logger.warning(f"Error parsing style issue: {e}")
                    
            return issues
            
        except Exception as e:
            logger.error(f"StyleAgent analysis failed: {e}")
            return []
