import json
from typing import List
from app.agents.base_agent import BaseAgent, CodeContext, Issue
from app.services.llm_client import llm_client
import logging

logger = logging.getLogger(__name__)

class SecurityAgent(BaseAgent):
    def get_agent_type(self) -> str:
        return "security"

    async def analyze(self, context: CodeContext) -> List[Issue]:
        logger.info(f"SecurityAgent analyzing PR {context.pr_number}...")
        
        system_prompt = """You are an AI Security Code Reviewer.
Your job is to deeply analyze the provided git diff for security vulnerabilities. Look for:
- SQL Injection, XSS, CSRF
- Hardcoded secrets, API keys, or credentials
- Insecure direct object references (IDOR)
- Authentication and authorization bypasses
- Path traversal
- Insecure cryptography or hashing
Output your findings ONLY as a JSON object with a key 'issues' containing a list of objects.
Each object must have: file_path, line_number, severity ('critical' or 'warning'), message, code_snippet, suggestion, confidence_score (float).
If there are no issues, return {"issues": []}.
"""

        prompt = f"""Review the following pull request diff for security vulnerabilities.

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
                        severity=item.get('severity', 'critical'),
                        message=item['message'],
                        code_snippet=item.get('code_snippet'),
                        suggestion=item.get('suggestion'),
                        confidence_score=confidence
                    ))
                except (KeyError, ValueError) as e:
                    logger.warning(f"Error parsing security issue: {e}")
                    
            return issues
            
        except Exception as e:
            logger.error(f"SecurityAgent analysis failed: {e}")
            return []
