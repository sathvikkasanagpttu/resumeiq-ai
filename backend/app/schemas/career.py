from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class RoadmapMilestone(BaseModel):
    step_number: int
    title: str
    description: str
    estimated_weeks: int
    learning_resources: List[str] = Field(default_factory=list)
    hands_on_project_to_prove: str
    evidence_to_add_to_resume: str

class SkillLearningPath(BaseModel):
    skill_name: str
    priority_level: str  # immediate, high, medium, elective
    job_market_demand: str  # high, medium, emerging
    effort_estimate_hours: int
    transferable_base: Optional[str] = None
    milestones: List[RoadmapMilestone] = Field(default_factory=list)

class CareerRoadmapResponse(BaseModel):
    match_id: Optional[str] = None
    target_role: str
    current_seniority_level: str
    target_seniority_level: str
    summary_strategy: str
    learning_paths: List[SkillLearningPath] = Field(default_factory=list)
    estimated_total_weeks: int

class JobRecommendationItem(BaseModel):
    job_id: str
    title: str
    company: str
    location: Optional[str]
    work_model: str
    compatibility_score: float
    why_it_matches: str
    strong_matches: List[str]
    potential_gaps: List[str]
    transferable_skills: List[str]
    risk_factors: List[str]
    recommended_strategy: str

class JobRecommendationsResponse(BaseModel):
    resume_id: str
    total_analyzed_jobs: int
    recommendations: List[JobRecommendationItem] = Field(default_factory=list)
