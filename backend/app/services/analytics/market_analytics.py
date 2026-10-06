from typing import List, Dict, Any, Optional
from collections import Counter
from sqlalchemy.orm import Session
from app.models.job import Job, JobSkill, JobRequirement
from app.models.resume import Resume
from app.schemas.analytics import (
    SkillFrequencyItem, SeniorityDistributionItem, DomainDistributionItem,
    MarketBenchmarkComparison, MarketAnalyticsResponse
)

class MarketAnalyticsEngine:
    @classmethod
    def analyze_market(
        cls,
        db: Session,
        candidate_resume: Optional[Resume] = None
    ) -> MarketAnalyticsResponse:
        jobs = db.query(Job).filter(Job.is_active == True).all()
        total_jobs = max(len(jobs), 1)

        # 1. Skill Frequency & Required Ratio
        skills_counter: Counter = Counter()
        required_counter: Counter = Counter()
        category_map: Dict[str, str] = {}

        for job in jobs:
            for sk in job.skills:
                norm = sk.normalized_skill
                skills_counter[norm] += 1
                if sk.is_required:
                    required_counter[norm] += 1
                category_map[norm] = "technical"

        top_skills: List[SkillFrequencyItem] = []
        for skill_name, count in skills_counter.most_common(12):
            req_ratio = required_counter[skill_name] / max(count, 1)
            top_skills.append(SkillFrequencyItem(
                skill_name=skill_name,
                category=category_map.get(skill_name, "technical"),
                frequency_count=count,
                percentage=round((count / total_jobs) * 100, 1),
                required_ratio=round(req_ratio, 2)
            ))

        # 2. Seniority Distribution
        seniority_counter: Counter = Counter()
        for j in jobs:
            seniority_counter[j.seniority.title()] += 1

        seniority_dist = [
            SeniorityDistributionItem(
                seniority=sen,
                count=cnt,
                percentage=round((cnt / total_jobs) * 100, 1)
            )
            for sen, cnt in seniority_counter.items()
        ]

        # 3. Domain Distribution
        domain_counter: Counter = Counter()
        for j in jobs:
            # Check requirements for domain tags
            for req in j.requirements:
                if req.category == "DOMAIN":
                    for ent in req.normalized_entities:
                        domain_counter[ent] += 1
            if not domain_counter:
                domain_counter["Cloud & Backend"] += 1
                domain_counter["Data & AI"] += 1

        domain_dist = [
            DomainDistributionItem(
                domain=dom,
                count=cnt,
                percentage=round((cnt / max(sum(domain_counter.values()), 1)) * 100, 1)
            )
            for dom, cnt in domain_counter.most_common(6)
        ]

        # 4. Candidate Benchmark Comparison
        benchmark: Optional[MarketBenchmarkComparison] = None
        if candidate_resume:
            cand_skills = set(s.normalized_skill.lower() for s in candidate_resume.skills)
            market_top = [s.skill_name for s in top_skills[:8]]
            
            matched_in_market = [s for s in market_top if s.lower() in cand_skills]
            missing_in_market = [s for s in market_top if s.lower() not in cand_skills]
            percentile = round((len(matched_in_market) / max(len(market_top), 1)) * 100, 1)

            benchmark = MarketBenchmarkComparison(
                candidate_skills_in_market=matched_in_market,
                missing_market_critical_skills=missing_in_market,
                candidate_percentile=percentile,
                summary=(
                    f"Candidate possesses {len(matched_in_market)} of the top {len(market_top)} most requested "
                    f"market skills ({percentile}% market coverage)."
                )
            )

        return MarketAnalyticsResponse(
            total_jobs_analyzed=len(jobs),
            top_skills=top_skills,
            seniority_distribution=seniority_dist,
            domain_distribution=domain_dist,
            candidate_benchmark=benchmark
        )

market_analytics_engine = MarketAnalyticsEngine()
