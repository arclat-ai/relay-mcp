from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.pipeline import PipelineCreate, PipelineResponse
from app.models.pipeline import Pipeline

router = APIRouter(prefix="/pipelines", tags=["pipelines"])

@router.get("", response_model=List[PipelineResponse])
async def list_pipelines(db: AsyncSession = Depends(get_db)):
    # Auth stub
    return []

@router.post("", response_model=PipelineResponse)
async def create_pipeline(pipeline: PipelineCreate, db: AsyncSession = Depends(get_db)):
    # Auth stub
    pass

@router.get("/{id}", response_model=PipelineResponse)
async def get_pipeline(id: UUID, db: AsyncSession = Depends(get_db)):
    pass

@router.delete("/{id}")
async def delete_pipeline(id: UUID, db: AsyncSession = Depends(get_db)):
    pass
