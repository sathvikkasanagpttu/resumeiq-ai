import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger, setup_logger
from app.core.database import SessionLocal, engine, Base
from app.core.exceptions import ResumeIQException
from app.api.v1 import api_v1_router
from app.services.rag.retriever import rag_retriever
from app.models.user import User, CandidateProfile
from app.core.security import get_password_hash

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up ResumeIQ application.")
    yield
    logger.info("Shutting down ResumeIQ application.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Evidence-First AI Resume & Job Matching Engine",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tracing & Latency Middleware
@app.middleware("http")
async def add_process_time_and_logging(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = round((time.time() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-MS"] = str(process_time)
    
    logger.info(
        f"{request.method} {request.url.path} completed with {response.status_code} in {process_time}ms",
        extra={"request_id": request_id, "latency_ms": process_time}
    )
    return response

# Custom Exception Handler
@app.exception_handler(ResumeIQException)
async def resumeiq_exception_handler(request: Request, exc: ResumeIQException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "detail": exc.detail,
            "extra": exc.extra,
            "request_id": getattr(request.state, "request_id", None)
        }
    )

# Include Routers
app.include_router(api_v1_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "app": "ResumeIQ",
        "tagline": "Evidence-First AI Resume & Job Matching Engine",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "api_v1": settings.API_V1_STR
    }
