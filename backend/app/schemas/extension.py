from datetime import datetime
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

# ==========================================
# PAIRING & AUTH
# ==========================================

class ExtensionPairRequest(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    pairing_code: Optional[str] = None
    device_name: str = "Chrome Extension"
    device_id: Optional[str] = None

class ExtensionPairResponse(BaseModel):
    extension_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in_seconds: int
    user_id: str
    user_email: str
    user_name: str
    device_id: str
    paired_at: str
    user: Optional[Dict[str, Any]] = None

class TokenRefreshRequest(BaseModel):
    refresh_token: str
    device_id: str

# ==========================================
# JD CAPTURE & PROVENANCE
# ==========================================

class JDCaptureRequest(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    work_model: Optional[str] = "remote"
    salary_text: Optional[str] = None
    description_text: str = Field(..., min_length=20)
    source_url: Optional[str] = None
    capture_method: Literal["selection", "site_adapter", "json_ld", "readability", "clipboard"] = "site_adapter"
    capture_confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    site_domain: Optional[str] = None

class JDCaptureResponse(BaseModel):
    jd_id: str
    content_hash: str
    title: str
    company: str
    location: Optional[str] = None
    is_cached: bool = False
    is_valid_job: bool = True
    requirements_count: int
    skills_count: int
    warnings: List[str] = Field(default_factory=list)
    capture_method: str
    capture_confidence: float

# ==========================================
# SECTION E MATCH RESULT CONTRACT
# ==========================================

class MatchedSkillEvidence(BaseModel):
    text: str
    section: str
    strength: str

class MatchedSkillItem(BaseModel):
    skill: str
    requirement_type: Literal["required", "preferred", "responsibility"] = "required"
    evidence: List[MatchedSkillEvidence] = Field(default_factory=list)

class TransferableSkillItem(BaseModel):
    skill: str
    transferable_from: str
    affinity: float
    evidence: str

class GapItem(BaseModel):
    skill: str
    severity: Literal["critical", "moderate", "minor", "transferable", "representation"]
    type: Literal["missing", "representation", "transferable"]
    recommendation: str
    confidence: float

class MatchComponentDetail(BaseModel):
    score: float
    weight: float
    explanation: str

class QuickMatchRequest(BaseModel):
    resume_id: str
    jd_id: Optional[str] = None
    job_id: Optional[str] = None
    raw_jd_text: Optional[str] = None
    job_data: Optional[Dict[str, Any]] = None
    title: Optional[str] = None
    company: Optional[str] = None
    source_url: Optional[str] = None
    capture_method: Optional[str] = "selection"
    capture_confidence: Optional[float] = 0.95
    verdict_thresholds: Optional[Dict[str, int]] = Field(
        default_factory=lambda: {"strong": 80, "good": 65, "partial": 45}
    )

class QuickMatchResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    schema_version: str = "1.0"
    match_id: str
    resume_id: str
    jd_id: str
    verdict: Literal["strong_match", "good_match", "partial_match", "weak_match"]
    verdict_thresholds: Dict[str, int]
    compatibility_score: int
    components: Dict[str, MatchComponentDetail]
    matched_skills: List[MatchedSkillItem] = Field(default_factory=list)
    transferable: List[TransferableSkillItem] = Field(default_factory=list)
    gaps: List[GapItem] = Field(default_factory=list)
    explanation: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    capture: Dict[str, Any]
    timings_ms: Dict[str, float]

# ==========================================
# RESUME PICKER & VERSIONS
# ==========================================

class ResumeVersionSummary(BaseModel):
    version_id: str
    version_num: int
    mode: str
    template_id: str
    ats_loss_score: float
    is_published: bool
    created_at: Optional[datetime] = None

class ExtensionResumeItem(BaseModel):
    id: str
    filename: str
    skills_count: int
    experience_count: int
    created_at: Optional[datetime] = None
    versions: List[ResumeVersionSummary] = Field(default_factory=list)

# ==========================================
# EXTENSION ACTIONS
# ==========================================

class ExtensionActionRequest(BaseModel):
    match_id: Optional[str] = None
    resume_id: Optional[str] = None
    job_id: Optional[str] = None
    action_type: Literal["tailor", "cover_letter", "recruiter_message"]
    target_platform: Optional[str] = None

class ExtensionActionResponse(BaseModel):
    action_type: str
    status: str
    title: str
    content: str
    cited_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    unsupported_rejected: List[str] = Field(default_factory=list)
    confidence_score: float

class ExtensionTrackerSaveRequest(BaseModel):
    match_id: Optional[str] = None
    job_id: Optional[str] = None
    stage: Optional[str] = "saved"
    status: Optional[str] = None
    notes: Optional[str] = None

# ==========================================
# COMPARE MODE
# ==========================================

class CompareRequest(BaseModel):
    jd_id: Optional[str] = None
    job_id: Optional[str] = None
    raw_jd_text: Optional[str] = None
    job_data: Optional[Dict[str, Any]] = None
    title: Optional[str] = None
    company: Optional[str] = None
    resume_ids: List[str] = Field(..., min_length=2, max_length=4)

class CompareItem(BaseModel):
    resume_id: str
    resume_name: str
    compatibility_score: int
    verdict: str
    top_strengths: List[str]
    critical_gaps_count: int

class CompareResponse(BaseModel):
    winning_resume_id: str
    winning_resume_name: str
    winning_score: int
    recommendation_reason: str
    comparisons: List[CompareItem]
