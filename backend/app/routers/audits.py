from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.audit import AuditResponse
from app.schemas.report import ReportResponse

router = APIRouter(tags=["audits"])

@router.post("/audits", response_model=AuditResponse)
async def create_audit(
    pipeline_id: UUID = Form(...),
    input_type: str = Form(...),
    input_raw: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    raise HTTPException(status_code=501, detail="Not implemented")

@router.get("/audits/{id}", response_model=AuditResponse)
async def get_audit(id: UUID, db: AsyncSession = Depends(get_db)):
    raise HTTPException(status_code=501, detail="Not implemented")

@router.get("/audits/{id}/report", response_model=ReportResponse)
async def get_audit_report(id: UUID, db: AsyncSession = Depends(get_db)):
    raise HTTPException(status_code=501, detail="Not implemented")

@router.get("/audits/{id}/report/share")
async def share_report(id: UUID, db: AsyncSession = Depends(get_db)):
    raise HTTPException(status_code=501, detail="Not implemented")

@router.get("/share/{token}", response_model=ReportResponse)
async def get_shared_report(token: str, db: AsyncSession = Depends(get_db)):
    raise HTTPException(status_code=501, detail="Not implemented")
