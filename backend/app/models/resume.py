import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Float, Integer, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf, docx, txt
    file_size = Column(Integer, nullable=False)
    raw_text = Column(Text, nullable=False)
    parsed_data = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="resumes")
    versions = relationship("ResumeVersion", back_populates="resume", cascade="all, delete-orphan")
    sections = relationship("ResumeSection", back_populates="resume", cascade="all, delete-orphan")
    skills = relationship("CandidateSkill", back_populates="resume", cascade="all, delete-orphan")
    experiences = relationship("CandidateExperience", back_populates="resume", cascade="all, delete-orphan")
    projects = relationship("CandidateProject", back_populates="resume", cascade="all, delete-orphan")
    educations = relationship("CandidateEducation", back_populates="resume", cascade="all, delete-orphan")
    certifications = relationship("CandidateCertification", back_populates="resume", cascade="all, delete-orphan")
    evidence_items = relationship("EvidenceItem", back_populates="resume", cascade="all, delete-orphan")
    matches = relationship("Match", back_populates="resume", cascade="all, delete-orphan")

class ResumeVersion(Base):
    __tablename__ = "resume_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    version_num = Column(Integer, nullable=False, default=1)
    change_summary = Column(Text, nullable=True)
    content_snapshot = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    resume = relationship("Resume", back_populates="versions")

class ResumeSection(Base):
    __tablename__ = "resume_sections"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    section_type = Column(String(50), nullable=False)  # contact, summary, experience, education, skills, projects, certifications, etc.
    title = Column(String(100), nullable=False)
    raw_content = Column(Text, nullable=False)
    start_index = Column(Integer, default=0)
    end_index = Column(Integer, default=0)

    resume = relationship("Resume", back_populates="sections")

class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    original_text = Column(String(255), nullable=False)
    normalized_skill = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=True)  # language, framework, database, cloud, ml, devops, soft_skill
    source_section = Column(String(100), nullable=True)
    source_evidence = Column(Text, nullable=False)  # exact quote or sentence demonstrating skill
    confidence = Column(Float, default=0.8)  # 0.0 - 1.0
    evidence_strength = Column(String(50), default="verified")  # verified, weak, inferred, missing, uncertain
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    resume = relationship("Resume", back_populates="skills")

class CandidateExperience(Base):
    __tablename__ = "candidate_experience"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    company = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    is_current = Column(Boolean, default=False)
    duration_months = Column(Integer, default=0)
    description = Column(Text, nullable=True)
    bullet_points = Column(JSON, default=list)  # list of bullet strings
    technologies = Column(JSON, default=list)  # list of tech strings

    resume = relationship("Resume", back_populates="experiences")

class CandidateProject(Base):
    __tablename__ = "candidate_projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    role = Column(String(255), nullable=True)
    description = Column(Text, nullable=False)
    technologies = Column(JSON, default=list)
    outcomes = Column(JSON, default=list)  # verified metrics/outcomes
    url = Column(String(500), nullable=True)

    resume = relationship("Resume", back_populates="projects")

class CandidateEducation(Base):
    __tablename__ = "candidate_education"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    institution = Column(String(255), nullable=False)
    degree = Column(String(255), nullable=True)
    field_of_study = Column(String(255), nullable=True)
    graduation_year = Column(String(20), nullable=True)
    gpa = Column(String(20), nullable=True)

    resume = relationship("Resume", back_populates="educations")

class CandidateCertification(Base):
    __tablename__ = "candidate_certifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    issuing_org = Column(String(255), nullable=True)
    issue_date = Column(String(50), nullable=True)
    expiration_date = Column(String(50), nullable=True)
    credential_id = Column(String(100), nullable=True)

    resume = relationship("Resume", back_populates="certifications")
