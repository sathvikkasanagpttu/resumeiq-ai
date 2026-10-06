import re
from typing import Dict, List, Optional, Tuple, Any
from app.services.ontology.taxonomy import ontology
from app.schemas.resume import (
    SkillExtraction, CandidateExperienceBase, CandidateProjectBase,
    CandidateEducationBase, CandidateCertificationBase
)
from app.schemas.evidence import EvidenceItemBase

ACTION_VERBS = {
    "built", "developed", "architected", "engineered", "designed", "created",
    "implemented", "deployed", "optimized", "migrated", "automated", "scaled",
    "reduced", "increased", "accelerated", "integrated", "led", "managed",
    "spearheaded", "orchestrated", "refactored", "analyzed", "delivered", "maintained"
}

METRIC_PATTERNS = [
    r"\b\d+%",                          # 40%
    r"\b\d+\s*percent",                # 15 percent
    r"\$\d+(\.\d+)?\s*(k|m|b)?\b",     # $500k, $1.2M
    r"\b\d+(\.\d+)?\s*(ms|seconds)\b", # 200ms
    r"\b\d+x\b",                       # 3x
    r"\b\d+(\.\d+)?\s*(k|m|million|billion|thousand)\b", # 10M, 500k
    r"\b\d+\+\s*(users|clients|nodes|servers|services|requests|rps)\b", # 100k+ users
]

