from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class CommentResponse(BaseModel):
    id: int
    file_path: Optional[str]
    line_number: Optional[int]
    agent_type: str
    severity: str
    message: str
    code_snippet: Optional[str]
    suggestion: Optional[str]
    accepted: Optional[bool]
    confidence_score: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True

class ReviewResponse(BaseModel):
    id: int
    pull_request_id: int
    status: str
    total_issues: int
    critical_issues: int
    warnings: int
    suggestions: int
    processing_time_ms: Optional[int]
    cost_usd: Optional[float]
    agent_versions: Optional[Dict[str, Any]]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class ReviewListResponse(BaseModel):
    reviews: List[ReviewResponse]
    total: int

class AgentPerformance(BaseModel):
    agent_type: str
    total_issues_raised: int
    critical_issues: int
    acceptance_rate: float
    avg_confidence_score: float

class AnalyticsResponse(BaseModel):
    total_reviews: int
    avg_processing_time_ms: float
    total_cost_usd: float
    issues_by_severity: Dict[str, int]
    agent_performance: List[AgentPerformance]
