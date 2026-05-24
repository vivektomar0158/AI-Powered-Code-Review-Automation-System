from typing import List, Dict, Any
from collections import defaultdict
from app.agents.base_agent import Issue
import logging

logger = logging.getLogger(__name__)

class SynthesizerAgent:
    def synthesize(self, all_issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine issues, deduplicate, and generate markdown review."""
        logger.info(f"SynthesizerAgent combining {len(all_issues)} total issues.")
        
        # Deduplication using file_path + line_number + basic message similarity
        unique_issues = self._deduplicate(all_issues)
        
        # Sort by severity (critical > warning > suggestion) and then confidence
        severity_order = {"critical": 0, "warning": 1, "suggestion": 2}
        unique_issues.sort(key=lambda x: (
            severity_order.get(x.severity, 3), 
            -x.confidence_score
        ))

        # Generate markdown
        markdown = self._generate_markdown(unique_issues)
        
        return {
            "issues": unique_issues,
            "markdown": markdown,
            "stats": {
                "total": len(unique_issues),
                "critical": sum(1 for i in unique_issues if i.severity == "critical"),
                "warnings": sum(1 for i in unique_issues if i.severity == "warning"),
                "suggestions": sum(1 for i in unique_issues if i.severity == "suggestion")
            }
        }

    def _deduplicate(self, issues: List[Issue]) -> List[Issue]:
        # Simplistic deduplication for MVP: Group by file and line.
        # If multiple agents flag the same line with similar severity, keep the one with higher confidence.
        grouped = defaultdict(list)
        for issue in issues:
            key = f"{issue.file_path}:{issue.line_number}"
            grouped[key].append(issue)
            
        deduplicated = []
        for key, group in grouped.items():
            if len(group) == 1:
                deduplicated.append(group[0])
            else:
                # Keep the one with highest confidence
                best_issue = max(group, key=lambda x: x.confidence_score)
                deduplicated.append(best_issue)
                
        return deduplicated

    def _generate_markdown(self, issues: List[Issue]) -> str:
        if not issues:
            return "## 🤖 AI Code Review\n\n✅ Excellent work! No significant issues found in this diff."
            
        criticals = [i for i in issues if i.severity == "critical"]
        warnings = [i for i in issues if i.severity == "warning"]
        suggestions = [i for i in issues if i.severity == "suggestion"]
        
        md = [f"## 🤖 AI Code Review\n\n**Summary:** {len(issues)} issues found ({len(criticals)} critical, {len(warnings)} warnings, {len(suggestions)} suggestions)\n"]
        
        if criticals:
            md.append("### 🔴 Critical Issues")
            for i in criticals:
                md.append(self._format_issue(i))
                
        if warnings:
            md.append("### ⚠️ Warnings")
            for i in warnings:
                md.append(self._format_issue(i))
                
        if suggestions:
            md.append("### 💡 Suggestions")
            for i in suggestions:
                md.append(self._format_issue(i))
                
        return "\n".join(md)
        
    def _format_issue(self, issue: Issue) -> str:
        loc = f"`{issue.file_path}`"
        if issue.line_number:
            loc += f" (Line {issue.line_number})"
            
        md = f"- **{loc}** [{getattr(issue, 'agent_type', 'System')}]: {issue.message}"
        if issue.suggestion:
            md += f"\n  - *Suggestion*: {issue.suggestion}"
        return md
