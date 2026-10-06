from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class SkillGapResponse(BaseModel):
    id: Optional[str] = None
    skill_name: str
    job_requirement_id: Optional[str] = None
    requirement_text: Optional[str] = None
    # Severity: critical, moderate, minor, transferable, representation
    gap_severity: str = Field(
        ...,
        description="critical (must-have missing), moderate (preferred missing), minor (nice to have), transferable (adjacent skill present), or representation (skill present but poorly articulated/quantified)"
    )
    candidate_evidence: Optional[str] = Field(None, description="Actual quote or 'No explicit evidence found'")
    explanation: str
    recommendation: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    transferable_from: Optional[str] = None

class SkillGapReport(BaseModel):
    match_id: str
    total_gaps: int
    critical_gaps_count: int
    moderate_gaps_count: int
    minor_gaps_count: int
    transferable_skills_count: int
    representation_gaps_count: int
    gaps: List[SkillGapResponse] = Field(default_factory=list)
