import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check_endpoint():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["database_connected"] is True
    assert data["ai_engine_ready"] is True

def test_full_api_workflow():
    # 1. Register User
    reg_res = client.post("/api/v1/auth/register", json={
        "email": "integration_tester@resumeiq.ai",
        "full_name": "Integration Tester",
        "password": "Password123!",
        "role": "candidate"
    })
    if reg_res.status_code == 400:
        # Already registered, log in
        login_res = client.post("/api/v1/auth/login", json={
            "email": "integration_tester@resumeiq.ai",
            "password": "Password123!"
        })
        token = login_res.json()["access_token"]
    else:
        assert reg_res.status_code == 200
        token = reg_res.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Upload Resume
    resume_content = """
Liam Vance
liam.vance@example.com

SUMMARY
Backend Engineer with 4 years experience in Python and PostgreSQL.

EXPERIENCE
Software Engineer - DataStack (2021 - Present)
• Built high-performance REST APIs with FastAPI and PostgreSQL, reducing latency by 40%.
• Deployed microservices with Docker on AWS EC2.

SKILLS
Python, FastAPI, PostgreSQL, Docker, AWS, Redis
""".encode("utf-8")
    files = {"file": ("liam_resume.txt", resume_content, "text/plain")}
    upload_res = client.post("/api/v1/resumes/upload", files=files, headers=headers)
    assert upload_res.status_code == 200
    resume_id = upload_res.json()["id"]

    # 3. Create Job
    job_payload = {
        "title": "Backend Python Developer",
        "company": "NextGen Cloud",
        "description": """
Requirements:
• 3+ years experience with Python and FastAPI.
• Required: PostgreSQL database architecture.
• Required: Containerization with Docker.
• Preferred: Redis caching.
• Preferred: AWS cloud services.
"""
    }
    job_res = client.post("/api/v1/jobs", json=job_payload, headers=headers)
    assert job_res.status_code == 200
    job_id = job_res.json()["id"]

    # 4. Compute Match
    match_res = client.post("/api/v1/matching", json={
        "resume_id": resume_id,
        "job_id": job_id
    }, headers=headers)
    assert match_res.status_code == 200
    match_data = match_res.json()
    match_id = match_data["id"]
    assert match_data["compatibility_score"] >= 70.0
    assert len(match_data["components"]) == 8

    # 5. Query Evidence Graph
    ev_res = client.get(f"/api/v1/evidence/{resume_id}/skill/FastAPI", headers=headers)
    assert ev_res.status_code == 200
    ev_data = ev_res.json()
    assert ev_data["status"] == "supported"
    assert len(ev_data["citations"]) > 0

    # 6. Get Skill Gaps
    gap_res = client.get(f"/api/v1/gaps/match/{match_id}", headers=headers)
    assert gap_res.status_code == 200
    gap_data = gap_res.json()
    assert "gaps" in gap_data

    # 7. Get Resume Optimization
    opt_res = client.get(f"/api/v1/optimization/match/{match_id}", headers=headers)
    assert opt_res.status_code == 200
    opt_data = opt_res.json()
    assert len(opt_data["modifications"]) > 0
    assert "truthfulness_guarantee" in opt_data

    # 8. Generate Application Materials (Cover Letter)
    app_res = client.post("/api/v1/applications/generate", json={
        "match_id": match_id,
        "doc_type": "cover_letter"
    }, headers=headers)
    assert app_res.status_code == 200
    app_data = app_res.json()
    assert app_data["verification_status"] == "verified_grounded"
    assert len(app_data["grounded_citations"]) > 0

    # 9. Get Career Roadmap
    road_res = client.get(f"/api/v1/career/roadmap/match/{match_id}", headers=headers)
    assert road_res.status_code == 200
    road_data = road_res.json()
    assert "learning_paths" in road_data

    # 10. Get Market Analytics
    analytics_res = client.get(f"/api/v1/analytics?resume_id={resume_id}", headers=headers)
    assert analytics_res.status_code == 200
    analytics_data = analytics_res.json()
    assert len(analytics_data["top_skills"]) > 0
    assert analytics_data["candidate_benchmark"] is not None
