from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.resumes import router as resumes_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.matching import router as matching_router
from app.api.v1.evidence import router as evidence_router
from app.api.v1.gaps import router as gaps_router
from app.api.v1.optimization import router as optimization_router
from app.api.v1.applications import router as applications_router
from app.api.v1.career import router as career_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.rag import router as rag_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.health import router as health_router
from app.api.v1.builder import router as builder_router

api_v1_router = APIRouter()

api_v1_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(resumes_router, prefix="/resumes", tags=["Resume Intelligence"])
api_v1_router.include_router(builder_router, prefix="/builder", tags=["Auto Resume Builder"])
api_v1_router.include_router(jobs_router, prefix="/jobs", tags=["Job Intelligence"])
api_v1_router.include_router(matching_router, prefix="/matching", tags=["Hybrid Matching"])
api_v1_router.include_router(evidence_router, prefix="/evidence", tags=["Evidence Graph"])
api_v1_router.include_router(gaps_router, prefix="/gaps", tags=["Skill Gap Engine"])
api_v1_router.include_router(optimization_router, prefix="/optimization", tags=["Resume Optimization"])
api_v1_router.include_router(applications_router, prefix="/applications", tags=["Application Generation"])
api_v1_router.include_router(career_router, prefix="/career", tags=["Career Roadmap & Recommendations"])
api_v1_router.include_router(analytics_router, prefix="/analytics", tags=["Market Analytics"])
api_v1_router.include_router(rag_router, prefix="/rag", tags=["RAG Knowledge Base"])
api_v1_router.include_router(tasks_router, prefix="/tasks", tags=["Background Tasks"])
api_v1_router.include_router(health_router, prefix="", tags=["Health & Observability"])
