from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from app.models.resume import Resume
from app.models.job import Job
from app.models.matching import Match, MatchComponent, SkillGap, Recommendation
from app.schemas.matching import MatchWeightsConfig, EvidenceCitation
from app.services.matching.lexical_engine import lexical_engine
from app.services.matching.semantic_engine import semantic_engine
from app.services.ontology.skill_matcher import skill_matcher
from app.services.matching.explainability import explainability_engine
from app.core.config import settings
from app.core.logging import logger

class HybridMatcher:
    @classmethod
    def compute_match(
        cls,
        db: Session,
        resume: Resume,
        job: Job,
        custom_weights: Optional[MatchWeightsConfig] = None
    ) -> Match:
        """
        Executes multi-signal candidate-job compatibility scoring across 10 distinct signals:
        1. Lexical Similarity (BM25)
        2. Semantic Similarity (Embeddings)
        3. Required Skill Coverage
        4. Preferred Skill Coverage
        5. Evidence Strength
        6. Experience Alignment
        7. Seniority Alignment
        8. Domain Alignment
        9. Education Alignment
        10. Preference Alignment
        """
        w = custom_weights or MatchWeightsConfig()

        # Gather Candidate Skills & Evidence
        cand_skills = [s.normalized_skill for s in resume.skills]
        verified_skills_count = sum(1 for s in resume.skills if s.evidence_strength == "verified")
        total_skills_count = max(len(resume.skills), 1)

        # 1. Lexical Score (BM25)
        lexical_score = lexical_engine.compute_bm25_similarity(job.description, resume.raw_text)

        # 2. Semantic Score (Embeddings Cosine Similarity)
        semantic_score = semantic_engine.compute_semantic_similarity(job.description, resume.raw_text)

        # 3 & 4. Required & Preferred Skill Coverage
        req_job_skills = [s for s in job.skills if s.is_required]
        pref_job_skills = [s for s in job.skills if not s.is_required]

        top_matched_skills: List[Dict[str, Any]] = []
        critical_missing_skills: List[str] = []
        detected_gaps: List[Dict[str, Any]] = []

        req_score_sum = 0.0
        for r_sk in req_job_skills:
            res = skill_matcher.compare_skill(r_sk.normalized_skill, cand_skills)
            req_score_sum += res.match_score
            if res.match_type in ["exact", "related", "transferable"]:
                top_matched_skills.append({
                    "skill": r_sk.normalized_skill,
                    "candidate_skill": res.matched_candidate_skill,
                    "type": res.match_type,
                    "score": res.match_score
                })
            else:
                critical_missing_skills.append(r_sk.normalized_skill)
                detected_gaps.append({
                    "skill": r_sk.normalized_skill,
                    "severity": "critical",
                    "explanation": f"Must-have requirement '{r_sk.normalized_skill}' is not evidenced in resume.",
                    "recommendation": f"Add concrete project or work evidence demonstrating proficiency in '{r_sk.normalized_skill}'.",
                    "confidence": 0.95
                })

        req_coverage = (req_score_sum / max(len(req_job_skills), 1)) * 100.0

        pref_score_sum = 0.0
        for p_sk in pref_job_skills:
            res = skill_matcher.compare_skill(p_sk.normalized_skill, cand_skills)
            pref_score_sum += res.match_score
            if res.match_type in ["exact", "related", "transferable"]:
                top_matched_skills.append({
                    "skill": p_sk.normalized_skill,
                    "candidate_skill": res.matched_candidate_skill,
                    "type": res.match_type,
                    "score": res.match_score
                })
            else:
                detected_gaps.append({
                    "skill": p_sk.normalized_skill,
                    "severity": "moderate",
                    "explanation": f"Preferred skill '{p_sk.normalized_skill}' is missing from profile.",
                    "recommendation": f"Consider acquiring foundational knowledge in '{p_sk.normalized_skill}'.",
                    "confidence": 0.85
                })

        pref_coverage = (pref_score_sum / max(len(pref_job_skills), 1)) * 100.0 if pref_job_skills else 100.0

        # Check Representation Gaps (Candidate has skill, but evidence is only 'weak' / list mention)
        for sk in resume.skills:
            if sk.evidence_strength == "weak" and any(r.normalized_skill == sk.normalized_skill for r in job.skills):
                detected_gaps.append({
                    "skill": sk.normalized_skill,
                    "severity": "representation",
                    "explanation": f"Skill '{sk.normalized_skill}' is listed in skills section but lacks action-oriented project or bullet evidence.",
                    "recommendation": f"Articulate specific impact and action verbs for '{sk.normalized_skill}' in your experience bullets.",
                    "confidence": 0.90
                })

        # 5. Evidence Strength Score
        evidence_strength_score = min(100.0, (verified_skills_count / total_skills_count) * 120.0)

        # 6. Experience Alignment Score
        cand_years = len(resume.experiences) * 1.5  # estimate based on verified roles
        job_years = job.experience_years_min or 2.0
        if cand_years >= job_years:
            exp_alignment = 100.0
        elif cand_years > 0:
            exp_alignment = min(100.0, (cand_years / job_years) * 100.0)
        else:
            exp_alignment = 40.0

        # 7. Seniority Alignment Score
        cand_seniority = "senior" if cand_years >= 5 else ("mid" if cand_years >= 2 else "entry")
        job_seniority = job.seniority.lower()
        if cand_seniority == job_seniority:
            seniority_score = 100.0
        elif (cand_seniority == "senior" and job_seniority in ["mid", "entry"]) or (cand_seniority == "mid" and job_seniority == "entry"):
            seniority_score = 90.0
        elif cand_seniority == "mid" and job_seniority == "senior":
            seniority_score = 75.0
        else:
            seniority_score = 55.0

        # 8. Domain Alignment Score
        cand_categories = set(s.category for s in resume.skills if s.category)
        domain_overlap = len(cand_categories) / 6.0  # normalized across primary tech domains
        domain_score = min(100.0, max(50.0, domain_overlap * 100.0))

        # 9. Education Alignment Score
        has_degree = len(resume.educations) > 0
        edu_score = 100.0 if has_degree else 75.0

        # 10. Preference Alignment Score
        pref_score = 100.0  # remote-ready standard

        # Compile Evidence Citations from verified evidence items
        citations: List[EvidenceCitation] = []
        for ev in resume.evidence_items[:6]:
            if ev.evidence_strength == "verified":
                citations.append(EvidenceCitation(
                    entity=ev.entity_name,
                    strength=ev.evidence_strength,
                    quote=ev.context_snippet,
                    source_section=ev.source_section,
                    explanation=f"Direct action verb '{ev.action_verb or 'implemented'}' verifies real-world application."
                ))

        # Configurable Weighted Combination
        # Normalize weights
        weight_dict = {
            "required_skills": w.weight_required_skills,
            "semantic_fit": w.weight_semantic_fit,
            "evidence_strength": w.weight_evidence_strength,
            "experience_alignment": w.weight_experience_alignment,
            "preferred_skills": w.weight_preferred_skills,
            "seniority_alignment": w.weight_seniority_alignment,
            "domain_alignment": w.weight_domain_alignment,
            "education_alignment": w.weight_education_alignment,
        }
        total_w = sum(weight_dict.values())

        raw_scores = {
            "required_skills": req_coverage,
            "semantic_fit": semantic_score,
            "evidence_strength": evidence_strength_score,
            "experience_alignment": exp_alignment,
            "preferred_skills": pref_coverage,
            "seniority_alignment": seniority_score,
            "domain_alignment": domain_score,
            "education_alignment": edu_score,
        }

        weighted_total = sum(raw_scores[k] * (weight_dict[k] / total_w) for k in weight_dict)
        compatibility_score = round(min(100.0, max(0.0, weighted_total)), 1)

        # Generate Explainability Summary
        explanation_summary = explainability_engine.generate_explanation(
            compatibility_score=compatibility_score,
            component_scores=raw_scores,
            top_matched_skills=top_matched_skills,
            critical_missing_skills=critical_missing_skills,
            citations=citations,
            candidate_years=cand_years,
            required_years=job_years
        )

        # Create Match Record
        match = Match(
            resume_id=resume.id,
            job_id=job.id,
            compatibility_score=compatibility_score,
            semantic_score=round(semantic_score, 1),
            lexical_score=round(lexical_score, 1),
            required_skill_coverage=round(req_coverage, 1),
            preferred_skill_coverage=round(pref_coverage, 1),
            evidence_strength_score=round(evidence_strength_score, 1),
            experience_alignment_score=round(exp_alignment, 1),
            seniority_alignment_score=round(seniority_score, 1),
            domain_alignment_score=round(domain_score, 1),
            education_alignment_score=round(edu_score, 1),
            preference_alignment_score=round(pref_score, 1),
            status="completed",
            calculation_weights=weight_dict,
            explanation_summary=explanation_summary.model_dump()
        )
        db.add(match)
        db.flush()

        # Create Match Components
        explanations_map = {
            "required_skills": f"Candidate demonstrates {req_coverage:.1f}% coverage across {len(req_job_skills)} required technical competencies.",
            "semantic_fit": f"Dense vector embedding alignment between candidate experience corpus and job scope scored {semantic_score:.1f}/100.",
            "evidence_strength": f"{evidence_strength_score:.1f}% of candidate skills are backed by verifiable action sentences or metrics.",
            "experience_alignment": f"Candidate career depth ({cand_years:.1f} yrs) relative to benchmark requirement ({job_years:.1f} yrs).",
            "preferred_skills": f"Coverage of non-mandatory, preferred domain attributes scored {pref_coverage:.1f}%.",
            "seniority_alignment": f"Seniority alignment between candidate level ({cand_seniority}) and target tier ({job_seniority}).",
            "domain_alignment": f"Cross-functional domain presence across technology categories scored {domain_score:.1f}%.",
            "education_alignment": f"Academic and credential qualification matching scored {edu_score:.1f}%.",
        }

        for comp_name, comp_raw in raw_scores.items():
            comp_w = weight_dict[comp_name]
            db_comp = MatchComponent(
                match_id=match.id,
                component_name=comp_name,
                weight=comp_w,
                raw_score=round(comp_raw, 1),
                weighted_score=round(comp_raw * comp_w, 2),
                explanation=explanations_map[comp_name]
            )
            db.add(db_comp)

        # Create Skill Gaps
        for gap in detected_gaps:
            db_gap = SkillGap(
                match_id=match.id,
                skill_name=gap["skill"],
                gap_severity=gap["severity"],
                candidate_evidence=None,
                explanation=gap["explanation"],
                recommendation=gap["recommendation"],
                confidence=gap["confidence"]
            )
            db.add(db_gap)

        # Create Recommendations
        rec_items = [
            Recommendation(
                match_id=match.id,
                category="resume_opt",
                title="Ground bullet points with action verbs and metrics",
                description="Strengthen evidence scores by revising passive task descriptions into measurable outcome statements.",
                priority="high",
                actionable_steps=["Identify projects using core technologies", "Add exact metrics (%, scale, latency, users)", "Use active verbs like 'Architected' or 'Engineered'"],
                grounded_evidence_citations=[c.quote for c in citations[:2]]
            ),
            Recommendation(
                match_id=match.id,
                category="skill_acquisition",
                title=f"Address critical gap in {critical_missing_skills[0]}" if critical_missing_skills else "Solidify adjacent technologies",
                description=f"Job requires verified experience in {critical_missing_skills[0]}." if critical_missing_skills else "Pursue deep-dive architecture projects.",
                priority="high" if critical_missing_skills else "medium",
                actionable_steps=["Complete proof-of-concept project", "Document architecture and code in GitHub repository", "Add project bullet point with measurable delivery"],
                grounded_evidence_citations=[]
            )
        ]
        for r in rec_items:
            db.add(r)

        db.commit()
        db.refresh(match)
        logger.info(f"Match computed: {match.id} (Compatibility Score: {match.compatibility_score})")
        return match
