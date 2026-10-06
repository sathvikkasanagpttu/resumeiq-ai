from datetime import datetime
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.wizard import WizardAnswer

class GenerateResumeRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resume_id: str
    mode: Literal["clean_rebuild", "role_targeted", "fresher", "experienced"] = "clean_rebuild"
    target_role: Optional[str] = None
    job_description_text: Optional[str] = None
    template_id: Literal["classic", "modern_minimal", "compact", "fresher"] = "classic"
    page_target: Literal[1, 2] = 1

class DiffReviewAction(BaseModel):
    diff_id: str
    action: Literal["accept", "reject", "edit"]
    edited_text: Optional[str] = None

class ResumeDiffResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    version_id: str
    field_path: str
    original_text: Optional[str] = None
    proposed_text: str
    status: str = "pending"
    edited_text: Optional[str] = None
    source: str = "ai_suggested_pending"
    evidence_ids: List[str] = Field(default_factory=list)
    change_reason: Optional[str] = None
    risk_flag: Optional[str] = None
    created_at: Optional[datetime] = None

class ResumeVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    resume_id: str
    parent_version_id: Optional[str] = None
    version_num: int
    mode: str
    template_id: str
    is_published: bool = False
    ats_loss_score: float = 0.0
    change_summary: Optional[str] = None
    canonical_profile: Dict[str, Any]
    diffs: List[ResumeDiffResponse] = Field(default_factory=list)
    rendered_html: Optional[str] = None
    created_at: Optional[datetime] = None

class WizardAnswerSubmission(BaseModel):
    resume_id: str
    answers: List[WizardAnswer]

class ExternalImportRequest(BaseModel):
    resume_id: str
    platform: Literal["linkedin", "github"]
    raw_text: str

class TrackerItemCreate(BaseModel):
    job_title: str
    company_name: str
    resume_version_id: Optional[str] = None
    target_job_id: Optional[str] = None
    stage: Literal["saved", "applied", "interviewing", "offer", "rejected"] = "saved"
    notes: Optional[str] = None

class TrackerItemUpdate(BaseModel):
    stage: Optional[Literal["saved", "applied", "interviewing", "offer", "rejected"]] = None
    notes: Optional[str] = None
    outcome: Optional[str] = None

class TrackerItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    job_title: str
    company_name: str
    stage: str
    resume_version_id: Optional[str] = None
    target_job_id: Optional[str] = None
    notes: Optional[str] = None
    outcome: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class InterviewPrepGenerateRequest(BaseModel):
    resume_id: str
    target_role: Optional[str] = None

class InterviewPrepQuestion(BaseModel):
    id: str
    question: str
    category: str
    evidence_id: Optional[str] = None
    context_evidence: str
    star_skeleton: Dict[str, str]

class InterviewPrepResponse(BaseModel):
    id: str
    resume_id: str
    target_role: str
    total_questions: int
    questions: List[InterviewPrepQuestion]