class EntityExtractor:
    @staticmethod
    def extract_contacts(text: str) -> Dict[str, Optional[str]]:
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
        email = email_match.group(0) if email_match else None

        phone_match = re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
        phone = phone_match.group(0) if phone_match else None

        linkedin_match = re.search(r"(linkedin\.com/in/[\w-]+)", text, re.IGNORECASE)
        linkedin = linkedin_match.group(0) if linkedin_match else None

        github_match = re.search(r"(github\.com/[\w-]+)", text, re.IGNORECASE)
        github = github_match.group(0) if github_match else None

        # Guess name from the first non-empty line
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        name = lines[0] if lines and len(lines[0]) < 50 and not re.search(r"@|\.com|\d{4}", lines[0]) else "Candidate"

        return {
            "name": name,
            "email": email,
            "phone": phone,
            "linkedin": linkedin,
            "github": github,
        }

    @staticmethod
    def extract_skills_with_evidence(
        sections: Dict[str, str],
        full_text: str
    ) -> Tuple[List[SkillExtraction], List[EvidenceItemBase]]:
        """
        Extracts skills from text and assigns evidence strength based on context:
        - verified: Action verb + metric or detailed accomplishment
        - weak: Mention in skills list or lonely keyword
        - inferred: Subsystem/parent alignment
        """
        extracted_skills: Dict[str, SkillExtraction] = {}
        evidence_items: List[EvidenceItemBase] = []

        # Split full text into candidate sentences
        sentences = re.split(r"(?<=[.!?\n])\s+", full_text)

        # Check every known canonical skill and alias in the ontology
        for alias_lower, canonical in ontology.alias_to_canonical.items():
            pattern = r"(?<!\w)" + re.escape(alias_lower) + r"(?!\w)"
            
            # Search across sentences for rich context
            for sentence in sentences:
                sent_clean = sentence.strip()
                if not sent_clean:
                    continue

                if re.search(pattern, sent_clean, re.IGNORECASE):
                    # Determine section source
                    source_section = "general"
                    for sec_type, sec_content in sections.items():
                        if sent_clean in sec_content:
                            source_section = sec_type
                            break

                    # Analyze evidence strength
                    sent_lower = sent_clean.lower()
                    has_action = any(verb in sent_lower for verb in ACTION_VERBS)
                    has_metric = any(re.search(mp, sent_clean, re.IGNORECASE) for mp in METRIC_PATTERNS)

                    if source_section in ["experience", "projects"] and (has_action or has_metric):
                        strength = "verified"
                        confidence = 0.95 if (has_action and has_metric) else 0.88
                    elif source_section == "skills":
                        strength = "weak"
                        confidence = 0.70
                    else:
                        strength = "weak" if not has_action else "verified"
                        confidence = 0.75

                    node = ontology.get_node(canonical)
                    category = node.category if node else "technical"

                    # Action verb detection
                    found_verb = next((v for v in ACTION_VERBS if v in sent_lower), None)
                    # Quantified impact detection
                    metric_found = None
                    for mp in METRIC_PATTERNS:
                        m = re.search(mp, sent_clean, re.IGNORECASE)
                        if m:
                            metric_found = m.group(0)
                            break

                    # Keep best evidence for each skill
                    if canonical not in extracted_skills or (
                        strength == "verified" and extracted_skills[canonical].evidence_strength != "verified"
                    ):
                        extracted_skills[canonical] = SkillExtraction(
                            original_text=sentence.strip()[:100],
                            normalized_skill=canonical,
                            category=category,
                            source_section=source_section,
                            source_evidence=sent_clean,
                            confidence=confidence,
                            evidence_strength=strength
                        )

                    evidence_items.append(EvidenceItemBase(
                        entity_type="skill",
                        entity_name=canonical,
                        context_snippet=sent_clean,
                        source_section=source_section,
                        evidence_strength=strength,
                        confidence_score=confidence,
                        action_verb=found_verb,
                        quantified_impact=metric_found,
                        metadata_info={"category": category}
                    ))

        return list(extracted_skills.values()), evidence_items

    @staticmethod
    def extract_experiences(experience_text: str) -> List[CandidateExperienceBase]:
        experiences: List[CandidateExperienceBase] = []
        if not experience_text.strip():
            return experiences

        blocks = re.split(r"\n\s*\n", experience_text.strip())
        current_exp: Optional[Dict[str, Any]] = None

        for block in blocks:
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            if not lines:
                continue

            first_line = lines[0]
            # Try to match Role at Company or Company - Role pattern
            role_match = re.search(r"^(.*?)(?:\s+at\s+|\s+[-–|]\s+)(.*?)$", first_line)
            date_match = re.search(
                r"\b((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|[0-9]{4})\b.*?[-–to\s]+(?:present|current|[0-9]{4}|[a-z]{3}))",
                block,
                re.IGNORECASE
            )

            bullets = [l.lstrip("•-* ").strip() for l in lines[1:] if l.startswith(("•", "-", "*")) or len(l) > 20]
            
            # Detect technologies in this experience
            techs = []
            for alias_lower, canonical in ontology.alias_to_canonical.items():
                if re.search(r"(?<!\w)" + re.escape(alias_lower) + r"(?!\w)", block, re.IGNORECASE):
                    if canonical not in techs:
                        techs.append(canonical)

            if role_match:
                role = role_match.group(1).strip()
                company = role_match.group(2).strip()
            else:
                role = first_line[:50]
                company = "Enterprise"

            date_str = date_match.group(0) if date_match else "Recent"
            is_current = "present" in date_str.lower() or "current" in date_str.lower()

            experiences.append(CandidateExperienceBase(
                company=company,
                role=role,
                location="Remote / Onsite",
                start_date=date_str,
                end_date="Present" if is_current else None,
                is_current=is_current,
                duration_months=24,
                description=block[:300],
                bullet_points=bullets if bullets else lines[1:],
                technologies=techs
            ))

        return experiences

    @staticmethod
    def extract_projects(projects_text: str) -> List[CandidateProjectBase]:
        projects: List[CandidateProjectBase] = []
        if not projects_text.strip():
            return projects

        blocks = re.split(r"\n\s*\n", projects_text.strip())
        for block in blocks:
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            if not lines:
                continue
            
            title = lines[0].lstrip("•-* ").strip()[:80]
            desc = " ".join(lines[1:]) if len(lines) > 1 else lines[0]
            
            techs = []
            for alias_lower, canonical in ontology.alias_to_canonical.items():
                if re.search(r"(?<!\w)" + re.escape(alias_lower) + r"(?!\w)", block, re.IGNORECASE):
                    if canonical not in techs:
                        techs.append(canonical)

            outcomes = [l for l in lines if any(re.search(mp, l) for mp in METRIC_PATTERNS)]
            url_match = re.search(r"(https?://[^\s]+|github\.com/[^\s]+)", block)
            url = url_match.group(0) if url_match else None

            projects.append(CandidateProjectBase(
                title=title,
                role="Lead Developer",
                description=desc,
                technologies=techs,
                outcomes=outcomes,
                url=url
            ))

        return projects

    @staticmethod
    def extract_education(edu_text: str) -> List[CandidateEducationBase]:
        educations: List[CandidateEducationBase] = []
        if not edu_text.strip():
            return educations

        lines = [l.strip() for l in edu_text.split("\n") if l.strip()]
        for line in lines:
            if len(line) < 5:
                continue
            year_match = re.search(r"\b(19\d{2}|20\d{2})\b", line)
            gpa_match = re.search(r"\bGPA:?\s*([0-4]\.\d{1,2})\b", line, re.IGNORECASE)
            
            degree = None
            for d in ["Bachelor", "B.S.", "B.A.", "Master", "M.S.", "Ph.D.", "Associate", "B.Tech", "M.Tech"]:
                if d.lower() in line.lower():
                    degree = d
                    break

            educations.append(CandidateEducationBase(
                institution=line[:60],
                degree=degree or "Degree / Certification",
                field_of_study="Computer Science & Engineering",
                graduation_year=year_match.group(0) if year_match else None,
                gpa=gpa_match.group(1) if gpa_match else None
            ))
        return educations

    @staticmethod
    def extract_certifications(cert_text: str) -> List[CandidateCertificationBase]:
        certs: List[CandidateCertificationBase] = []
        if not cert_text.strip():
            return certs

        lines = [l.strip() for l in cert_text.split("\n") if l.strip()]
        for line in lines:
            line_clean = line.lstrip("•-* ").strip()
            if len(line_clean) < 4:
                continue
            year_match = re.search(r"\b(19\d{2}|20\d{2})\b", line_clean)
            certs.append(CandidateCertificationBase(
                name=line_clean[:100],
                issuing_org=None,
                issue_date=year_match.group(0) if year_match else None
            ))
        return certs
