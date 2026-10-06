import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Float, Integer, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    raw_text = Column(Text, nullable=False)
    location = Column(String(255), nullable=True)
    work_model = Column(String(50), default="remote")  # remote, hybrid, onsite
    seniority = Column(String(50), default="mid")  # entry, mid, senior, lead, principal, executive
    experience_years_min = Column(Float, default=0.0)
    experience_years_max = Column(Float, nullable=True)
    parsed_data = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="jobs")
    versions = relationship("JobVersion", back_populates="job", cascade="all, delete-orphan")
    requirements = relationship("JobRequirement", back_populates="job", cascade="all, delete-orphan")
    skills = relationship("JobSkill", back_populates="job", cascade="all, delete-orphan")
    matches = relationship("Match", back_populates="job", cascade="all, delete-orphan")

class JobVersion(Base):
    __tablename__ = "job_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    version_num = Column(Integer, default=1)
    change_summary = Column(Text, nullable=True)
    content_snapshot = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    job = relationship("Job", back_populates="versions")

class JobRequirement(Base):
    __tablename__ = "job_requirements"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    requirement_text = Column(Text, nullable=False)
    # Categories: REQUIRED, PREFERRED, RESPONSIBILITY, QUALIFICATION, EXPERIENCE, DOMAIN, BEHAVIORAL, LOCATION
    category = Column(String(50), nullable=False, default="REQUIRED", index=True)
    importance_weight = Column(Float, default=1.0)  # 0.1 - 1.0
    normalized_entities = Column(JSON, default=list)  # extracted entities or skills

    job = relationship("Job", back_populates="requirements")
    skill_gaps = relationship("SkillGap", back_populates="job_requirement")

class JobSkill(Base):
    __tablename__ = "job_skills"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_name = Column(String(255), nullable=False)
    normalized_skill = Column(String(255), nullable=False, index=True)
    is_required = Column(Boolean, default=True)
    importance_weight = Column(Float, default=1.0)
    context_snippet = Column(Text, nullable=True)

    job = relationship("Job", back_populates="skills")
