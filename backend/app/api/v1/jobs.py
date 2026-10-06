from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.job import Job
from app.models.audit import AuditLog
from app.schemas.job import JobCreate, JobResponse, JobDetailResponse
from app.services.job.job_pipeline import JobPipeline
from app.api.deps import get_current_user

router = APIRouter()

@router.post("", response_model=JobDetailResponse)
def create_job(
    job_in: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = JobPipeline.parse_and_save(
        db=db,
        user_id=current_user.id,
        job_in=job_in
    )

    audit = AuditLog(
        user_id=current_user.id,
        action="create_job",
        resource_type="job",
        resource_id=job.id,
        details={"title": job.title, "company": job.company}
    )
    db.add(audit)
    db.commit()

    return job

@router.get("", response_model=List[JobResponse])
def list_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    jobs = db.query(Job).filter(Job.is_active == True).all()
    results = []
    for j in jobs:
        results.append(JobResponse(
            id=j.id,
            user_id=j.user_id,
            title=j.title,
            company=j.company,
            location=j.location,
            work_model=j.work_model,
            seniority=j.seniority,
            experience_years_min=j.experience_years_min,
            is_active=j.is_active,
            created_at=j.created_at,
            requirements_count=len(j.requirements),
            skills_count=len(j.skills)
        ))
    return results

@router.get("/{job_id}", response_model=JobDetailResponse)
def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.delete("/{job_id}")
def delete_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    db.delete(job)
    db.commit()
    return {"status": "success", "message": "Job posting deleted"}
