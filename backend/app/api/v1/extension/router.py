import asyncio
import hashlib
import io
import secrets
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
from app.models.extension import ExtensionDevice, ExtensionPairingCode
from app.schemas.extension import (
    ExtensionPairRequest, ExtensionPairResponse, TokenRefreshRequest,
    PairingCodeResponse, ExtensionDeviceResponse,
    JDCaptureRequest, JDCaptureResponse,
    QuickMatchRequest, QuickMatchResultResponse,
    ExtensionResumeItem, ResumeVersionSummary,
    ExtensionActionRequest, ExtensionActionResponse,
    ExtensionTrackerSaveRequest, CompareRequest, CompareResponse
)
from app.services.extension.extension_service import extension_service
from app.services.parser.resume_pipeline import ResumePipeline
def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

router = APIRouter()

# -------------------------------------------------------------
# 1. Pairing & Authentication
# -------------------------------------------------------------
@router.post("/auth/pairing-code", response_model=PairingCodeResponse)
def generate_pairing_code(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a secure random single-use 6-digit pairing code with a 5-minute expiry.
    """
    raw_code = f"{secrets.randbelow(900000) + 100000}"
    code_hash = hashlib.sha256(raw_code.encode("utf-8")).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    pairing_rec = ExtensionPairingCode(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        code_hash=code_hash,
        is_used=False,
        expires_at=expires_at,
        created_at=datetime.now(timezone.utc)
    )
    db.add(pairing_rec)
    db.commit()

    return PairingCodeResponse(
        pairing_code=raw_code,
        expires_at=expires_at,
        expires_in_seconds=300
    )

@router.post("/auth/pair", response_model=ExtensionPairResponse)
def pair_extension_device(
    req: ExtensionPairRequest,
    db: Session = Depends(get_db)
):
    """
    Pair an extension device using either email/password or a single-use pairing code.
    Rejects missing or invalid credentials with 401. No fallback to first active user.
    """
    user = None
    now = datetime.now(timezone.utc)

    if req.email and req.password:
        candidate = db.query(User).filter(User.email == req.email.strip()).first()
        if candidate and verify_password(req.password, candidate.hashed_password):
            user = candidate
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password."
            )
    elif req.pairing_code:
        code_str = req.pairing_code.strip()
        code_hash = hashlib.sha256(code_str.encode("utf-8")).hexdigest()
        rec = db.query(ExtensionPairingCode).filter(ExtensionPairingCode.code_hash == code_hash).first()
        if not rec:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid pairing code."
            )
        if rec.is_used:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Pairing code has already been used."
            )
        if ensure_utc(rec.expires_at) < now:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Pairing code has expired."
            )
        
        # Mark code as used
        rec.is_used = True
        rec.used_at = now
        user = db.query(User).filter(User.id == rec.user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive or not found."
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid email/password or single-use pairing code is required."
        )

    device_id = req.device_id or str(uuid.uuid4())
    raw_refresh_token = secrets.token_urlsafe(32)
    hashed_refresh = hashlib.sha256(raw_refresh_token.encode("utf-8")).hexdigest()

    # Upsert ExtensionDevice record
    device = db.query(ExtensionDevice).filter(
        ExtensionDevice.device_id == device_id,
        ExtensionDevice.user_id == user.id
    ).first()

    if not device:
        device = ExtensionDevice(
            id=str(uuid.uuid4()),
            device_id=device_id,
            user_id=user.id,
            device_name=req.device_name or "Chrome Extension",
            hashed_refresh_token=hashed_refresh,
            created_at=now,
            last_used_at=now,
            revoked_at=None
        )
        db.add(device)
    else:
        device.hashed_refresh_token = hashed_refresh
        device.device_name = req.device_name or device.device_name
        device.last_used_at = now
        device.revoked_at = None

    db.commit()

    # Create scoped, short-lived (30-min) extension access token
    access_token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=30),
        scope="extension",
        token_type="access"
    )

    return ExtensionPairResponse(
        extension_token=access_token,
        refresh_token=raw_refresh_token,
        token_type="Bearer",
        expires_in_seconds=1800,
        user_id=user.id,
        user_email=user.email,
        user_name=user.full_name,
        device_id=device_id,
        paired_at=now.isoformat(),
        user={"id": user.id, "email": user.email, "name": user.full_name}
    )

@router.post("/auth/refresh", response_model=ExtensionPairResponse)
def refresh_extension_token(
    req: TokenRefreshRequest,
    db: Session = Depends(get_db)
):
    """
    Validate refresh token against database and rotate it.
    Reuse of an old token immediately revokes the device.
    """
    device = db.query(ExtensionDevice).filter(ExtensionDevice.device_id == req.device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Device not found.")

    if device.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device has been revoked.")

    incoming_hash = hashlib.sha256(req.refresh_token.encode("utf-8")).hexdigest()
    if incoming_hash != device.hashed_refresh_token:
        # Token reuse detected: revoke device immediately in DB
        device.revoked_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid refresh token. Token reuse detected; device has been revoked."
        )

    now = datetime.now(timezone.utc)
    user = device.user
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is inactive or not found.")

    # Rotate refresh token
    new_raw_refresh = secrets.token_urlsafe(32)
    device.hashed_refresh_token = hashlib.sha256(new_raw_refresh.encode("utf-8")).hexdigest()
    device.last_used_at = now
    db.commit()

    new_access_token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=30),
        scope="extension",
        token_type="access"
    )

    return ExtensionPairResponse(
        extension_token=new_access_token,
        refresh_token=new_raw_refresh,
        token_type="Bearer",
        expires_in_seconds=1800,
        user_id=user.id,
        user_email=user.email,
        user_name=user.full_name,
        device_id=device.device_id,
        paired_at=now.isoformat(),
        user={"id": user.id, "email": user.email, "name": user.full_name}
    )

@router.get("/devices", response_model=List[ExtensionDeviceResponse])
def list_extension_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List paired extension devices for the current logged-in user."""
    devices = db.query(ExtensionDevice).filter(
        ExtensionDevice.user_id == current_user.id
    ).order_by(ExtensionDevice.last_used_at.desc()).all()
    
    return [
        ExtensionDeviceResponse(
            id=d.id,
            device_id=d.device_id,
            device_name=d.device_name,
            created_at=d.created_at,
            last_used_at=d.last_used_at,
            revoked_at=d.revoked_at,
            is_revoked=d.is_revoked
        ) for d in devices
    ]

@router.post("/devices/{device_id}/revoke")
def revoke_extension_device(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Revoke a paired extension device in DB."""
    device = db.query(ExtensionDevice).filter(
        ExtensionDevice.device_id == device_id,
        ExtensionDevice.user_id == current_user.id
    ).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found.")

    device.revoked_at = datetime.now(timezone.utc)
    db.commit()
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
    if match.resume.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied.")

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
