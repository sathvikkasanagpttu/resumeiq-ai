import pytest
from app.core.database import SessionLocal, Base, engine
from app.services.parser.resume_pipeline import ResumePipeline
from app.services.job.job_pipeline import JobPipeline
from app.services.matching.hybrid_matcher import HybridMatcher
from app.schemas.job import JobCreate
from app.schemas.matching import MatchWeightsConfig
from app.models.user import User

@pytest.fixture
def test_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()

def test_hybrid_matching(test_db):
    user = test_db.query(User).filter(User.email == "test_match@resumeiq.ai").first()
    if not user:
        user = User(email="test_match@resumeiq.ai", hashed_password="pw", full_name="Match Tester", role="candidate")
        test_db.add(user)
        test_db.commit()

    resume_text = """
Elena Rostova
elena@example.com

EXPERIENCE
Senior Python Engineer - DataCloud (2019 - Present)
• Built a scalable FastAPI service with PostgreSQL and Docker handling 10k rps.
• Deployed microservices to AWS EC2 and S3.

SKILLS
Python, FastAPI, PostgreSQL, Docker, AWS, Redis
"""
    resume = ResumePipeline.process_and_save(
        db=test_db,
        user_id=user.id,
        filename="elena.txt",
        file_bytes=resume_text.encode("utf-8")
    )

    job_create = JobCreate(
        title="Senior Python Backend Developer",
        company="FinServe",
        description="""
Requirements:
• 4+ years software engineering experience.
• Required: Python, FastAPI, PostgreSQL.
• Required: Docker containerization.
• Preferred: Redis caching.
• Preferred: AWS cloud services.
"""
    )
    job = JobPipeline.parse_and_save(db=test_db, user_id=user.id, job_in=job_create)

    # Run match with default weights
    match = HybridMatcher.compute_match(db=test_db, resume=resume, job=job)
    assert match.compatibility_score >= 70.0
    assert match.semantic_score > 0.0
    assert match.lexical_score > 0.0
    assert match.required_skill_coverage >= 80.0
    assert len(match.components) == 8
    assert "headline" in match.explanation_summary

    # Run match with custom weights
    custom_w = MatchWeightsConfig(
        weight_required_skills=0.50,
        weight_semantic_fit=0.10,
        weight_evidence_strength=0.10,
        weight_experience_alignment=0.10,
        weight_preferred_skills=0.05,
        weight_seniority_alignment=0.05,
        weight_domain_alignment=0.05,
        weight_education_alignment=0.05
    )
    custom_match = HybridMatcher.compute_match(db=test_db, resume=resume, job=job, custom_weights=custom_w)
    assert custom_match.calculation_weights["required_skills"] == 0.50
