from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from app.services.ontology.taxonomy import ontology, SkillNode

@dataclass
class SkillComparisonResult:
    target_skill: str
    matched_candidate_skill: Optional[str]
    match_type: str  # exact, related, transferable, missing
    match_score: float  # 0.0 to 1.0
    explanation: str

class SkillMatcher:
    def __init__(self):
        self.ontology = ontology

    def compare_skill(
        self,
        job_skill: str,
        candidate_skills: List[str]
    ) -> SkillComparisonResult:
        """
        Compares a single required/preferred job skill against a candidate's list of skills.
        Classifies as exact, related, transferable, or missing.
        """
        normalized_job_skill = self.ontology.normalize(job_skill) or job_skill.strip()
        job_node = self.ontology.get_node(job_skill)

        # 1. Exact Match Check (case-insensitive & canonical)
        for cand_skill in candidate_skills:
            cand_norm = self.ontology.normalize(cand_skill) or cand_skill.strip()
            if normalized_job_skill.lower() == cand_norm.lower():
                return SkillComparisonResult(
                    target_skill=job_skill,
                    matched_candidate_skill=cand_skill,
                    match_type="exact",
                    match_score=1.0,
                    explanation=f"Exact match on '{cand_skill}'"
                )

        if not job_node:
            # Check simple string containment as fallback
            for cand_skill in candidate_skills:
                if job_skill.lower() in cand_skill.lower() or cand_skill.lower() in job_skill.lower():
                    return SkillComparisonResult(
                        target_skill=job_skill,
                        matched_candidate_skill=cand_skill,
                        match_type="related",
                        match_score=0.8,
                        explanation=f"Textual similarity between '{job_skill}' and '{cand_skill}'"
                    )
            return SkillComparisonResult(
                target_skill=job_skill,
                matched_candidate_skill=None,
                match_type="missing",
                match_score=0.0,
                explanation=f"No evidence found for '{job_skill}'"
            )

        # 2. Check if candidate has a CHILD skill (e.g., job asks for Python, candidate has FastAPI or Pandas)
        for cand_skill in candidate_skills:
            cand_node = self.ontology.get_node(cand_skill)
            if cand_node and cand_node.canonical_name in job_node.children:
                return SkillComparisonResult(
                    target_skill=job_skill,
                    matched_candidate_skill=cand_node.canonical_name,
                    match_type="related",
                    match_score=0.90,
                    explanation=f"Candidate demonstrates '{cand_node.canonical_name}', which is a specialized subsystem of '{job_node.canonical_name}'"
                )

        # 3. Check if candidate has a PARENT skill (e.g., job asks for FastAPI, candidate has Python)
        for cand_skill in candidate_skills:
            cand_node = self.ontology.get_node(cand_skill)
            if cand_node and cand_node.canonical_name in job_node.parents:
                return SkillComparisonResult(
                    target_skill=job_skill,
                    matched_candidate_skill=cand_node.canonical_name,
                    match_type="related",
                    match_score=0.75,
                    explanation=f"Candidate demonstrates foundational skill '{cand_node.canonical_name}', which supports '{job_node.canonical_name}'"
                )

        # 4. Check Transferable Skills (e.g., candidate has AWS, job asks for GCP)
        for cand_skill in candidate_skills:
            cand_node = self.ontology.get_node(cand_skill)
            if cand_node:
                # Direct transferable weight from candidate to job
                if job_node.canonical_name in cand_node.transferable_to:
                    weight = cand_node.transferable_to[job_node.canonical_name]
                    return SkillComparisonResult(
                        target_skill=job_skill,
                        matched_candidate_skill=cand_node.canonical_name,
                        match_type="transferable",
                        match_score=weight,
                        explanation=f"Candidate has '{cand_node.canonical_name}' which possesses a {int(weight*100)}% transferable affinity to '{job_node.canonical_name}'"
                    )
                # Check siblings / related
                if cand_node.canonical_name in job_node.related:
                    return SkillComparisonResult(
                        target_skill=job_skill,
                        matched_candidate_skill=cand_node.canonical_name,
                        match_type="related",
                        match_score=0.75,
                        explanation=f"Candidate demonstrates related technology '{cand_node.canonical_name}' in the same technological domain as '{job_node.canonical_name}'"
                    )

        # 5. Missing Skill
        return SkillComparisonResult(
            target_skill=job_skill,
            matched_candidate_skill=None,
            match_type="missing",
            match_score=0.0,
            explanation=f"No verified or transferable evidence found for required skill '{job_skill}'"
        )

skill_matcher = SkillMatcher()
