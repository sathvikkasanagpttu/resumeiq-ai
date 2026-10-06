import re
from typing import Dict, List, Optional, Any, Tuple
from app.models.resume import Resume
from app.services.ontology.taxonomy import ontology
from app.schemas.evidence import VerificationClaim
from app.core.exceptions import HallucinationDetectedError

class VerificationPipeline:
    """
    AI Verification Pipeline ensuring zero hallucination.
    Evaluates claims against the candidate's actual resume evidence graph.
    Rejects or flags unsupported claims before recommendations or generated materials reach the user.
    """
    @classmethod
    def verify_claim(
        cls,
        resume: Resume,
        claim_text: str,
        target_entity: str
    ) -> VerificationClaim:
        """
        Runs: Claim -> Retrieval -> Validation -> Support Check -> Confidence Calc
        """
        norm_entity = ontology.normalize(target_entity) or target_entity.strip().lower()
        
        # Search candidate resume for explicit mentions of the target entity
        matching_skills = [
            s for s in resume.skills
            if s.normalized_skill.lower() == norm_entity.lower()
        ]
        
        matching_evidence = [
            e for e in resume.evidence_items
            if e.entity_name.lower() == norm_entity.lower()
        ]

        # 1. Supported Check (Verified Evidence)
        if matching_evidence:
            best_ev = matching_evidence[0]
            if best_ev.evidence_strength == "verified":
                return VerificationClaim(
                    claim=claim_text,
                    target_entity=target_entity,
                    confidence=best_ev.confidence_score,
                    evidence_strength="verified",
                    status="supported",
                    cited_evidence=best_ev.context_snippet,
                    reason=f"Verified through action sentence in {best_ev.source_section} section."
                )
            else:
                return VerificationClaim(
                    claim=claim_text,
                    target_entity=target_entity,
                    confidence=0.72,
                    evidence_strength="weak",
                    status="partially_supported",
                    cited_evidence=best_ev.context_snippet,
                    reason="Entity mentioned in resume, but lacks quantified metrics or direct project action verbs."
                )

        if matching_skills:
            sk = matching_skills[0]
            return VerificationClaim(
                claim=claim_text,
                target_entity=target_entity,
                confidence=sk.confidence,
                evidence_strength=sk.evidence_strength,
                status="partially_supported" if sk.evidence_strength != "verified" else "supported",
                cited_evidence=sk.source_evidence,
                reason="Identified in candidate skills inventory."
            )

        # 2. Check for Inferred / Transferable Support
        node = ontology.get_node(target_entity)
        if node:
            for cand_sk in resume.skills:
                cand_node = ontology.get_node(cand_sk.normalized_skill)
                if cand_node and node.canonical_name in cand_node.transferable_to:
                    trans_score = cand_node.transferable_to[node.canonical_name]
                    return VerificationClaim(
                        claim=claim_text,
                        target_entity=target_entity,
                        confidence=round(trans_score * 0.85, 2),
                        evidence_strength="inferred",
                        status="uncertain",
                        cited_evidence=cand_sk.source_evidence,
                        reason=(
                            f"Inferred via transferable skill '{cand_sk.normalized_skill}' "
                            f"(affinity {int(trans_score*100)}%). Explicit '{target_entity}' experience is not documented."
                        )
                    )

        # 3. Unsupported / Missing Check
        return VerificationClaim(
            claim=claim_text,
            target_entity=target_entity,
            confidence=0.0,
            evidence_strength="missing",
            status="unsupported",
            cited_evidence=None,
            reason=f"No factual evidence found in candidate profile for '{target_entity}'."
        )

    @classmethod
    def validate_generated_text(
        cls,
        resume: Resume,
        generated_text: str,
        prohibited_entities: Optional[List[str]] = None
    ) -> Tuple[bool, List[VerificationClaim], List[str]]:
        """
        Validates generated material (cover letter, bullet point, outreach)
        against candidate resume facts.
        Flags any entity or technology mentioned in generated text that lacks supporting evidence.
        """
        detected_claims: List[VerificationClaim] = []
        flagged_unsupported: List[str] = []
        
        # Check all known tech terms mentioned in generated text
        for alias_lower, canonical in ontology.alias_to_canonical.items():
            pattern = r"\b" + re.escape(alias_lower) + r"\b"
            if re.search(pattern, generated_text, re.IGNORECASE):
                claim_result = cls.verify_claim(
                    resume=resume,
                    claim_text=f"Candidate has proficient experience with {canonical}",
                    target_entity=canonical
                )
                detected_claims.append(claim_result)
                if claim_result.status in ["unsupported", "missing"]:
                    flagged_unsupported.append(canonical)

        # Also check explicit prohibited entities
        if prohibited_entities:
            for p in prohibited_entities:
                if re.search(r"\b" + re.escape(p) + r"\b", generated_text, re.IGNORECASE):
                    flagged_unsupported.append(p)

        is_valid = len(flagged_unsupported) == 0
        return is_valid, detected_claims, list(set(flagged_unsupported))

verification_pipeline = VerificationPipeline()
