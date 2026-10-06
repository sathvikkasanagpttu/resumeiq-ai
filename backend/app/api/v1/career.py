from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.matching import Match
from app.models.resume import Resume
from app.schemas.career import CareerRoadmapResponse, JobRecommendationsResponse
from app.services.career.roadmap import career_roadmap_service
from app.services.career.recommendations import job_recommendation_engine
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/roadmap/match/{match_id}", response_model=CareerRoadmapResponse)
def get_career_roadmap(
    match_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.resume.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    return career_roadmap_service.generate_roadmap(db, match)

@router.get("/recommendations/resume/{resume_id}", response_model=JobRecommendationsResponse)
def get_job_recommendations(
    resume_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if resume.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    return job_recommendation_engine.recommend_jobs(db, resume)
