import re
from typing import List, Dict, Any, Optional, Tuple, Set
from app.services.ontology.taxonomy import ontology
from app.schemas.canonical_profile import CanonicalProfile

WEAK_VERBS_REGEX = re.compile(
    r"^(worked on|responsible for|helped with|assisted in|assisted with|handled|did|participated in|tasked with|involved in|supported)\s+",
    re.IGNORECASE
)

METRIC_REGEX = re.compile(
    r"(\b\d+(?:\.\d+)?%|\b\d+(?:\.\d+)?x|\$\d+(?:,\d+)*(?:\.\d+)?[kmbKMB]?|\b\d+\+?\s+(?:users|req\/s|rps|services|microservices|clients|teams|engineers|ms|seconds|minutes|hours|days|queries|nodes|clusters)\b)",
    re.IGNORECASE
)

STRONG_VERB_MAP = {
    "api": "Architected",
    "backend": "Engineered",
    "database": "Optimized",
    "query": "Accelerated",
    "performance": "Optimized",
    "cache": "Streamlined",
    "docker": "Containerized",
    "kubernetes": "Orchestrated",
    "pipeline": "Automated",
    "ci/cd": "Streamlined",
    "machine learning": "Formulated",
    "model": "Trained",
    "frontend": "Constructed",
    "ui": "Engineered",
    "microservices": "Architected",
    "cloud": "Deployed",
    "security": "Hardened",
    "testing": "Spearheaded",
}

