from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from app.models.resume import Resume
from app.models.evidence import EvidenceItem

class EvidenceNode:
    def __init__(self, node_id: str, node_type: str, label: str, metadata: Dict[str, Any]):
        self.node_id = node_id
        self.node_type = node_type  # candidate, skill, project, experience, quote
        self.label = label
        self.metadata = metadata
        self.edges: List["EvidenceNode"] = []

class EvidenceGraph:
    """
    Evidence Graph representing relational lineage:
    Candidate -> Skill -> Project / Experience -> Exact Resume Evidence
    Enables explainable answers to:
    'Why does the system believe this candidate has Python experience?'
    """
    def __init__(self, resume: Resume):
        self.resume = resume
        self.graph: Dict[str, List[Dict[str, Any]]] = {}
        self._build_graph()

    def _build_graph(self):
        # Index skills
        for sk in self.resume.skills:
            norm_skill = sk.normalized_skill.lower()
            if norm_skill not in self.graph:
                self.graph[norm_skill] = []

            # Find matching experiences
            related_exps = []
            for exp in self.resume.experiences:
                if sk.normalized_skill in (exp.technologies or []):
                    related_exps.append({
                        "company": exp.company,
                        "role": exp.role,
                        "date": exp.start_date
                    })

            # Find matching projects
            related_projs = []
            for proj in self.resume.projects:
                if sk.normalized_skill in (proj.technologies or []):
                    related_projs.append({
                        "title": proj.title,
                        "description": proj.description[:120]
                    })

            # Find exact evidence quotes
            quotes = []
            for ev in self.resume.evidence_items:
                if ev.entity_name.lower() == norm_skill:
                    quotes.append({
                        "quote": ev.context_snippet,
                        "section": ev.source_section,
                        "strength": ev.evidence_strength,
                        "confidence": ev.confidence_score,
                        "action_verb": ev.action_verb,
                        "metric": ev.quantified_impact
                    })

            self.graph[norm_skill].append({
                "canonical_skill": sk.normalized_skill,
                "evidence_strength": sk.evidence_strength,
                "confidence": sk.confidence,
                "source_evidence": sk.source_evidence,
                "related_experiences": related_exps,
                "related_projects": related_projs,
                "exact_quotes": quotes
            })

    def explain_skill_evidence(self, skill_name: str) -> Dict[str, Any]:
        """
        Answers: 'Why does the system believe this candidate has <skill_name> experience?'
        Returns citations, associated experiences, projects, and confidence.
        """
        norm = skill_name.strip().lower()
        if norm not in self.graph or not self.graph[norm]:
            return {
                "skill": skill_name,
                "status": "unsupported",
                "confidence": 0.0,
                "evidence_strength": "missing",
                "explanation": f"No explicit or verified evidence for '{skill_name}' exists in candidate resume.",
                "citations": []
            }

        data = self.graph[norm][0]
        return {
            "skill": data["canonical_skill"],
            "status": "supported" if data["evidence_strength"] == "verified" else "partially_supported",
            "confidence": data["confidence"],
            "evidence_strength": data["evidence_strength"],
            "explanation": (
                f"Candidate demonstrated '{data['canonical_skill']}' in {len(data['related_experiences'])} work experience(s) "
                f"and {len(data['related_projects'])} project(s) with '{data['evidence_strength']}' evidence."
            ),
            "primary_evidence": data["source_evidence"],
            "related_experiences": data["related_experiences"],
            "related_projects": data["related_projects"],
            "citations": data["exact_quotes"]
        }

    def to_cytoscape_elements(self) -> List[Dict[str, Any]]:
        """
        Exports the graph to nodes and edges for frontend graph visualization.
        """
        elements: List[Dict[str, Any]] = []
        root_id = "candidate_root"
        elements.append({
            "data": {"id": root_id, "label": "Candidate Profile", "type": "candidate"}
        })

        for skill_norm, items in self.graph.items():
            if not items:
                continue
            item = items[0]
            skill_id = f"skill_{skill_norm}"
            elements.append({
                "data": {
                    "id": skill_id,
                    "label": item["canonical_skill"],
                    "type": "skill",
                    "strength": item["evidence_strength"]
                }
            })
            elements.append({
                "data": {"source": root_id, "target": skill_id, "label": "possesses"}
            })

            # Add connected experiences
            for i, exp in enumerate(item["related_experiences"][:2]):
                exp_id = f"exp_{skill_norm}_{i}"
                elements.append({
                    "data": {"id": exp_id, "label": f"{exp['role']} @ {exp['company']}", "type": "experience"}
                })
                elements.append({
                    "data": {"source": skill_id, "target": exp_id, "label": "applied_in"}
                })

        return elements
