from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.resume import Resume
from app.models.audit import AuditLog
from app.schemas.resume import ResumeResponse, ResumeDetailResponse
from app.services.parser.resume_pipeline import ResumePipeline
from app.api.deps import get_current_user

router = APIRouter()

import io
import re
from pathlib import Path
from app.core.config import settings
from app.core.rate_limit import rate_limiter, check_user_and_ip_limits
from app.core.exceptions import DocumentParsingError

@router.post("/upload", response_model=ResumeDetailResponse)
async def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Rate limiting on resume upload (per-user and per-IP)
    check_user_and_ip_limits(
        request=request,
        user_id=current_user.id,
        action="resume_upload",
        user_limit=15,
        ip_limit=30,
        window_seconds=60
    )

    # 2. Sanitize filename: strip path traversal and special characters
    raw_name = Path(file.filename or "resume.txt").name
    clean_filename = re.sub(r"[^\w\.-]", "_", raw_name)

    # 3. Stream content in 64KB chunks to enforce size limit while streaming
    chunk_size = 64 * 1024
    total_bytes = 0
    buffer = io.BytesIO()

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total_bytes += len(chunk)
        if total_bytes > settings.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum upload size limit of {settings.MAX_UPLOAD_SIZE_BYTES / (1024 * 1024):.0f}MB"
            )
        buffer.write(chunk)

    contents = buffer.getvalue()

    try:
        resume = ResumePipeline.process_and_save(
            db=db,
            user_id=current_user.id,
            filename=clean_filename,
            file_bytes=contents
        )
    except DocumentParsingError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail if hasattr(e, 'detail') else e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to process document: {str(e)}")

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="upload_resume",
        resource_type="resume",
        resource_id=resume.id,
        details={"filename": clean_filename, "file_size": len(contents)}
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
