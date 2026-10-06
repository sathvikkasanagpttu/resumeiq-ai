from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict

class QualityIssue(BaseModel):
    issue_type: str  # weak_verb, missing_metric, passive_voice, duplicate_bullet, vague_claim, date_conflict, timeline_gap
    severity: str    # critical, warning, suggestion
    message: str
    target_section: str
    line_text: Optional[str] = None
    suggested_fix: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class QualityComponentScore(BaseModel):
    name: str  # structure, clarity, impact_language, evidence_density, keyword_truthfulness, consistency, length, readability
    score: float = Field(..., ge=0.0, le=100.0)
    weight: float
    grade: str  # Excellent, Good, Needs Improvement, Poor
    explanation: str
    issues: List[QualityIssue] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class TimelineAnomaly(BaseModel):
    anomaly_type: str  # overlap, employment_gap, impossible_date, duration_contradiction
    severity: str      # warning, critical
    company_or_entity: str
    dates: str
    description: str
    remediation_hint: str

    model_config = ConfigDict(from_attributes=True)

class TimelineAnalysisResult(BaseModel):
    total_career_months: int
    total_career_years: float
    anomalies: List[TimelineAnomaly] = Field(default_factory=list)
    has_critical_inconsistency: bool = False

    model_config = ConfigDict(from_attributes=True)

class ImpliedSkillSuggestion(BaseModel):
    implied_skill: str
    trigger_text: str
    context_section: str
    rationale: str
    suggested_question: str  # Prompt for Missing-Info Wizard

    model_config = ConfigDict(from_attributes=True)

class ResumeQualityReport(BaseModel):
    resume_id: str
    overall_quality_score: float = Field(..., ge=0.0, le=100.0)
    readiness_tier: str  # Job-Ready, Minor Edits Needed, Significant Gaps
    components: List[QualityComponentScore]
    timeline_analysis: TimelineAnalysisResult
    representation_gaps: List[ImpliedSkillSuggestion]
    top_recommendations: List[str]

    model_config = ConfigDict(from_attributes=True)

class ExternalImportRequest(BaseModel):
    source_type: str  # linkedin, github
    raw_pasted_text: str

class ExternalImportResponse(BaseModel):
    source_type: str
    facts_extracted_count: int
    confirmed_facts: List[Dict[str, Any]]
    message: str

QualityReportResponse = ResumeQualityReport
