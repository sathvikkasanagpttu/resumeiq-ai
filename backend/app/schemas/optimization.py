from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class BulletModification(BaseModel):
    section: str
    original_text: str
    optimized_text: str
    rationale: str
    grounded_evidence: str
    unsupported_elements_removed: List[str] = Field(default_factory=list)
    confidence: float

class ResumeOptimizationResponse(BaseModel):
    match_id: str
    resume_id: str
    job_id: str
    summary_of_changes: str
    truthfulness_guarantee: str = "Strictly grounded in existing candidate profile. No fabrication of metrics or experience."
    modifications: List[BulletModification] = Field(default_factory=list)
    representation_improvements: List[str] = Field(default_factory=list)
    formatting_recommendations: List[str] = Field(default_factory=list)
    estimated_compatibility_gain: float
