from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

class RecommendationResponse(BaseModel):
    id: UUID
    title: str
    explanation: str
    code_before: Optional[str] = None
    code_after: Optional[str] = None
    effort: str
    impact: str
    
    model_config = {"from_attributes": True}

class BottleneckResponse(BaseModel):
    id: UUID
    type: str
    severity: str
    title: str
    description: str
    time_lost_ms: int
    location: Optional[str] = None
    rank: int
    recommendation: Optional[RecommendationResponse] = None
    
    model_config = {"from_attributes": True}

class AuditSummaryResponse(BaseModel):
    id: UUID
    total_bottlenecks: int
    estimated_improvement_pct: int
    top_issue: str
    report_html: str
    share_token: str
    
    model_config = {"from_attributes": True}

class ReportResponse(BaseModel):
    audit_id: UUID
    summary: AuditSummaryResponse
    bottlenecks: List[BottleneckResponse]
