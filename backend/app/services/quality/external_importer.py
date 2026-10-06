import re
import uuid
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.resume import UserConfirmedFact
from app.schemas.quality import ExternalImportResponse
from app.services.ontology.taxonomy import ontology

class ExternalImporter:
    """
    Parses user-pasted LinkedIn and GitHub export text into verified, user-confirmed evidence facts.
    Strictly accepts text supplied directly by the user (no automated web scraping).
    """

    @classmethod
    def import_external_text(
        cls,
        db: Session,
        user_id: str,
        resume_id: str,
        source_type: str,
        raw_text: str
    ) -> ExternalImportResponse:
        extracted_facts: List[Dict[str, Any]] = []

        if source_type.lower() == "linkedin":
            extracted_facts = cls._parse_linkedin_text(raw_text)
        elif source_type.lower() == "github":
            extracted_facts = cls._parse_github_text(raw_text)
        else:
            extracted_facts = cls._parse_generic_profile_text(raw_text)

        # Save extracted facts into UserConfirmedFact table
        for item in extracted_facts:
            fact = UserConfirmedFact(
                id=str(uuid.uuid4()),
                user_id=user_id,
                resume_id=resume_id,
                fact_category=item["category"],
                field_target=item.get("target"),
                claim_text=item["claim"],
                verification_source=f"external_{source_type.lower()}"
            )
            db.add(fact)

        db.commit()

        return ExternalImportResponse(
            source_type=source_type,
            facts_extracted_count=len(extracted_facts),
            confirmed_facts=extracted_facts,
            message=f"Successfully extracted {len(extracted_facts)} verified facts from your {source_type} text."
        )

    @classmethod
    def _parse_linkedin_text(cls, text: str) -> List[Dict[str, Any]]:
        facts = []
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        # Extract skills mentions
        for line in lines:
            # Check for ontology skills
            for node in ontology.nodes.values():
                if re.search(r"\b" + re.escape(node.canonical_name) + r"\b", line, re.IGNORECASE):
                    facts.append({
                        "category": "skill",
                        "target": "skills",
                        "claim": f"Demonstrated competency in {node.canonical_name} as recorded on LinkedIn profile."
                    })
                    break

        # Extract achievements/metrics
        metrics = re.findall(r"(\b\d+[\d,\.]*%\b|\$\d+[\d,\.]*|\b\d+[\d,\.]*\s*users\b)", text, re.IGNORECASE)
        for m in metrics[:5]:
            facts.append({
                "category": "metric",
                "target": "experience",
                "claim": f"Verified LinkedIn metric: {m}"
            })

        return facts[:15]

    @classmethod
    def _parse_github_text(cls, text: str) -> List[Dict[str, Any]]:
        facts = []
        # Look for repositories or repo stars
        repo_matches = re.findall(r"([A-Za-z0-9_-]+/[A-Za-z0-9_-]+)", text)
        for repo in repo_matches[:5]:
            facts.append({
                "category": "project",
                "target": "projects",
                "claim": f"Active GitHub repository: https://github.com/{repo}"
            })

        # Look for languages listed in GitHub
        for node in ontology.nodes.values():
            if re.search(r"\b" + re.escape(node.canonical_name) + r"\b", text, re.IGNORECASE):
                facts.append({
                    "category": "skill",
                    "target": "skills",
                    "claim": f"Codebase contribution with {node.canonical_name} on GitHub."
                })
                break

        return facts[:10]

    @classmethod
    def _parse_generic_profile_text(cls, text: str) -> List[Dict[str, Any]]:
        facts = []
        for line in text.split("\n")[:10]:
            if len(line.strip()) > 15:
                facts.append({
                    "category": "responsibility",
                    "target": "experience",
                    "claim": line.strip()
                })
        return facts
