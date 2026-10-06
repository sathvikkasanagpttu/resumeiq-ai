from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class JobCreate(BaseModel):
    title: str
    company: str
    description: str
    location: Optional[str] = "Remote"
    work_model: Optional[str] = "remote"  # remote, hybrid, onsite
    seniority: Optional[str] = "mid"
    experience_years_min: Optional[float] = 0.0
    experience_years_max: Optional[float] = None

class JobRequirementBase(BaseModel):
    requirement_text: str
    category: str = Field(
        ...,
        description="REQUIRED, PREFERRED, RESPONSIBILITY, QUALIFICATION, EXPERIENCE, DOMAIN, BEHAVIORAL, LOCATION"
    )
    importance_weight: float = Field(..., ge=0.0, le=1.0)
    normalized_entities: List[str] = Field(default_factory=list)

class JobRequirementResponse(JobRequirementBase):
    id: str
    job_id: str

    model_config = ConfigDict(from_attributes=True)

class JobSkillBase(BaseModel):
    skill_name: str
    normalized_skill: str
    is_required: bool = True
    importance_weight: float = 1.0
    context_snippet: Optional[str] = None

class JobSkillResponse(JobSkillBase):
    id: str
    job_id: str

    model_config = ConfigDict(from_attributes=True)

class JobResponse(BaseModel):
    id: str
    user_id: str
    title: str
    company: str
    location: Optional[str]
    work_model: str
    seniority: str
    experience_years_min: float
    is_active: bool
    created_at: datetime
    requirements_count: Optional[int] = 0
    skills_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)

class JobDetailResponse(JobResponse):
    description: str
    raw_text: str
    requirements: List[JobRequirementResponse] = Field(default_factory=list)
    skills: List[JobSkillResponse] = Field(default_factory=list)
