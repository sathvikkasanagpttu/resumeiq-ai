from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.resume import Resume
from app.models.job import Job
from app.schemas.career import JobRecommendationItem, JobRecommendationsResponse
from app.services.matching.hybrid_matcher import HybridMatcher

class JobRecommendationEngine:
    @classmethod
    def recommend_jobs(
        cls,
        db: Session,
        resume: Resume,
        limit: int = 10
    ) -> JobRecommendationsResponse:
        """
        Ranks all active jobs against candidate resume using multi-signal hybrid matching
        and produces structured application strategies, risk factors, and transferable skill explanations.
        """
        jobs = db.query(Job).filter(Job.is_active == True).all()
        ranked_items: List[JobRecommendationItem] = []

        for job in jobs:
            # Quick check / compute match
            match = HybridMatcher.compute_match(db, resume, job)
            
            # Strong matches
            strong_matches = [
                s.skill_name for s in job.skills[:3]
                if any(cs.normalized_skill.lower() == s.normalized_skill.lower() for cs in resume.skills)
            ]
            
            # Gaps
            gaps = [
                g.skill_name for g in match.skill_gaps if g.gap_severity in ["critical", "moderate"]
            ][:3]

            # Transferable skills
            transferable = [
                cs.normalized_skill for cs in resume.skills[:3]
                if any(cs.normalized_skill.lower() != js.normalized_skill.lower() for js in job.skills)
            ]

            risk_factors = []
            if match.experience_alignment_score < 70:
                risk_factors.append("Candidate experience depth is below listed job minimum.")
            if len(gaps) > 2:
                risk_factors.append(f"Multiple key technologies ({', '.join(gaps[:2])}) lack verified evidence.")
            if not risk_factors:
                risk_factors.append("Low risk: High core competency overlap.")

            ranked_items.append(JobRecommendationItem(
                job_id=job.id,
                title=job.title,
                company=job.company,
                location=job.location,
                work_model=job.work_model,
                compatibility_score=match.compatibility_score,
                why_it_matches=(
                    f"Strong alignment across {len(strong_matches)} core competencies with {match.semantic_score:.1f}% "
                    f"semantic fit and {match.evidence_strength_score:.1f}% verified evidence."
                ),
                strong_matches=strong_matches if strong_matches else ["Baseline engineering fundamentals"],
                potential_gaps=gaps if gaps else ["None identified"],
                transferable_skills=transferable[:2],
                risk_factors=risk_factors,
                recommended_strategy=match.explanation_summary.get("recommendation_strategy", "Apply with tailored evidence bullets.")
            ))

        ranked_items.sort(key=lambda x: x.compatibility_score, reverse=True)

        return JobRecommendationsResponse(
            resume_id=resume.id,
            total_analyzed_jobs=len(jobs),
            recommendations=ranked_items[:limit]
        )

job_recommendation_engine = JobRecommendationEngine()
