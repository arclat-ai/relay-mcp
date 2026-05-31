from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.audit import AuditResponse
from app.schemas.report import ReportResponse
from app.engine.engine import AuditEngine

router = APIRouter(tags=["audits"])

@router.post("/audits/quick")
async def quick_audit(
    input_type: str = Form(...),
    input_raw: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
) -> Dict[str, Any]:
    """Run the audit engine directly and return results without persisting to DB."""
    engine = AuditEngine()

    if input_type == "logs":
        if file is not None:
            raw = (await file.read()).decode("utf-8")
        elif input_raw:
            raw = input_raw
        else:
            raise HTTPException(status_code=422, detail="Provide a file or input_raw for log audits")
        result = engine.run("logs", raw)
    elif input_type == "description":
        if not input_raw:
            raise HTTPException(status_code=422, detail="Provide input_raw for description audits")
        result = engine.run("description", input_raw)
    else:
        raise HTTPException(status_code=422, detail="input_type must be 'logs' or 'description'")

    return result.to_dict()

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
