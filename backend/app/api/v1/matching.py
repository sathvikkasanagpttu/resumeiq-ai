from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.resume import Resume
from app.models.job import Job
from app.models.matching import Match
from app.schemas.matching import MatchRequest, MatchResponse, MatchComponentResponse
from app.services.matching.hybrid_matcher import HybridMatcher
from app.api.deps import get_current_user

router = APIRouter()

@router.post("", response_model=MatchResponse)
def compute_match(
    req: MatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = db.query(Resume).filter(Resume.id == req.resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if resume.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied to resume")

    job = db.query(Job).filter(Job.id == req.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    match = HybridMatcher.compute_match(
        db=db,
        resume=resume,
        job=job,
        custom_weights=req.weights
    )
    return match

@router.get("/{match_id}", response_model=MatchResponse)
def get_match(
    match_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.resume.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return match

@router.get("/resume/{resume_id}", response_model=List[MatchResponse])
def get_resume_matches(
    resume_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if resume.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    matches = db.query(Match).filter(Match.resume_id == resume_id).all()
    return matches
