import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)  # skill, project, experience, education, certification
    entity_name = Column(String(255), nullable=False, index=True)
    context_snippet = Column(Text, nullable=False)  # exact quote from resume
    source_section = Column(String(100), nullable=False)  # experience, projects, summary, skills
    # evidence_strength: verified, weak, inferred, missing, uncertain
    evidence_strength = Column(String(50), nullable=False, default="verified")
    confidence_score = Column(Float, default=0.85)  # 0.0 - 1.0
    action_verb = Column(String(100), nullable=True)  # e.g. "built", "architected", "managed"
    quantified_impact = Column(String(255), nullable=True)  # e.g. "reduced latency by 40%"
    metadata_info = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    resume = relationship("Resume", back_populates="evidence_items")
