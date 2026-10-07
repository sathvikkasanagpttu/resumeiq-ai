from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.resume import Resume
from app.schemas.analytics import MarketAnalyticsResponse
from app.services.analytics.market_analytics import market_analytics_engine
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("", response_model=MarketAnalyticsResponse)
def get_market_analytics(
    resume_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    candidate_resume = None
    if resume_id:
        candidate_resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not candidate_resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        if candidate_resume.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Access denied to requested resume analytics")

    return market_analytics_engine.analyze_market(
        db=db,
        candidate_resume=candidate_resume
    )
