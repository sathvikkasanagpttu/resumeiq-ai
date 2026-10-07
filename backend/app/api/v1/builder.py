import io
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, Request, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.rate_limit import check_user_and_ip_limits
from app.api.deps import get_current_user
from app.models.user import User
from app.models.resume import Resume, ResumeVersion, ResumeDiffItem, ApplicationTrackerItem, InterviewPrepSession
from app.schemas.builder import (
    GenerateResumeRequest, DiffReviewAction, ResumeDiffResponse, ResumeVersionResponse,
    WizardAnswerSubmission, ExternalImportRequest,
    TrackerItemCreate, TrackerItemUpdate, TrackerItemResponse,
    InterviewPrepGenerateRequest, InterviewPrepResponse
)
from app.schemas.wizard import WizardSessionResponse, WizardSubmitResponse
from app.schemas.quality import QualityReportResponse
from app.schemas.canonical_profile import CanonicalProfile
from app.services.builder.generation_engine import ResumeGenerator
from app.services.builder.exporters import ResumeExporter
from app.services.wizard.wizard_service import WizardService
from app.services.quality.quality_analyzer import QualityAnalyzer
from app.services.quality.external_importer import ExternalImporter
from app.services.career.interview_prep_service import InterviewPrepService
from app.core.logging import logger

router = APIRouter()

