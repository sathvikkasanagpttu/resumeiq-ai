from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.resume import Resume
from app.models.audit import AuditLog
from app.schemas.resume import ResumeResponse, ResumeDetailResponse
from app.services.parser.resume_pipeline import ResumePipeline
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/upload", response_model=ResumeDetailResponse)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contents = await file.read()
    filename = file.filename or "resume.txt"

    resume = ResumePipeline.process_and_save(
        db=db,
        user_id=current_user.id,
        filename=filename,
        file_bytes=contents
    )

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="upload_resume",
        resource_type="resume",
        resource_id=resume.id,
        details={"filename": filename, "file_size": len(contents)}
    )
    db.add(audit)
    db.commit()

    return resume

@router.get("", response_model=List[ResumeResponse])
def list_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resumes = db.query(Resume).filter(Resume.user_id == current_user.id).all()
    results = []
    for r in resumes:
        results.append(ResumeResponse(
            id=r.id,
            user_id=r.user_id,
            filename=r.filename,
            file_type=r.file_type,
            file_size=r.file_size,
            is_active=r.is_active,
            created_at=r.created_at,
            skills_count=len(r.skills),
            experience_count=len(r.experiences)
        ))
    return results

@router.get("/{resume_id}", response_model=ResumeDetailResponse)
def get_resume(
    resume_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    # Security: ownership check
    if resume.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied to this resume")
    return resume

@router.delete("/{resume_id}")
def delete_resume(
    resume_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if resume.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    db.delete(resume)
    db.commit()
    return {"status": "success", "message": "Resume deleted successfully"}
