from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.schemas.common import HealthCheckResponse
from app.core.config import settings

router = APIRouter()

@router.get("/health", response_model=HealthCheckResponse)
@router.get("/health/ready", response_model=HealthCheckResponse)
def health_check(db: Session = Depends(get_db)):
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    return HealthCheckResponse(
        status="healthy" if db_ok else "degraded",
        version="1.0.0",
        database_connected=db_ok,
        ai_engine_ready=True,
        redis_connected=bool(settings.REDIS_URL)
    )