# -------------------------------------------------------------
# Auto Resume Builder & Generation
# -------------------------------------------------------------
@router.post("/generate", response_model=ResumeVersionResponse)
def generate_resume_version(
    req: GenerateResumeRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_user_and_ip_limits(
        request=request,
        user_id=current_user.id,
        action="builder_generation",
        user_limit=20,
        ip_limit=40,
        window_seconds=60
    )
    resume = db.query(Resume).filter(
        Resume.id == req.resume_id,
        Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    version = ResumeGenerator.generate_version(db=db, user_id=current_user.id, request=req)
    return version

@router.get("/versions/{resume_id}", response_model=List[ResumeVersionResponse])
def get_resume_versions(
    resume_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    versions = db.query(ResumeVersion).filter(
        ResumeVersion.resume_id == resume_id
    ).order_by(ResumeVersion.version_num.desc()).all()
    return versions

@router.get("/version/{version_id}", response_model=ResumeVersionResponse)
def get_resume_version_detail(
    version_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    version = db.query(ResumeVersion).filter(ResumeVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found.")
    return version

@router.post("/diff/review", response_model=ResumeDiffResponse)
def review_bullet_diff(
    action_req: DiffReviewAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        updated_diff = ResumeGenerator.review_diff(
            db=db,
            user_id=current_user.id,
            diff_id=action_req.diff_id,
            action=action_req.action,
            edited_text=action_req.edited_text
        )
        return updated_diff
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# -------------------------------------------------------------
# Missing-Info Wizard
# -------------------------------------------------------------
@router.get("/wizard/questions/{resume_id}", response_model=WizardSessionResponse)
def get_wizard_questions(
    resume_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    raw_canonical = (resume.parsed_data or {}).get("canonical_profile")
    if not raw_canonical:
        from app.services.parser.canonical_builder import CanonicalProfileBuilder
        raw_canonical = CanonicalProfileBuilder.build_from_parsed_data(
            raw_text=resume.raw_text,
            contacts=(resume.parsed_data or {}).get("contacts", {}),
            sections_dict={s.section_type: s.raw_content for s in resume.sections},
            skills=resume.skills,
            experiences=resume.experiences,
            projects=resume.projects,
            educations=resume.educations,
            certifications=resume.certifications
        ).model_dump()

    profile = CanonicalProfile.model_validate(raw_canonical)
    return WizardService.generate_questions(resume=resume, profile=profile)

@router.post("/wizard/answers", response_model=WizardSubmitResponse)
def submit_wizard_answers(
    sub: WizardAnswerSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return WizardService.apply_answers(
            db=db,
            user_id=current_user.id,
            resume_id=sub.resume_id,
            answers=sub.answers
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# -------------------------------------------------------------
# Quality Report & External Import
# -------------------------------------------------------------
@router.get("/quality/{resume_id}", response_model=QualityReportResponse)
def get_quality_report(
    resume_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")
    raw_canonical = (resume.parsed_data or {}).get("canonical_profile")
    if not raw_canonical:
        from app.services.parser.canonical_builder import CanonicalProfileBuilder
        raw_canonical = CanonicalProfileBuilder.build_from_parsed_data(
            raw_text=resume.raw_text,
            contacts=(resume.parsed_data or {}).get("contacts", {}),
            sections_dict={s.section_type: s.raw_content for s in resume.sections},
            skills=resume.skills,
            experiences=resume.experiences,
            projects=resume.projects,
            educations=resume.educations,
            certifications=resume.certifications
        ).model_dump()

    profile = CanonicalProfile.model_validate(raw_canonical)
    return QualityAnalyzer.analyze_resume(resume_id=resume.id, profile=profile)

@router.post("/import-external")
def import_external_profile(
    req: ExternalImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        facts = ExternalImporter.import_profile(
            db=db,
            user_id=current_user.id,
            resume_id=req.resume_id,
            platform=req.platform,
            raw_text=req.raw_text
        )
        return {
            "status": "success",
            "platform": req.platform,
            "facts_imported": len(facts),
            "message": f"Successfully imported {len(facts)} verified facts from {req.platform}."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# -------------------------------------------------------------
# Multi-Format Resume Exporter (PDF, DOCX, TXT, JSON, HTML)
# -------------------------------------------------------------
@router.get("/export/{version_id}")
def export_resume_version(
    version_id: str,
    format: str = Query("pdf", pattern="^(pdf|docx|txt|json|html)$"),
    redact_pii: bool = Query(False, description="Enable PII redaction for blind screening"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    version = db.query(ResumeVersion).filter(ResumeVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found.")

    profile_dict = version.canonical_profile or {}
    profile = CanonicalProfile.model_validate(profile_dict)
    if redact_pii:
        profile = profile.get_redacted_copy()
    filename_base = f"resume_v{version.version_num}_{version.template_id}"

    if format == "json":
        json_content = ResumeExporter.to_json(profile)
        return Response(
            content=json_content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.json"'}
        )
    elif format == "txt":
        txt_content = ResumeExporter.to_txt(profile)
        return Response(
            content=txt_content,
            media_type="text/plain",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.txt"'}
        )
    elif format == "html":
        html_content = ResumeExporter.to_html(profile, template_id=version.template_id, mode=version.mode)
        return Response(
            content=html_content,
            media_type="text/html",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.html"'}
        )
    elif format == "docx":
        docx_bytes = ResumeExporter.to_docx(profile, template_id=version.template_id)
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.docx"'}
        )
    else:  # pdf
        pdf_bytes = ResumeExporter.to_pdf(profile, template_id=version.template_id)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.pdf"'}
        )

# -------------------------------------------------------------
# Application Tracker & Outcome Analytics
# -------------------------------------------------------------
@router.get("/tracker", response_model=List[TrackerItemResponse])
def get_tracker_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    items = db.query(ApplicationTrackerItem).filter(
        ApplicationTrackerItem.user_id == current_user.id
    ).order_by(ApplicationTrackerItem.created_at.desc()).all()
    return [
        TrackerItemResponse(
            id=it.id,
            user_id=it.user_id,
            job_title=it.role_title,
            company_name=it.company,
            stage=it.status,
            resume_version_id=it.resume_version_id,
            target_job_id=it.job_id,
            notes=it.outcome_notes,
            created_at=it.created_at,
            updated_at=it.updated_at
        ) for it in items
    ]

@router.post("/tracker", response_model=TrackerItemResponse)
def create_tracker_item(
    req: TrackerItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    import uuid
    item = ApplicationTrackerItem(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        job_id=req.target_job_id,
        resume_version_id=req.resume_version_id,
        role_title=req.job_title,
        company=req.company_name,
        status=req.stage,
        outcome_notes=req.notes
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return TrackerItemResponse(
        id=item.id,
        user_id=item.user_id,
        job_title=item.role_title,
        company_name=item.company,
        stage=item.status,
        resume_version_id=item.resume_version_id,
        target_job_id=item.job_id,
        notes=item.outcome_notes,
        created_at=item.created_at,
        updated_at=item.updated_at
    )

@router.patch("/tracker/{item_id}", response_model=TrackerItemResponse)
def update_tracker_item(
    item_id: str,
    req: TrackerItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.query(ApplicationTrackerItem).filter(
        ApplicationTrackerItem.id == item_id,
        ApplicationTrackerItem.user_id == current_user.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Tracker item not found.")

    if req.stage is not None:
        item.status = req.stage
    if req.notes is not None:
        item.outcome_notes = req.notes

    db.commit()
    db.refresh(item)
    return TrackerItemResponse(
        id=item.id,
        user_id=item.user_id,
        job_title=item.role_title,
        company_name=item.company,
        stage=item.status,
        resume_version_id=item.resume_version_id,
        target_job_id=item.job_id,
        notes=item.outcome_notes,
        created_at=item.created_at,
        updated_at=item.updated_at
    )

@router.delete("/tracker/{item_id}")
def delete_tracker_item(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.query(ApplicationTrackerItem).filter(
        ApplicationTrackerItem.id == item_id,
        ApplicationTrackerItem.user_id == current_user.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Tracker item not found.")

    db.delete(item)
    db.commit()
    return {"status": "success", "message": "Tracker item deleted."}

# -------------------------------------------------------------
# Interview Prep STAR Engine
# -------------------------------------------------------------
@router.post("/interview-prep", response_model=InterviewPrepResponse)
def generate_interview_prep(
    req: InterviewPrepGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return InterviewPrepService.generate_prep(
            db=db,
            user_id=current_user.id,
            resume_id=req.resume_id,
            target_role=req.target_role
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
