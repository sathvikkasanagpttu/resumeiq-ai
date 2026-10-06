from typing import List, Dict, Any
from app.schemas.matching import MatchExplanationSummary, EvidenceCitation

class ExplainabilityEngine:
    @staticmethod
    def generate_explanation(
        compatibility_score: float,
        component_scores: Dict[str, float],
        top_matched_skills: List[Dict[str, Any]],
        critical_missing_skills: List[str],
        citations: List[EvidenceCitation],
        candidate_years: float,
        required_years: float,
    ) -> MatchExplanationSummary:
        # Determine headline based on score
        if compatibility_score >= 85:
            headline = "Strong Evidence-Backed Match"
            overall = (
                f"Candidate exhibits substantial technical alignment with a {compatibility_score:.1f}/100 "
                "compatibility score. Core required competencies are demonstrated with verified project and work history."
            )
            strategy = "Focus application on high-impact leadership and specific architecture deliverables cited in resume."
        elif compatibility_score >= 70:
            headline = "Competitive Match with Addressable Gaps"
            overall = (
                f"Candidate demonstrates solid foundational capabilities ({compatibility_score:.1f}/100), "
                "covering key requirements, though certain secondary or specialized requirements require clarification or transferable framing."
            )
            strategy = "Highlight transferable capabilities and quantify direct experience in related systems."
        elif compatibility_score >= 50:
            headline = "Partial Alignment - Significant Skill Gaps"
            overall = (
                f"Candidate matches selected criteria ({compatibility_score:.1f}/100) but lacks explicit evidence "
                f"for critical requirements. Identified missing areas: {', '.join(critical_missing_skills[:3])}."
            )
            strategy = "Pursue targeted upskilling or highlight adjacent project experience before applying."
        else:
            headline = "Low Alignment with Current Requirements"
            overall = (
                f"Candidate profile shows limited overlap ({compatibility_score:.1f}/100) with required tech stack and experience levels."
            )
            strategy = "Consider roles better tailored to current core competencies or undertake comprehensive gap closure."

        # Top strengths
        strengths = []
        for match in top_matched_skills[:4]:
            skill = match.get("skill")
            m_type = match.get("type", "exact")
            cand_skill = match.get("candidate_skill", skill)
            if m_type == "exact":
                strengths.append(f"Demonstrated verified proficiency in required skill '{skill}'")
            elif m_type == "related":
                strengths.append(f"Strong related domain background via '{cand_skill}' aligning with '{skill}'")
            elif m_type == "transferable":
                strengths.append(f"Transferable expertise from '{cand_skill}' applicable to '{skill}'")

        if candidate_years >= required_years:
            strengths.append(f"Meets or exceeds required experience timeline ({candidate_years:.1f} yrs vs {required_years:.1f} yrs required)")

        # Critical concerns
        concerns = []
        for missing in critical_missing_skills[:3]:
            concerns.append(f"Missing explicit candidate evidence for required skill '{missing}'")

        if candidate_years < required_years:
            concerns.append(
                f"Candidate experience timeline ({candidate_years:.1f} yrs) is below stated minimum ({required_years:.1f} yrs)"
            )

        return MatchExplanationSummary(
            headline=headline,
            overall_assessment=overall,
            top_strengths=strengths if strengths else ["Basic profile overlap detected"],
            critical_concerns=concerns if concerns else ["No critical blockers identified"],
            citations=citations[:5],
            recommendation_strategy=strategy
        )

explainability_engine = ExplainabilityEngine()
