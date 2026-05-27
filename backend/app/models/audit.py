from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import uuid

class Audit(Base):
    __tablename__ = "audits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey("pipelines.id"))
    status = Column(String, default="pending")
    input_type = Column(String)
    input_file_url = Column(String, nullable=True)
    input_raw = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

class AuditSummary(Base):
    __tablename__ = "audit_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audit_id = Column(UUID(as_uuid=True), ForeignKey("audits.id"), unique=True)
    total_bottlenecks = Column(Integer)
    estimated_improvement_pct = Column(Integer)
    top_issue = Column(String)
    report_html = Column(String)
    share_token = Column(String, unique=True)
