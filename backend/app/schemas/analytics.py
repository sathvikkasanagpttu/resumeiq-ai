from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class SkillFrequencyItem(BaseModel):
    skill_name: str
    category: str
    frequency_count: int
    percentage: float
    required_ratio: float  # proportion where it was marked REQUIRED vs PREFERRED

class SeniorityDistributionItem(BaseModel):
    seniority: str
    count: int
    percentage: float

class DomainDistributionItem(BaseModel):
    domain: str
    count: int
    percentage: float

class MarketBenchmarkComparison(BaseModel):
    candidate_skills_in_market: List[str]
    missing_market_critical_skills: List[str]
    candidate_percentile: float
    summary: str

class MarketAnalyticsResponse(BaseModel):
    total_jobs_analyzed: int
    top_skills: List[SkillFrequencyItem]
    seniority_distribution: List[SeniorityDistributionItem]
    domain_distribution: List[DomainDistributionItem]
    candidate_benchmark: Optional[MarketBenchmarkComparison] = None
