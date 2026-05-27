from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class PipelineBase(BaseModel):
    name: str
    description: Optional[str] = None
    framework: str

class PipelineCreate(PipelineBase):
    pass

class PipelineResponse(PipelineBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    
    model_config = {"from_attributes": True}
