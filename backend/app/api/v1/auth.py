from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.core.rate_limit import rate_limiter
from app.models.user import User, CandidateProfile
from app.schemas.user import UserCreate, UserLogin, Token, UserResponse
from app.api.deps import get_current_user

router = APIRouter()

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

@router.post("/register", response_model=Token)
def register(user_in: UserCreate, request: Request, db: Session = Depends(get_db)):
    ip = get_client_ip(request)
    # Rate limit registrations per IP: max 10 per hour
    rate_limiter.check_or_raise(f"register:{ip}", max_requests=10, window_seconds=3600, action_name="registration")

    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email is already registered")

    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role or "candidate"
    )
    db.add(user)
    db.flush()

    profile = CandidateProfile(
        user_id=user.id,
        headline="Software Professional",
        summary="",
        total_experience_years=0.0,
        seniority_level="mid"
    )
    db.add(profile)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, token_type="access")
    return Token(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role
    )

@router.post("/login", response_model=Token)
def login(login_in: UserLogin, request: Request, db: Session = Depends(get_db)):
    ip = get_client_ip(request)
    fail_key = f"{ip}:{login_in.email.strip().lower()}"

    # Check if locked out due to previous failed attempts (max 5 per 5 minutes)
    is_locked, retry_after = rate_limiter.is_failed_locked(fail_key, max_failures=5, window_seconds=300)
    if is_locked:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed login attempts. Account temporarily locked for {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )

    user = db.query(User).filter(User.email == login_in.email.strip()).first()
    if not user or not verify_password(login_in.password, user.hashed_password):
        # Record failed login attempt
        now_locked = rate_limiter.record_failure(fail_key, max_failures=5, window_seconds=300)
        if now_locked:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Try again in 300 seconds.",
                headers={"Retry-After": "300"}
            )
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    # Successful login: clear failures
    rate_limiter.clear_failures(fail_key)

    token = create_access_token(user.id, token_type="access")
    return Token(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
