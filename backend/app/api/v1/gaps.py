from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.matching import Match
from app.schemas.gap import SkillGapReport
from app.services.career.gap_analyzer import gap_analyzer
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/match/{match_id}", response_model=SkillGapReport)
def get_gap_report(
    match_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.resume.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    return gap_analyzer.get_gap_report(db, match)
