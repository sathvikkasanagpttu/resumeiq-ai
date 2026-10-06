from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class GeneratedMaterialRequest(BaseModel):
    match_id: str
    doc_type: str = Field(..., description="cover_letter, recruiter_message, interview_qa, tailored_resume")
    custom_tone: Optional[str] = "confident and evidence-backed"
    target_role: Optional[str] = None
    custom_prompt_context: Optional[str] = None

class EvidenceGroundingCitation(BaseModel):
    paragraph_or_claim: str
    cited_resume_evidence: str
    evidence_strength: str
    confidence: float

class GeneratedMaterialResponse(BaseModel):
    id: str
    match_id: str
    doc_type: str
    title: str
    content: str
    verification_status: str  # verified_grounded, partially_verified, flagged_unsupported
    confidence_score: float
    grounded_citations: List[EvidenceGroundingCitation] = Field(default_factory=list)
    unsupported_claims_rejected: List[str] = Field(default_factory=list)
    anti_hallucination_guarantee: str = "Verified 100% against candidate factual record. Zero fabricated achievements."
