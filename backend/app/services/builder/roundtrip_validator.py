from typing import Dict, Any, List, Set, Tuple
from app.schemas.canonical_profile import CanonicalProfile
from app.services.builder.exporters import ResumeExporter
from app.services.builder.template_engine import get_val
from app.services.parser.section_detector import SectionDetector
from app.services.parser.entity_extractor import EntityExtractor

class RoundTripValidator:
    """
    ATS-Safety & Round-Trip Validation Engine.
    Re-parses the exported resume through RESUMEIQ's own NLP parser,
    extracts entities, and calculates information loss percentage.
    If loss > 5%, flags the build as ATS-unsafe and blocks auto-publishing.
    """

    LOSS_THRESHOLD = 0.05  # 5% max allowable loss

    @classmethod
    def validate(
        cls,
        profile: CanonicalProfile,
        rendered_text: str = None
    ) -> Dict[str, Any]:
        # 1. Obtain ground truth entities from CanonicalProfile
        renderable = profile.get_renderable_copy()

        expected_skills: Set[str] = set()
        for cat in renderable.skills:
            for sk in cat.skills:
                expected_skills.add(sk.normalized_name.lower())

        expected_companies: List[str] = []
        expected_dates: List[str] = []
        for exp in renderable.experience:
            comp = get_val(exp.company, "").strip()
            if comp:
                expected_companies.append(comp)
            s_date = get_val(exp.start_date, "").strip()
            if s_date:
                expected_dates.append(s_date)

        for edu in renderable.education:
            inst = get_val(edu.institution, "").strip()
            if inst:
                expected_companies.append(inst)

        total_entities = len(expected_skills) + len(expected_companies) + len(expected_dates)

        if total_entities == 0:
            return {
                "ats_loss_score": 0.0,
                "is_safe": True,
                "status": "passed",
                "missing_skills": [],
                "missing_jobs": [],
                "missing_dates": [],
                "total_expected_entities": 0,
                "message": "Zero entities in profile; passed trivially."
            }

        # 2. Render text if not provided
        if not rendered_text:
            rendered_text = ResumeExporter.to_txt(renderable)

        # 3. Re-parse text through SectionDetector and EntityExtractor
        sections = SectionDetector.detect_sections(rendered_text)
        sec_map = {s.section_type: s.content for s in sections}
        extracted_skills, _ = EntityExtractor.extract_skills_with_evidence(sec_map, rendered_text)
        re_extracted_skill_set = {s.normalized_skill.lower() for s in extracted_skills}

        # 4. Identify missing items
        missing_skills = [
            sk for sk in expected_skills
            if sk.lower() not in re_extracted_skill_set and sk.lower() not in rendered_text.lower()
        ]

        missing_companies = [
            comp for comp in expected_companies
            if comp.lower() not in rendered_text.lower()
        ]

        missing_dates = [
            dt for dt in expected_dates
            if dt.lower() not in rendered_text.lower()
        ]

        total_missing = len(missing_skills) + len(missing_companies) + len(missing_dates)
        loss_score = round(total_missing / total_entities, 4)
        is_safe = loss_score <= cls.LOSS_THRESHOLD

        status = "passed" if is_safe else "ats_loss_warning"
        msg = (
            f"ATS loss score is {loss_score * 100:.1f}%. "
            f"Retained {total_entities - total_missing}/{total_entities} core entities."
        )
        if not is_safe:
            msg += f" WARNING: Exceeds {cls.LOSS_THRESHOLD * 100:.0f}% loss threshold."

        return {
            "ats_loss_score": loss_score,
            "is_safe": is_safe,
            "status": status,
            "missing_skills": missing_skills,
            "missing_jobs": missing_companies,
            "missing_dates": missing_dates,
            "total_expected_entities": total_entities,
            "total_missing": total_missing,
            "message": msg
        }
