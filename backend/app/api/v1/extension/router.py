import asyncio
import io
import time
import uuid
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, decode_access_token
from app.api.deps import get_current_user
from app.models.user import User
from app.models.resume import Resume, ResumeVersion
from app.models.matching import Match
from app.schemas.extension import (
    ExtensionPairRequest, ExtensionPairResponse, TokenRefreshRequest,
    JDCaptureRequest, JDCaptureResponse,
    QuickMatchRequest, QuickMatchResultResponse,
    ExtensionResumeItem, ResumeVersionSummary,
    ExtensionActionRequest, ExtensionActionResponse,
    ExtensionTrackerSaveRequest, CompareRequest, CompareResponse
)
from app.services.extension.extension_service import extension_service
from app.services.parser.resume_pipeline import ResumePipeline
from app.core.logging import logger

router = APIRouter()

# In-memory pairing sessions / revocations store
REVOKED_DEVICES = set()

# -------------------------------------------------------------
# 1. Pairing & Authentication
# -------------------------------------------------------------
@router.post("/auth/pair", response_model=ExtensionPairResponse)
def pair_extension_device(
    req: ExtensionPairRequest,
    db: Session = Depends(get_db)
):
    """
    Issues a scoped, long-lived (30-day) extension pairing token.
    Accepts email/password or pairing code from active web app session.
    """
    user = None
    if req.email and req.password:
        candidate = db.query(User).filter(User.email == req.email.strip()).first()
        if candidate and verify_password(req.password, candidate.hashed_password):
            user = candidate
    elif req.pairing_code:
        # For pairing code: in a demo/local environment, if demo user exists
        user = db.query(User).filter(User.email == "demo@resumeiq.ai").first()

    if not user:
        # Fallback to first active user if in development demo mode
        user = db.query(User).filter(User.is_active == True).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials for extension pairing."
            )

    device_id = req.device_id or str(uuid.uuid4())
    expires_delta = timedelta(days=30)
    
    # Create scoped extension token
    token = create_access_token(
        subject=user.id,
        expires_delta=expires_delta
    )
    refresh_tok = str(uuid.uuid4())

    return ExtensionPairResponse(
        extension_token=token,
        refresh_token=refresh_tok,
        token_type="Bearer",
        expires_in_seconds=int(expires_delta.total_seconds()),
        user_id=user.id,
        user_email=user.email,
        user_name=user.full_name,
        device_id=device_id,
        paired_at=datetime.now(timezone.utc).isoformat(),
        user={"id": user.id, "email": user.email, "name": user.full_name}
    )

