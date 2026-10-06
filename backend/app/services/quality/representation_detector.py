from typing import List, Set
from app.schemas.canonical_profile import CanonicalProfile
from app.schemas.quality import ImpliedSkillSuggestion
from app.services.ontology.taxonomy import ontology

class RepresentationGapDetector:
    """
    Detects implied skills that are strongly suggested by project or experience descriptions
    but never explicitly stated in the candidate's skills section.
    Surfaces these as non-presumptive questions for the candidate to confirm.
    """

    IMPLICATION_RULES = [
        # (trigger_keywords, implied_skill, domain_explanation)
        (["fastapi", "flask", "django", "pandas", "numpy"], "Python", "Python backend frameworks and data tools"),
        (["react", "next.js", "vue", "angular", "node.js"], "JavaScript", "Modern web and frontend ecosystems"),
        (["postgresql", "mysql", "sql server", "sqlite", "oracle"], "SQL", "Relational database querying and modeling"),
        (["docker", "kubernetes", "ecs", "helm"], "Containerization", "Container orchestration and deployments"),
        (["aws", "gcp", "azure", "ec2", "s3", "lambda"], "Cloud Architecture", "Public cloud computing infrastructure"),
        (["microservices", "rest api", "restful apis", "endpoints"], "API Design", "Distributed RESTful service architecture"),
        (["power bi", "tableau", "looker"], "Business Intelligence", "Executive dashboarding and data analytics"),
        (["pytorch", "tensorflow", "keras"], "Deep Learning", "Neural network architecture and training"),
    ]

    @classmethod
    def detect_gaps(cls, profile: CanonicalProfile) -> List[ImpliedSkillSuggestion]:
        # Collect all explicitly named skills
        explicit_skills: Set[str] = set()
        for cat in profile.skills:
            for s in cat.skills:
                explicit_skills.add(s.name.lower())
                explicit_skills.add(s.normalized_name.lower())

        # Collect all text from experience bullets and project descriptions
        experience_texts = []
        for exp in profile.experience:
            c_name = str(exp.company.value or "Experience")
            for b in exp.highlights:
                experience_texts.append((b.value, f"Experience @ {c_name}"))

        for proj in profile.projects:
            p_name = str(proj.name.value or "Project")
            for b in proj.highlights:
                experience_texts.append((b.value, f"Project '{p_name}'"))

        suggestions: List[ImpliedSkillSuggestion] = []
        seen_implied = set()

        for text, section_name in experience_texts:
            text_lower = text.lower()
            for triggers, implied_skill, rationale in cls.IMPLICATION_RULES:
                if implied_skill.lower() in explicit_skills or implied_skill.lower() in seen_implied:
                    continue

                for trigger in triggers:
                    if trigger in text_lower:
                        seen_implied.add(implied_skill.lower())
                        suggestions.append(ImpliedSkillSuggestion(
                            implied_skill=implied_skill,
                            trigger_text=text[:100],
                            context_section=section_name,
                            rationale=f"Mentioning '{trigger}' in {section_name} strongly indicates practical exposure to {rationale}.",
                            suggested_question=(
                                f"Your {section_name} mentions '{trigger}'. "
                                f"Do you have hands-on experience with {implied_skill}? "
                                f"Confirm to add {implied_skill} to your verified skills."
                            )
                        ))
                        break

        return suggestions
