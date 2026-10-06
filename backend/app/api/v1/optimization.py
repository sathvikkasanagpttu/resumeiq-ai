from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.matching import Match
from app.schemas.optimization import ResumeOptimizationResponse
from app.services.llm.optimizer import resume_optimizer
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/match/{match_id}", response_model=ResumeOptimizationResponse)
def get_resume_optimization(
    match_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.resume.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    return resume_optimizer.optimize(db, match)
