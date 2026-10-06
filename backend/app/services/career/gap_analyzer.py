from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.matching import Match, SkillGap
from app.schemas.gap import SkillGapResponse, SkillGapReport

class GapAnalyzer:
    @classmethod
    def get_gap_report(cls, db: Session, match: Match) -> SkillGapReport:
        gaps = db.query(SkillGap).filter(SkillGap.match_id == match.id).all()
        
        report_gaps: List[SkillGapResponse] = []
        crit_count = 0
        mod_count = 0
        min_count = 0
        trans_count = 0
        rep_count = 0

        for g in gaps:
            if g.gap_severity == "critical":
                crit_count += 1
            elif g.gap_severity == "moderate":
                mod_count += 1
            elif g.gap_severity == "minor":
                min_count += 1
            elif g.gap_severity == "transferable":
                trans_count += 1
            elif g.gap_severity == "representation":
                rep_count += 1

            report_gaps.append(SkillGapResponse(
                id=g.id,
                skill_name=g.skill_name,
                job_requirement_id=g.job_requirement_id,
                gap_severity=g.gap_severity,
                candidate_evidence=g.candidate_evidence or "No verified resume evidence found",
                explanation=g.explanation,
                recommendation=g.recommendation,
                confidence=g.confidence
            ))

        return SkillGapReport(
            match_id=match.id,
            total_gaps=len(report_gaps),
            critical_gaps_count=crit_count,
            moderate_gaps_count=mod_count,
            minor_gaps_count=min_count,
            transferable_skills_count=trans_count,
            representation_gaps_count=rep_count,
            gaps=report_gaps
        )

gap_analyzer = GapAnalyzer()