class BulletRewriter:
    """
    Evidence-Grounded STAR/XYZ Bullet Point Rewriter.
    STRICT ZERO-HALLUCINATION:
    - Never fabricates numbers, percentages, or multipliers.
    - Never introduces technologies absent from the candidate's verified profile.
    - Converts passive phrasing into active, impact-oriented statements.
    """

    @classmethod
    def extract_metrics(cls, text: str) -> List[str]:
        return METRIC_REGEX.findall(text)

    @classmethod
    def extract_technologies(cls, text: str, allowed_canonical_skills: Optional[Set[str]] = None) -> List[str]:
        found: List[str] = []
        for alias_lower, canonical in ontology.alias_to_canonical.items():
            pattern = r"(?<!\w)" + re.escape(alias_lower) + r"(?!\w)"
            if re.search(pattern, text, re.IGNORECASE):
                if allowed_canonical_skills is None or canonical.lower() in allowed_canonical_skills:
                    if canonical not in found:
                        found.append(canonical)
        return found

    @classmethod
    def rewrite_bullet(
        cls,
        original_bullet: str,
        profile: CanonicalProfile,
        target_role: Optional[str] = None,
        user_confirmed_metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        cleaned_orig = original_bullet.strip().rstrip(".")
        if not cleaned_orig:
            return {
                "original_text": original_bullet,
                "proposed_text": original_bullet,
                "change_reason": "Empty bullet",
                "risk_flag": "safe_enhancement",
                "verified": True,
                "metrics_used": [],
                "technologies_used": []
            }

        # 1. Collect candidate's verified skills pool
        candidate_skills_set: Set[str] = set()
        for cat in profile.skills:
            for sk in cat.skills:
                candidate_skills_set.add(sk.normalized_name.lower())
                candidate_skills_set.add(sk.name.lower())

        # 2. Extract metrics from original bullet
        orig_metrics = cls.extract_metrics(cleaned_orig)
        all_allowed_metrics = set(orig_metrics + (user_confirmed_metrics or []))

        # 3. Extract technologies from original bullet
        orig_technologies = cls.extract_technologies(cleaned_orig, candidate_skills_set)

        # 4. Detect weak starting verb and choose strong replacement
        match_weak = WEAK_VERBS_REGEX.match(cleaned_orig)
        chosen_verb = "Engineered"
        task_text = cleaned_orig

        if match_weak:
            weak_phrase = match_weak.group(1)
            task_text = cleaned_orig[match_weak.end():].strip()
            # Capitalize first letter of remaining task text
            if task_text:
                task_text = task_text[0].upper() + task_text[1:]

            # Select context-aware action verb
            lower_bullet = cleaned_orig.lower()
            verb_found = False
            for kw, verb in STRONG_VERB_MAP.items():
                if kw in lower_bullet:
                    chosen_verb = verb
                    verb_found = True
                    break
            if not verb_found:
                chosen_verb = "Spearheaded"
        else:
            # Check if first word is already an action verb
            first_word = cleaned_orig.split()[0] if cleaned_orig.split() else ""
            if first_word.endswith("ed") or first_word.endswith("ing"):
                chosen_verb = first_word if not first_word.endswith("ing") else first_word[:-3] + "ed"
                task_text = " ".join(cleaned_orig.split()[1:])
            else:
                chosen_verb = "Implemented"
                task_text = cleaned_orig

        # 5. Build rewritten STAR bullet
        # Ensure tech clause is grounded
        tech_clause = ""
        if orig_technologies:
            tech_str = ", ".join(orig_technologies[:3])
            # Only add "utilizing..." if technologies aren't already mentioned in task_text
            tech_already_in_task = any(re.search(r"\b" + re.escape(t) + r"\b", task_text, re.IGNORECASE) for t in orig_technologies)
            if not tech_already_in_task:
                tech_clause = f" utilizing {tech_str}"

        # Clean task text of trailing periods or redundant verbs
        clean_task = task_text.rstrip(".")
        # If task text already starts with the chosen verb, avoid duplicate
        if clean_task.lower().startswith(chosen_verb.lower()):
            proposed = f"{clean_task}{tech_clause}."
        else:
            # Lowercase first letter if appending to verb
            if clean_task and not clean_task[0].isupper() or len(clean_task) > 1:
                clean_task_fragment = clean_task[0].lower() + clean_task[1:] if not clean_task.startswith("API") and not clean_task.startswith("UI") else clean_task
            else:
                clean_task_fragment = clean_task
            proposed = f"{chosen_verb} {clean_task_fragment}{tech_clause}."

        # Ensure punctuation is clean
        proposed = re.sub(r"\s+", " ", proposed).strip()
        if not proposed.endswith("."):
            proposed += "."

        # 6. HALLUCINATION & EVIDENCE VERIFICATION AUDIT
        # Audit metrics: Ensure NO fabricated numbers were added
        proposed_metrics = cls.extract_metrics(proposed)
        for pm in proposed_metrics:
            if pm not in all_allowed_metrics:
                # REJECT rewrite because an unauthorized metric appeared!
                return {
                    "original_text": original_bullet,
                    "proposed_text": original_bullet,
                    "change_reason": "Rejected rewrite: unverified metric detected.",
                    "risk_flag": "needs_user_verification",
                    "verified": False,
                    "metrics_used": orig_metrics,
                    "technologies_used": orig_technologies
                }

        # Audit technologies: Ensure NO skills absent from candidate profile were added
        proposed_techs = cls.extract_technologies(proposed)
        for pt in proposed_techs:
            if pt.lower() not in candidate_skills_set:
                # Strip or reject
                return {
                    "original_text": original_bullet,
                    "proposed_text": original_bullet,
                    "change_reason": f"Rejected rewrite: unverified technology '{pt}' detected.",
                    "risk_flag": "needs_user_verification",
                    "verified": False,
                    "metrics_used": orig_metrics,
                    "technologies_used": orig_technologies
                }

        # If identical, keep reason clean
        if proposed.strip().lower() == original_bullet.strip().lower():
            reason = "Maintained existing strong bullet structure."
        else:
            reason = f"Enhanced passive action framing to '{chosen_verb}' and structured for STAR clarity."

        return {
            "original_text": original_bullet,
            "proposed_text": proposed,
            "change_reason": reason,
            "risk_flag": "safe_enhancement",
            "verified": True,
            "metrics_used": orig_metrics,
            "technologies_used": orig_technologies
        }
