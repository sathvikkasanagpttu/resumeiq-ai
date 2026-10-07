import re
from typing import Dict, List, Tuple, Any, Optional
from sqlalchemy.orm import Session
from app.models.job import Job, JobVersion, JobRequirement, JobSkill
from app.services.ontology.taxonomy import ontology
from app.schemas.job import JobCreate
from app.core.logging import logger
from app.services.parser.document_reader import DocumentReader

SENIORITY_KEYWORDS = {
    "entry": ["entry", "junior", "associate", "graduate", "intern"],
    "mid": ["mid", "intermediate", "standard", "ii"],
    "senior": ["senior", "sr", "iii", "lead", "staff"],
    "lead": ["lead", "principal", "architect", "director", "head of", "vp"]
}

WORK_MODEL_KEYWORDS = {
    "remote": ["remote", "work from home", "wfh", "anywhere"],
    "hybrid": ["hybrid", "flexible", "partial remote"],
    "onsite": ["onsite", "in-person", "office only"]
}

class JobPipeline:
    @classmethod
    def parse_and_save(
        cls,
        db: Session,
        user_id: str,
        job_in: JobCreate
    ) -> Job:
        """
        Parses raw job description text, extracts structured requirements with classifications and weights,
        extracts normalized skills, and persists to DB.
        """
        # Sanitize and defend against prompt injections and hidden characters in untrusted JD
        clean_text, warnings = DocumentReader.sanitize_and_detect_hidden_text(job_in.description)
        text = clean_text
        if warnings:
            logger.warning(f"Security warnings on JD capture for user {user_id}: {warnings}")

        
        # 1. Infer Seniority if not set
        seniority = job_in.seniority or cls._detect_seniority(job_in.title + " " + text)
        
        # 2. Infer Work Model
        work_model = job_in.work_model or cls._detect_work_model(text)
        
        # 3. Infer Years of Experience
        exp_min, exp_max = cls._extract_experience_years(text)
        if job_in.experience_years_min and job_in.experience_years_min > 0:
            exp_min = job_in.experience_years_min

        # 4. Extract classified requirements
        classified_reqs = cls._extract_requirements(text)

        # 5. Extract Job Skills
        job_skills = cls._extract_skills(text, classified_reqs)

        # 6. Create Job model
        parsed_dict = {
            "seniority": seniority,
            "work_model": work_model,
            "experience_range": [exp_min, exp_max],
            "requirements_count": len(classified_reqs),
            "skills_count": len(job_skills)
        }
        if warnings:
            parsed_dict["security_warnings"] = warnings

        job = Job(
            user_id=user_id,
            title=job_in.title,
            company=job_in.company,
            description=text,
            raw_text=text,
            location=job_in.location or "Remote",
            work_model=work_model,
            seniority=seniority,
            experience_years_min=exp_min,
            experience_years_max=exp_max,
            parsed_data=parsed_dict
        )
        db.add(job)
        db.flush()

        # 7. Save Requirements
        for req in classified_reqs:
            db_req = JobRequirement(
                job_id=job.id,
                requirement_text=req["text"],
                category=req["category"],
                importance_weight=req["weight"],
                normalized_entities=req["entities"]
            )
            db.add(db_req)

        # 8. Save Job Skills
        for sk in job_skills:
            db_sk = JobSkill(
                job_id=job.id,
                skill_name=sk["name"],
                normalized_skill=sk["normalized"],
                is_required=sk["is_required"],
                importance_weight=sk["weight"],
                context_snippet=sk["context"]
            )
            db.add(db_sk)

        # 9. Create initial JobVersion
        version = JobVersion(
            job_id=job.id,
            version_num=1,
            change_summary="Initial job description ingest and structured analysis",
            content_snapshot={
                "requirements": [r["text"][:80] for r in classified_reqs],
                "skills": [s["normalized"] for s in job_skills]
            }
        )
        db.add(version)

        db.commit()
        db.refresh(job)
        logger.info(f"Job {job.id} parsed: {len(classified_reqs)} requirements, {len(job_skills)} skills identified")
        return job

    @classmethod
    def _detect_seniority(cls, text: str) -> str:
        text_lower = text.lower()
        for sen, kws in SENIORITY_KEYWORDS.items():
            if any(re.search(r"\b" + re.escape(kw) + r"\b", text_lower) for kw in kws):
                return sen
        return "mid"

    @classmethod
    def _detect_work_model(cls, text: str) -> str:
        text_lower = text.lower()
        for wm, kws in WORK_MODEL_KEYWORDS.items():
            if any(re.search(r"\b" + re.escape(kw) + r"\b", text_lower) for kw in kws):
                return wm
        return "remote"

    @classmethod
    def _extract_experience_years(cls, text: str) -> Tuple[float, Optional[float]]:
        # Examples: "5+ years", "3-5 years of experience", "minimum 4 years"
        match = re.search(r"\b(\d+)(?:\s*(?:-|to)\s*(\d+))?\+?\s*years?\b", text, re.IGNORECASE)
        if match:
            min_yrs = float(match.group(1))
            max_yrs = float(match.group(2)) if match.group(2) else None
            return min_yrs, max_yrs
        return 2.0, None

    @classmethod
    def _extract_requirements(cls, text: str) -> List[Dict[str, Any]]:
        """
        Splits job text into bullet points/sentences and categorizes each into:
        REQUIRED, PREFERRED, RESPONSIBILITY, QUALIFICATION, EXPERIENCE, DOMAIN, BEHAVIORAL, LOCATION
        with importance weight (0.1 - 1.0).
        """
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        current_section = "GENERAL"
        requirements: List[Dict[str, Any]] = []

        for line in lines:
            line_lower = line.lower()
            
            # Detect section header in job posting
            if any(k in line_lower for k in ["basic qualifications", "required qualifications", "must have", "requirements", "what you need"]):
                current_section = "REQUIRED"
                continue
            elif any(k in line_lower for k in ["preferred qualifications", "nice to have", "bonus points", "desired qualifications"]):
                current_section = "PREFERRED"
                continue
            elif any(k in line_lower for k in ["responsibilities", "what you will do", "duties", "role overview"]):
                current_section = "RESPONSIBILITY"
                continue

            # Skip short headers
            if len(line) < 10 or line.endswith(":") and len(line) < 40:
                continue

            cleaned_bullet = line.lstrip("•-*0123456789. ")
            if len(cleaned_bullet) < 15:
                continue

            # Determine category
            category = "REQUIRED"
            weight = 0.9

            if current_section == "PREFERRED" or any(p in line_lower for p in ["plus", "preferred", "nice to have", "bonus", "optional"]):
                category = "PREFERRED"
                weight = 0.6
            elif current_section == "RESPONSIBILITY" or any(p in line_lower for p in ["responsible for", "you will", "design and implement", "collaborate with"]):
                category = "RESPONSIBILITY"
                weight = 0.8
            elif re.search(r"\b(\d+\+?\s*years?|experience\s+with)\b", line_lower):
                category = "EXPERIENCE"
                weight = 0.95
            elif any(d in line_lower for d in ["degree", "bachelor", "master", "phd", "computer science"]):
                category = "QUALIFICATION"
                weight = 0.75
            elif any(b in line_lower for b in ["communication", "teamwork", "leadership", "adaptability", "passionate", "empathy"]):
                category = "BEHAVIORAL"
                weight = 0.5
            elif any(loc in line_lower for loc in ["relocation", "timezone", "est", "pst", "located in", "citizenship"]):
                category = "LOCATION"
                weight = 0.7
            elif any(dom in line_lower for dom in ["fintech", "healthcare", "e-commerce", "saas", "cybersecurity", "telecom"]):
                category = "DOMAIN"
                weight = 0.8
            elif current_section == "REQUIRED":
                category = "REQUIRED"
                weight = 1.0

            # Extract normalized entities in this requirement
            entities = []
            for alias_lower, canonical in ontology.alias_to_canonical.items():
                if re.search(r"\b" + re.escape(alias_lower) + r"\b", line_lower):
                    if canonical not in entities:
                        entities.append(canonical)

            requirements.append({
                "text": cleaned_bullet,
                "category": category,
                "weight": weight,
                "entities": entities
            })

        return requirements

    @classmethod
    def _extract_skills(cls, text: str, requirements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extracts all job skills from ontology, linking each with required status and weight.
        """
        skills_found: Dict[str, Dict[str, Any]] = {}
        text_lower = text.lower()

        for alias_lower, canonical in ontology.alias_to_canonical.items():
            pattern = r"\b" + re.escape(alias_lower) + r"\b"
            if re.search(pattern, text_lower):
                # Determine if it appears in a REQUIRED vs PREFERRED requirement
                is_req = True
                weight = 1.0
                snippet = ""

                for r in requirements:
                    if canonical in r["entities"]:
                        snippet = r["text"]
                        if r["category"] == "PREFERRED":
                            is_req = False
                            weight = 0.65
                        else:
                            is_req = True
                            weight = r["weight"]
                        break

                if canonical not in skills_found or (is_req and not skills_found[canonical]["is_required"]):
                    skills_found[canonical] = {
                        "name": canonical,
                        "normalized": canonical,
                        "is_required": is_req,
                        "weight": weight,
                        "context": snippet or f"Found in job description: {canonical}"
                    }

        return list(skills_found.values())