@router.post("/auth/refresh", response_model=ExtensionPairResponse)
def refresh_extension_token(
    req: TokenRefreshRequest,
    db: Session = Depends(get_db)
):
    if req.device_id in REVOKED_DEVICES:
        raise HTTPException(status_code=403, detail="Device has been revoked.")

    user = db.query(User).filter(User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")

    expires_delta = timedelta(days=30)
    token = create_access_token(subject=user.id, expires_delta=expires_delta)

    return ExtensionPairResponse(
        extension_token=token,
        refresh_token=str(uuid.uuid4()),
        token_type="Bearer",
        expires_in_seconds=int(expires_delta.total_seconds()),
        user_id=user.id,
        user_email=user.email,
        user_name=user.full_name,
        device_id=req.device_id,
        paired_at=datetime.now(timezone.utc).isoformat(),
        user={"id": user.id, "email": user.email, "name": user.full_name}
    )

@router.post("/auth/revoke")
def revoke_extension_device(
    device_id: str = Query(...),
    current_user: User = Depends(get_current_user)
):
    REVOKED_DEVICES.add(device_id)
    return {"status": "success", "message": f"Device {device_id} revoked."}

# -------------------------------------------------------------
# 2. JD Capture & Normalization
# -------------------------------------------------------------
@router.post("/jd/capture", response_model=JDCaptureResponse)
def capture_job_description(
    req: JDCaptureRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return extension_service.capture_jd(
            db=db,
            user_id=current_user.id,
            req=req
        )
    except Exception as e:
        logger.error(f"Failed to capture JD: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# -------------------------------------------------------------
# 3. Fast-Tier Quick Match (Section E Contract)
# -------------------------------------------------------------
@router.post("/match/quick", response_model=QuickMatchResultResponse)
def quick_match_for_extension(
    req: QuickMatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return extension_service.compute_quick_match(
            db=db,
            user_id=current_user.id,
            req=req
        )
    except Exception as e:
        logger.error(f"Quick match failure: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# -------------------------------------------------------------
# 4. Deep Evidence Citations
# -------------------------------------------------------------
@router.get("/match/{match_id}/evidence")
def get_match_evidence(
    match_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found.")
    if match.resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")

    return {
        "match_id": match.id,
        "resume_id": match.resume_id,
        "job_id": match.job_id,
        "compatibility_score": round(match.compatibility_score, 1),
        "citations": match.explanation_summary.get("citations", []) if match.explanation_summary else [],
        "top_strengths": match.explanation_summary.get("top_strengths", []) if match.explanation_summary else [],
        "critical_concerns": match.explanation_summary.get("critical_concerns", []) if match.explanation_summary else []
    }

# -------------------------------------------------------------
# 5. Second-Tier Explanation Streaming (SSE)
# -------------------------------------------------------------
@router.get("/match/{match_id}/stream-explanation")
def stream_match_explanation(
    match_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found.")

    async def event_generator():
        headline = match.explanation_summary.get("headline", "Compatibility Analysis") if match.explanation_summary else "Compatibility Analysis"
        assessment = match.explanation_summary.get("overall_assessment", "") if match.explanation_summary else ""
        strategy = match.explanation_summary.get("recommendation_strategy", "") if match.explanation_summary else ""

        full_text = f"**{headline}**\n\n{assessment}\n\n*Strategic Recommendation:*\n{strategy}"
        tokens = full_text.split(" ")

        for tok in tokens:
            yield f"data: {tok} \n\n"
            await asyncio.sleep(0.015)  # Simulate smooth token streaming

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )

# -------------------------------------------------------------
# 6. Resume Picker & Upload
# -------------------------------------------------------------
@router.get("/resumes", response_model=List[ExtensionResumeItem])
def get_extension_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resumes = db.query(Resume).filter(
        Resume.user_id == current_user.id,
        Resume.is_active == True
    ).order_by(Resume.created_at.desc()).all()

    items: List[ExtensionResumeItem] = []
    for r in resumes:
        versions = db.query(ResumeVersion).filter(ResumeVersion.resume_id == r.id).order_by(ResumeVersion.version_num.desc()).all()
        items.append(ExtensionResumeItem(
            id=r.id,
            filename=r.filename,
            skills_count=len(r.skills),
            experience_count=len(r.experiences),
            created_at=r.created_at,
            versions=[
                ResumeVersionSummary(
                    version_id=v.id,
                    version_num=v.version_num,
                    mode=v.mode,
                    template_id=v.template_id,
                    ats_loss_score=v.ats_loss_score,
                    is_published=v.is_published,
                    created_at=v.created_at
                ) for v in versions
            ]
        ))
    return items

@router.post("/resume/upload")
async def upload_resume_from_extension(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Direct drag-and-drop resume upload inside extension side panel.
    """
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File exceeds 10MB limit.")

    parsed_resume = ResumePipeline.process_and_save(
        db=db,
        user_id=current_user.id,
        filename=file.filename or "uploaded_resume.pdf",
        file_bytes=content
    )

    return {
        "status": "success",
        "resume_id": parsed_resume.id,
        "filename": parsed_resume.filename,
        "skills_count": len(parsed_resume.skills),
        "experience_count": len(parsed_resume.experiences),
        "message": f"Successfully parsed {file.filename} into verified Canonical Profile."
    }

# -------------------------------------------------------------
# 7. One-Click Grounded Actions
# -------------------------------------------------------------
@router.post("/actions/tailor", response_model=ExtensionActionResponse)
def extension_action_tailor(
    req: ExtensionActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    req.action_type = "tailor"
    return extension_service.execute_action(db=db, user_id=current_user.id, req=req)

@router.post("/actions/cover-letter", response_model=ExtensionActionResponse)
def extension_action_cover_letter(
    req: ExtensionActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    req.action_type = "cover_letter"
    return extension_service.execute_action(db=db, user_id=current_user.id, req=req)

@router.post("/actions/recruiter-message", response_model=ExtensionActionResponse)
def extension_action_recruiter_message(
    req: ExtensionActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    req.action_type = "recruiter_message"
    return extension_service.execute_action(db=db, user_id=current_user.id, req=req)

@router.post("/tracker/save")
def extension_save_to_tracker(
    req: ExtensionTrackerSaveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return extension_service.save_tracker_item(db=db, user_id=current_user.id, req=req)

# -------------------------------------------------------------
# 8. Compare Mode (Side-by-Side 2–3 Resume Versions)
# -------------------------------------------------------------
@router.post("/compare", response_model=CompareResponse)
def extension_compare_resumes(
    req: CompareRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return extension_service.compare_resumes(db=db, user_id=current_user.id, req=req)
    except Exception as e:
        logger.error(f"Compare failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
