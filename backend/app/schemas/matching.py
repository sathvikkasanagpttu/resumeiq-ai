from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.core.config import settings

class MatchWeightsConfig(BaseModel):
    weight_required_skills: float = Field(default_factory=lambda: settings.WEIGHT_REQUIRED_SKILLS)
    weight_semantic_fit: float = Field(default_factory=lambda: settings.WEIGHT_SEMANTIC_FIT)
    weight_evidence_strength: float = Field(default_factory=lambda: settings.WEIGHT_EVIDENCE_STRENGTH)
    weight_experience_alignment: float = Field(default_factory=lambda: settings.WEIGHT_EXPERIENCE_ALIGNMENT)
    weight_preferred_skills: float = Field(default_factory=lambda: settings.WEIGHT_PREFERRED_SKILLS)
    weight_seniority_alignment: float = Field(default_factory=lambda: settings.WEIGHT_SENIORITY_ALIGNMENT)
    weight_domain_alignment: float = Field(default_factory=lambda: settings.WEIGHT_DOMAIN_ALIGNMENT)
    weight_education_alignment: float = Field(default_factory=lambda: settings.WEIGHT_EDUCATION_ALIGNMENT)

    @model_validator(mode="after")
    def validate_weights_sum(self) -> "MatchWeightsConfig":
        total = (
            self.weight_required_skills +
            self.weight_semantic_fit +
            self.weight_evidence_strength +
            self.weight_experience_alignment +
            self.weight_preferred_skills +
            self.weight_seniority_alignment +
            self.weight_domain_alignment +
            self.weight_education_alignment
        )
        if round(total, 4) != 1.0:
            raise ValueError(f"Matching weights must sum to 1.0 (got {total:.4f})")
        return self

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
