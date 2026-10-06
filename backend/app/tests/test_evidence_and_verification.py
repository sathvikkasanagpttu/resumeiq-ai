import pytest
from app.core.database import SessionLocal, Base, engine
from app.services.parser.resume_pipeline import ResumePipeline
from app.services.evidence.evidence_graph import EvidenceGraph
from app.services.evidence.verification import verification_pipeline
from app.models.user import User

@pytest.fixture
def test_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()

def test_evidence_graph_and_verification(test_db):
    user = test_db.query(User).filter(User.email == "test_ev@resumeiq.ai").first()
    if not user:
        user = User(email="test_ev@resumeiq.ai", hashed_password="pw", full_name="Test Ev", role="candidate")
        test_db.add(user)
        test_db.commit()

    sample_resume = """
Jane Doe
jane@example.com

EXPERIENCE
Lead Developer - CloudSys (2020 - Present)
• Built a FastAPI microservices backend with PostgreSQL handling 50k rpm, decreasing latency by 35%.
• Deployed Docker containers to AWS ECS.

SKILLS
Python, FastAPI, PostgreSQL, Docker, AWS
"""
    resume = ResumePipeline.process_and_save(
        db=test_db,
        user_id=user.id,
        filename="jane_resume.txt",
        file_bytes=sample_resume.encode("utf-8")
    )

    # 1. Evidence Graph Query
    graph = EvidenceGraph(resume)
    python_exp = graph.explain_skill_evidence("Python")
    assert python_exp["status"] in ["supported", "partially_supported"]
    assert len(python_exp["citations"]) > 0

    # Query for nonexistent skill
    k8s_exp = graph.explain_skill_evidence("Kubernetes")
    assert k8s_exp["status"] == "unsupported"
    assert k8s_exp["evidence_strength"] == "missing"

    # Cytoscape elements
    elements = graph.to_cytoscape_elements()
    assert len(elements) > 0
    assert any(el["data"]["id"] == "candidate_root" for el in elements)

    # 2. Verification Pipeline
    # Supported claim (FastAPI is in experience bullet with action verb and metric)
    claim_fastapi = verification_pipeline.verify_claim(resume, "Candidate has FastAPI experience", "FastAPI")
    assert claim_fastapi.status == "supported"
    assert claim_fastapi.evidence_strength == "verified"

    # Partially supported claim (Python listed in skills section without action bullet)
    claim_python = verification_pipeline.verify_claim(resume, "Candidate has Python experience", "Python")
    assert claim_python.status in ["supported", "partially_supported"]


    # Unsupported claim (Hallucination test)
    claim2 = verification_pipeline.verify_claim(resume, "Candidate has Kubernetes experience", "Kubernetes")
    assert claim2.status == "unsupported"
    assert claim2.confidence == 0.0

    # Validate generated text with unsupported claims
    is_valid, claims, flagged = verification_pipeline.validate_generated_text(
        resume=resume,
        generated_text="I have 5 years experience with Kubernetes and PyTorch."
    )
    assert not is_valid
    assert "Kubernetes" in flagged or "PyTorch" in flagged
