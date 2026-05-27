from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class AuditCreateForm(BaseModel):
    pipeline_id: UUID
    input_type: str  # logs | description
    input_raw: Optional[str] = None

class AuditResponse(BaseModel):
    id: UUID
    pipeline_id: UUID
    status: str
    input_type: str
    input_file_url: Optional[str] = None
    input_raw: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}
