from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import uuid

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bottleneck_id = Column(UUID(as_uuid=True), ForeignKey("bottlenecks.id"))
    title = Column(String, nullable=False)
    explanation = Column(String, nullable=False)
    code_before = Column(String)
    code_after = Column(String)
    effort = Column(String)
    impact = Column(String)
