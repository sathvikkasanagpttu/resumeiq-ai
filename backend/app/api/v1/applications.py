from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.matching import Match, GeneratedDocument
from app.schemas.application import GeneratedMaterialRequest, GeneratedMaterialResponse
from app.services.llm.application_gen import application_generator
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/generate", response_model=GeneratedMaterialResponse)
def generate_application_material(
    req: GeneratedMaterialRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    match = db.query(Match).filter(Match.id == req.match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.resume.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    return application_generator.generate_material(
        db=db,
        user_id=current_user.id,
        request=req,
        match=match
    )
