import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Match(Base):
    __tablename__ = "matches"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Candidate–Job Compatibility Score (0 - 100)
    compatibility_score = Column(Float, nullable=False, default=0.0)
    
    # 10 Component Signals (each 0 - 100)
    semantic_score = Column(Float, default=0.0)
    lexical_score = Column(Float, default=0.0)
    required_skill_coverage = Column(Float, default=0.0)
    preferred_skill_coverage = Column(Float, default=0.0)
    evidence_strength_score = Column(Float, default=0.0)
    experience_alignment_score = Column(Float, default=0.0)
    seniority_alignment_score = Column(Float, default=0.0)
    domain_alignment_score = Column(Float, default=0.0)
    education_alignment_score = Column(Float, default=0.0)
    preference_alignment_score = Column(Float, default=0.0)
    
    status = Column(String(50), default="completed")  # queued, processing, completed, failed
    calculation_weights = Column(JSON, nullable=False)  # exact weights snapshot used
    explanation_summary = Column(JSON, default=dict)  # structured explanation
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    resume = relationship("Resume", back_populates="matches")
    job = relationship("Job", back_populates="matches")
    components = relationship("MatchComponent", back_populates="match", cascade="all, delete-orphan")
    skill_gaps = relationship("SkillGap", back_populates="match", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="match", cascade="all, delete-orphan")
    generated_documents = relationship("GeneratedDocument", back_populates="match", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="match", cascade="all, delete-orphan")

class MatchComponent(Base):
    __tablename__ = "match_components"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    match_id = Column(String(36), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)
    component_name = Column(String(100), nullable=False)
    weight = Column(Float, nullable=False)
    raw_score = Column(Float, nullable=False)  # 0 - 100
    weighted_score = Column(Float, nullable=False)  # weight * raw_score
    explanation = Column(Text, nullable=False)

    match = relationship("Match", back_populates="components")

class SkillGap(Base):
    __tablename__ = "skill_gaps"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    match_id = Column(String(36), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_name = Column(String(255), nullable=False, index=True)
    job_requirement_id = Column(String(36), ForeignKey("job_requirements.id", ondelete="SET NULL"), nullable=True)
    # Severity: critical, moderate, minor, transferable, representation
    gap_severity = Column(String(50), nullable=False, default="critical")
    candidate_evidence = Column(Text, nullable=True)  # empty or partial snippet
    explanation = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=False)
    confidence = Column(Float, default=0.9)

    match = relationship("Match", back_populates="skill_gaps")
    job_requirement = relationship("JobRequirement", back_populates="skill_gaps")

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    match_id = Column(String(36), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(100), nullable=False)  # resume_opt, skill_acquisition, application_strategy
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(50), default="high")  # high, medium, low
    actionable_steps = Column(JSON, default=list)
    grounded_evidence_citations = Column(JSON, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    match = relationship("Match", back_populates="recommendations")

class GeneratedDocument(Base):
    __tablename__ = "generated_documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    match_id = Column(String(36), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    doc_type = Column(String(50), nullable=False)  # tailored_resume, cover_letter, recruiter_message, interview_qa
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    cited_evidence = Column(JSON, default=list)  # list of exact candidate quotes supporting text
    # verification_status: verified_grounded, partially_verified, flagged_unsupported
    verification_status = Column(String(50), default="verified_grounded")
    confidence_score = Column(Float, default=0.92)
    unsupported_claims_detected = Column(JSON, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    match = relationship("Match", back_populates="generated_documents")
    user = relationship("User", back_populates="generated_documents")

class Application(Base):
    __tablename__ = "applications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    match_id = Column(String(36), ForeignKey("matches.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(50), default="draft")  # draft, applied, interviewing, offered, rejected
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="applications")
    match = relationship("Match", back_populates="applications")
