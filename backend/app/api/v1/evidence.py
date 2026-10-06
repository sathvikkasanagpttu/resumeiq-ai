from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.resume import Resume
from app.schemas.evidence import VerificationClaim
from app.services.evidence.evidence_graph import EvidenceGraph
from app.services.evidence.verification import verification_pipeline
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/{resume_id}/skill/{skill_name}")
def explain_skill_evidence(
    resume_id: str,
    skill_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if resume.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    graph = EvidenceGraph(resume)
    return graph.explain_skill_evidence(skill_name)

@router.get("/{resume_id}/graph")
def get_evidence_graph_elements(
    resume_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if resume.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    graph = EvidenceGraph(resume)
    return {"elements": graph.to_cytoscape_elements()}

@router.post("/{resume_id}/verify-claim", response_model=VerificationClaim)
def verify_claim(
    resume_id: str,
    claim_text: str,
    target_entity: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if resume.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    return verification_pipeline.verify_claim(
        resume=resume,
        claim_text=claim_text,
        target_entity=target_entity
    )
