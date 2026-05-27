from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class UserBase(BaseModel):
    email: str
    name: Optional[str] = None
    company: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: UUID
    plan: str
    created_at: datetime
    
    model_config = {"from_attributes": True}
    
class UserUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
