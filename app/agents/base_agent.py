from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class Issue(BaseModel):
    file_path: str
    line_number: Optional[int] = None
    severity: str  # critical, warning, suggestion
    message: str
    code_snippet: Optional[str] = None
    suggestion: Optional[str] = None
    confidence_score: float = 0.7
    agent_type: str = "unknown"   # ← added field

class CodeContext(BaseModel):
    pr_number: int
    repository: str
    diff_content: str
    files_changed: int
    similar_patterns: List[Dict[str, Any]] = []
    repo_config: Dict[str, Any] = {}

class BaseAgent(ABC):
    @abstractmethod
    async def analyze(self, context: CodeContext) -> List[Issue]:
        pass
        
    @abstractmethod
    def get_agent_type(self) -> str:
        pass
        
    def calculate_confidence(self, base_confidence: float, similar_patterns: List[Dict[str, Any]]) -> float:
        if not similar_patterns:
            return base_confidence
        boost = sum(0.05 for p in similar_patterns if p.get("positive_votes", 0) > 0)
        return min(0.99, base_confidence + boost)
