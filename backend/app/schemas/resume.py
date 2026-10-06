from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.schemas.evidence import EvidenceItemResponse

class SkillExtraction(BaseModel):
    original_text: str
    normalized_skill: str
    category: Optional[str] = "technical"
    source_section: str
    source_evidence: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence_strength: str = Field(..., description="verified, weak, inferred, missing, uncertain")

class CandidateSkillResponse(SkillExtraction):
    id: str
    resume_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CandidateExperienceBase(BaseModel):
    company: str
    role: str
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False
    duration_months: int = 0
    description: Optional[str] = None
    bullet_points: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)

class CandidateExperienceResponse(CandidateExperienceBase):
    id: str
    resume_id: str

    model_config = ConfigDict(from_attributes=True)

class CandidateProjectBase(BaseModel):
    title: str
    role: Optional[str] = None
    description: str
    technologies: List[str] = Field(default_factory=list)
    outcomes: List[str] = Field(default_factory=list)
    url: Optional[str] = None

class CandidateProjectResponse(CandidateProjectBase):
    id: str
    resume_id: str

    model_config = ConfigDict(from_attributes=True)

class CandidateEducationBase(BaseModel):
    institution: str
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    graduation_year: Optional[str] = None
    gpa: Optional[str] = None

class CandidateEducationResponse(CandidateEducationBase):
    id: str
    resume_id: str

    model_config = ConfigDict(from_attributes=True)

class CandidateCertificationBase(BaseModel):
    name: str
    issuing_org: Optional[str] = None
    issue_date: Optional[str] = None
    expiration_date: Optional[str] = None
    credential_id: Optional[str] = None

class CandidateCertificationResponse(CandidateCertificationBase):
    id: str
    resume_id: str

    model_config = ConfigDict(from_attributes=True)

class ResumeSectionResponse(BaseModel):
    id: str
    section_type: str
    title: str
    raw_content: str
    start_index: int
    end_index: int

    model_config = ConfigDict(from_attributes=True)

class ResumeResponse(BaseModel):
    id: str
    user_id: str
    filename: str
    file_type: str
    file_size: int
    is_active: bool
    created_at: datetime
    skills_count: Optional[int] = 0
    experience_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)

class ResumeDetailResponse(ResumeResponse):
    raw_text: str
    sections: List[ResumeSectionResponse] = Field(default_factory=list)
    skills: List[CandidateSkillResponse] = Field(default_factory=list)
    experiences: List[CandidateExperienceResponse] = Field(default_factory=list)
    projects: List[CandidateProjectResponse] = Field(default_factory=list)
    educations: List[CandidateEducationResponse] = Field(default_factory=list)
    certifications: List[CandidateCertificationResponse] = Field(default_factory=list)
    evidence_items: List[EvidenceItemResponse] = Field(default_factory=list)
