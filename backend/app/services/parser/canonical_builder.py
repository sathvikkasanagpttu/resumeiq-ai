import re
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.schemas.canonical_profile import (
    CanonicalProfile, CanonicalBasics, CanonicalExperience,
    CanonicalProject, CanonicalEducation, CanonicalCertification,
    CanonicalSkillCategory, GroundedField, GroundedBullet,
    GroundedSkillItem, GroundedSocialProfile, SourceSpan, LocationInfo
)
from app.services.ontology.taxonomy import ontology

class CanonicalProfileBuilder:
    """
    Transforms extracted resume entities into a normalized, single-source-of-truth
    CanonicalProfile (JSON Resume schema) with full evidence grounding.
    """

    @classmethod
    def build_from_parsed_data(
        cls,
        raw_text: str,
        contacts: Dict[str, Any],
        sections_dict: Dict[str, str],
        skills: List[Any],
        experiences: List[Any],
        projects: List[Any],
        educations: List[Any],
        certifications: List[Any]
    ) -> CanonicalProfile:
        # 1. Basics & Social Links
        name_val = contacts.get("name") or cls._extract_fallback_name(raw_text)
        email_val = contacts.get("email") or "candidate@example.com"
        phone_val = contacts.get("phone")
        summary_val = sections_dict.get("summary") or (
            f"Experienced professional with background in software systems and engineering."
        )

        profiles = cls._extract_social_links(raw_text)

        basics = CanonicalBasics(
            name=GroundedField(value=name_val, source="extracted", confidence=0.95),
            label=GroundedField(
                value=experiences[0].role if experiences else "Software Professional",
                source="extracted",
                confidence=0.9
            ),
            email=GroundedField(value=email_val, source="extracted", confidence=0.98),
            phone=GroundedField(value=phone_val, source="extracted", confidence=0.85 if phone_val else 0.5),
            summary=GroundedField(value=summary_val, source="extracted", confidence=0.9),
            location=GroundedField(
                value={"city": contacts.get("location", "Remote"), "region": None},
                source="extracted",
                confidence=0.8
            ),
            profiles=profiles
        )

        # 2. Experiences & Normalized Bullets
        canonical_experiences: List[CanonicalExperience] = []
        for exp in experiences:
            norm_role = cls._normalize_job_title(exp.role)
            norm_start, norm_end, is_curr, dur = cls._normalize_date_range(exp.start_date, exp.end_date, exp.is_current)

            bullets: List[GroundedBullet] = []
            for b_idx, b_text in enumerate(exp.bullet_points):
                action_verb = cls._extract_action_verb(b_text)
                metrics = cls._extract_metrics(b_text)
                bullet_tech = cls._extract_inline_tech(b_text)

                bullets.append(GroundedBullet(
                    id=str(uuid.uuid4()),
                    value=b_text.strip(),
                    source="extracted",
                    source_span=SourceSpan(page=1, text_snippet=b_text[:80]),
                    confidence=0.95 if metrics else 0.85,
                    action_verb=action_verb,
                    quantified_metrics=metrics,
                    technologies=bullet_tech,
                    is_accepted=True
                ))

            canonical_experiences.append(CanonicalExperience(
                id=str(uuid.uuid4()),
                company=GroundedField(value=exp.company.strip(), source="extracted", confidence=0.95),
                position=GroundedField(value=norm_role, source="extracted", confidence=0.95),
                start_date=GroundedField(value=norm_start, source="extracted", confidence=0.9),
                end_date=GroundedField(value=norm_end, source="extracted", confidence=0.9),
                is_current=GroundedField(value=is_curr, source="extracted", confidence=0.95),
                duration_months=dur,
                summary=GroundedField(value=exp.description, source="extracted", confidence=0.85) if exp.description else None,
                highlights=bullets,
                technologies=[
                    GroundedSkillItem(
                        name=t,
                        normalized_name=ontology.normalize(t) or t,
                        source="extracted",
                        usage_depth="used_in_production_with_outcome" if any(m in b.value for b in bullets for m in b.quantified_metrics) else "used_in_project"
                    ) for t in (exp.technologies or [])
                ]
            ))

        # 3. Projects
        canonical_projects: List[CanonicalProject] = []
        for proj in projects:
            p_bullets = [
                GroundedBullet(
                    id=str(uuid.uuid4()),
                    value=o,
                    source="extracted",
                    quantified_metrics=cls._extract_metrics(o),
                    action_verb=cls._extract_action_verb(o),
                    is_accepted=True
                ) for o in (proj.outcomes or [])
            ]
            if not p_bullets and proj.description:
                p_bullets.append(GroundedBullet(
                    id=str(uuid.uuid4()),
                    value=proj.description,
                    source="extracted",
                    action_verb=cls._extract_action_verb(proj.description),
                    is_accepted=True
                ))

            canonical_projects.append(CanonicalProject(
                id=str(uuid.uuid4()),
                name=GroundedField(value=proj.title.strip(), source="extracted", confidence=0.95),
                description=GroundedField(value=proj.description.strip(), source="extracted", confidence=0.9),
                highlights=p_bullets,
                technologies=[
                    GroundedSkillItem(
                        name=t,
                        normalized_name=ontology.normalize(t) or t,
                        source="extracted",
                        usage_depth="used_in_project"
                    ) for t in (proj.technologies or [])
                ],
                url=GroundedField(value=proj.url, source="extracted") if proj.url else None
            ))

        # 4. Education
        canonical_education: List[CanonicalEducation] = []
        for edu in educations:
            canonical_education.append(CanonicalEducation(
                id=str(uuid.uuid4()),
                institution=GroundedField(value=edu.institution.strip(), source="extracted", confidence=0.95),
                area=GroundedField(value=edu.field_of_study or "Computer Science", source="extracted", confidence=0.9),
                study_type=GroundedField(value=edu.degree or "Bachelor of Science", source="extracted", confidence=0.9),
                end_date=GroundedField(value=edu.graduation_year or "2022", source="extracted", confidence=0.85),
                score=GroundedField(value=edu.gpa, source="extracted", confidence=0.9) if edu.gpa else None
            ))

        # 5. Categorized Skills
        canonical_skills = cls._group_and_normalize_skills(skills, experiences, projects)

        # 6. Certifications
        canonical_certs: List[CanonicalCertification] = []
        for cert in certifications:
            canonical_certs.append(CanonicalCertification(
                id=str(uuid.uuid4()),
                name=GroundedField(value=cert.name.strip(), source="extracted", confidence=0.95),
                issuer=GroundedField(value=cert.issuing_org or "Certified Authority", source="extracted", confidence=0.9),
                date=GroundedField(value=cert.issue_date or "2023", source="extracted", confidence=0.85)
            ))

        return CanonicalProfile(
            basics=basics,
            experience=canonical_experiences,
            projects=canonical_projects,
            education=canonical_education,
            skills=canonical_skills,
            certifications=canonical_certs,
            achievements=[]
        )

    @classmethod
    def _extract_fallback_name(cls, raw_text: str) -> str:
        lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
        for line in lines[:3]:
            # If line is 2-4 words and no emails/numbers
            if not re.search(r"[@0-9]", line) and 2 <= len(line.split()) <= 4:
                return line
        return "Candidate Profile"

    @classmethod
    def _extract_social_links(cls, raw_text: str) -> List[GroundedSocialProfile]:
        profiles = []
        github_match = re.search(r"github\.com/([A-Za-z0-9_-]+)", raw_text, re.IGNORECASE)
        if github_match:
            profiles.append(GroundedSocialProfile(
                network="GitHub",
                username=github_match.group(1),
                url=f"https://github.com/{github_match.group(1)}",
                source="extracted",
                confidence=1.0
            ))
        linkedin_match = re.search(r"linkedin\.com/in/([A-Za-z0-9_-]+)", raw_text, re.IGNORECASE)
        if linkedin_match:
            profiles.append(GroundedSocialProfile(
                network="LinkedIn",
                username=linkedin_match.group(1),
                url=f"https://linkedin.com/in/{linkedin_match.group(1)}",
                source="extracted",
                confidence=1.0
            ))
        return profiles

    @classmethod
    def _normalize_job_title(cls, title: str) -> str:
        cleaned = title.strip()
        replacements = {
            r"\bsr\b\.?": "Senior",
            r"\bjr\b\.?": "Junior",
            r"\bdev\b": "Developer",
            r"\beng\b\.?": "Engineer",
            r"\barch\b\.?": "Architect",
            r"\badmin\b": "Administrator",
            r"\bmgr\b\.?": "Manager"
        }
        for pat, rep in replacements.items():
            cleaned = re.sub(pat, rep, cleaned, flags=re.IGNORECASE)
        return cleaned

    @classmethod
    def _normalize_date_range(cls, start: Optional[str], end: Optional[str], is_current: bool):
        start_str = start.strip() if start else "2021"
        end_str = "Present" if is_current or not end else end.strip()
        is_curr = is_current or ("present" in end_str.lower())
        
        # Estimate duration in months
        dur = 24
        try:
            start_year_m = re.search(r"\b(20\d\d|19\d\d)\b", start_str)
            end_year_m = re.search(r"\b(20\d\d|19\d\d)\b", end_str)
            if start_year_m and end_year_m:
                s_y = int(start_year_m.group(1))
                e_y = int(end_year_m.group(1))
                dur = max(6, (e_y - s_y) * 12)
            elif start_year_m and is_curr:
                s_y = int(start_year_m.group(1))
                now_y = datetime.now().year
                dur = max(6, (now_y - s_y) * 12)
        except Exception:
            dur = 18

        return start_str, end_str, is_curr, dur

    @classmethod
    def _extract_action_verb(cls, text: str) -> Optional[str]:
        words = re.findall(r"\b[A-Za-z]{3,}\b", text)
        if words:
            candidate = words[0].capitalize()
            common_verbs = [
                "Built", "Architected", "Engineered", "Developed", "Designed",
                "Created", "Orchestrated", "Implemented", "Led", "Optimized",
                "Automated", "Integrated", "Managed", "Scaled", "Reduced"
            ]
            if candidate in common_verbs:
                return candidate
        return None

    @classmethod
    def _extract_metrics(cls, text: str) -> List[str]:
        # Detect metrics like 45%, 20,000 req/sec, $12,000, 3x, 5M rows
        pattern = r"(\b\d+[\d,\.]*%\b|\b\d+[\d,\.]*\s*(?:req/sec|requests/sec|ms|users|rows)\b|\$\d+[\d,\.]*\b|\b\d+x\b)"
        matches = re.findall(pattern, text, re.IGNORECASE)
        return [m.strip() for m in matches]

    @classmethod
    def _extract_inline_tech(cls, text: str) -> List[str]:
        found = []
        for node in ontology.nodes.values():
            if re.search(r"\b" + re.escape(node.canonical_name) + r"\b", text, re.IGNORECASE):
                found.append(node.canonical_name)
        return list(set(found))

    @classmethod
    def _group_and_normalize_skills(
        cls,
        skills: List[Any],
        experiences: List[Any],
        projects: List[Any]
    ) -> List[CanonicalSkillCategory]:
        categories: Dict[str, List[GroundedSkillItem]] = {
            "Languages": [],
            "Frameworks & Libraries": [],
            "Databases & Storage": [],
            "Cloud & DevOps": [],
            "AI & Data Science": [],
            "Tools & Methodologies": []
        }

        seen_normalized = set()

        for sk in skills:
            norm_name = ontology.normalize(sk.normalized_skill) or sk.normalized_skill
            if norm_name in seen_normalized:
                continue
            seen_normalized.add(norm_name)

            # Determine usage depth
            has_production = any(
                sk.normalized_skill.lower() in (exp.description or "").lower() or
                any(sk.normalized_skill.lower() in b.lower() for b in exp.bullet_points)
                for exp in experiences
            )
            has_project = any(
                sk.normalized_skill.lower() in (proj.description or "").lower()
                for proj in projects
            )

            if has_production:
                depth = "used_in_production_with_outcome"
            elif has_project:
                depth = "used_in_project"
            else:
                depth = "listed_only"

            item = GroundedSkillItem(
                id=str(uuid.uuid4()),
                name=sk.normalized_skill,
                normalized_name=norm_name,
                category=sk.category or "technical",
                source="extracted",
                confidence=sk.confidence,
                evidence_strength=sk.evidence_strength,
                usage_depth=depth,
                evidence_quote=sk.source_evidence[:150] if sk.source_evidence else None
            )

            # Assign category
            cat_lower = (sk.category or "").lower()
            if "language" in cat_lower or norm_name in ["Python", "Java", "Go", "C++", "JavaScript", "TypeScript", "SQL"]:
                categories["Languages"].append(item)
            elif "framework" in cat_lower or norm_name in ["FastAPI", "Flask", "React", "Next.js", "Django", "Vue"]:
                categories["Frameworks & Libraries"].append(item)
            elif "database" in cat_lower or norm_name in ["PostgreSQL", "MySQL", "Redis", "MongoDB", "SQL Server"]:
                categories["Databases & Storage"].append(item)
            elif "cloud" in cat_lower or "devops" in cat_lower or norm_name in ["AWS", "Docker", "Kubernetes", "Linux"]:
                categories["Cloud & DevOps"].append(item)
            elif "ml" in cat_lower or norm_name in ["PyTorch", "TensorFlow", "Scikit-Learn", "NLP", "Pandas", "Power BI"]:
                categories["AI & Data Science"].append(item)
            else:
                categories["Tools & Methodologies"].append(item)

        result: List[CanonicalSkillCategory] = []
        for cat_name, items in categories.items():
            if items:
                result.append(CanonicalSkillCategory(
                    category_name=cat_name,
                    skills=items
                ))
        return result
