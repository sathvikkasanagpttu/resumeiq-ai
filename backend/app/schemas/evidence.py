from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class EvidenceItemBase(BaseModel):
    entity_type: str  # skill, project, experience, education, certification
    entity_name: str
    context_snippet: str
    source_section: str
    evidence_strength: str = Field(
        ...,
        description="verified (strong action+metric), weak (mention only), inferred (transferable), missing, or uncertain"
    )
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    action_verb: Optional[str] = None
    quantified_impact: Optional[str] = None
    metadata_info: Dict[str, Any] = Field(default_factory=dict)

class EvidenceItemResponse(EvidenceItemBase):
    id: str
    resume_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class VerificationClaim(BaseModel):
    claim: str
    target_entity: str
    confidence: float
    evidence_strength: str
    status: str  # supported, partially_supported, uncertain, unsupported, missing
    cited_evidence: Optional[str] = None
    reason: str
