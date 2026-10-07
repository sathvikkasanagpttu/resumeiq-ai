from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.schemas.common import HealthCheckResponse
from app.core.config import settings
from app.core.logging import logger

router = APIRouter()

def check_redis_connection() -> bool:
    """Genuinely ping Redis instance if REDIS_URL is configured."""
    if not settings.REDIS_URL:
        return False
    try:
        import redis
        client = redis.Redis.from_url(settings.REDIS_URL, socket_timeout=0.8)
        client.ping()
        return True
    except Exception as e:
        logger.warning(f"Redis healthcheck ping failed: {e}")
        return False

@router.get("/health", response_model=HealthCheckResponse)
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint: really pings database and Redis."""
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.error(f"Database healthcheck ping failed: {e}")
        db_ok = False

    redis_ok = check_redis_connection()

    if not db_ok:
        current_status = "unhealthy"
    elif settings.REDIS_URL and not redis_ok:
        current_status = "degraded"
    else:
        current_status = "healthy"

    return HealthCheckResponse(
        status=current_status,
        version="1.0.0",
        database_connected=db_ok,
        ai_engine_ready=True,
        redis_connected=redis_ok
    )

@router.get("/health/ready", response_model=HealthCheckResponse)
def readiness_check(db: Session = Depends(get_db)):
    """Readiness probe: returns 200 if dependencies ready, 503 if database down."""
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.error(f"Readiness probe failed on database check: {e}")
        db_ok = False

    redis_ok = check_redis_connection()

    if not db_ok:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "version": "1.0.0",
                "database_connected": False,
                "ai_engine_ready": True,
                "redis_connected": redis_ok
            }
        )

    return HealthCheckResponse(
        status="ready",
        version="1.0.0",
        database_connected=True,
        ai_engine_ready=True,
        redis_connected=redis_ok
    )

