from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class MatchWeightsConfig(BaseModel):
    weight_required_skills: float = 0.25
    weight_semantic_fit: float = 0.20
    weight_evidence_strength: float = 0.15
    weight_experience_alignment: float = 0.15
    weight_preferred_skills: float = 0.08
    weight_seniority_alignment: float = 0.07
    weight_domain_alignment: float = 0.05
    weight_education_alignment: float = 0.05

class MatchComponentResponse(BaseModel):
    component_name: str
    weight: float
    raw_score: float
    weighted_score: float
    explanation: str

class MatchRequest(BaseModel):
    resume_id: str
    job_id: str
    weights: Optional[MatchWeightsConfig] = None

class EvidenceCitation(BaseModel):
    entity: str
    strength: str
    quote: str
    source_section: str
    explanation: str

class MatchExplanationSummary(BaseModel):
    headline: str
    overall_assessment: str
    top_strengths: List[str]
    critical_concerns: List[str]
    citations: List[EvidenceCitation]
    recommendation_strategy: str

class MatchResponse(BaseModel):
    id: str
    resume_id: str
    job_id: str
    compatibility_score: float = Field(..., description="Candidate-Job Compatibility Score (0-100)")
    semantic_score: float
    lexical_score: float
    required_skill_coverage: float
    preferred_skill_coverage: float
    evidence_strength_score: float
    experience_alignment_score: float
    seniority_alignment_score: float
    domain_alignment_score: float
    education_alignment_score: float
    preference_alignment_score: float
    status: str
    calculation_weights: Dict[str, float]
    components: List[MatchComponentResponse] = Field(default_factory=list)
    explanation_summary: MatchExplanationSummary
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
