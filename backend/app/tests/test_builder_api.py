import pytest
import io
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

RESUME_TEXT = """
EMILY WATSON
emily.watson@example.com | (555) 987-6543 | New York, NY
https://github.com/emilywatson | https://linkedin.com/in/emilywatson

SUMMARY
Senior Backend Architect designing enterprise distributed microservices using Python, FastAPI, and Docker.

SKILLS
Python, FastAPI, Docker, PostgreSQL, Redis, Kubernetes

EXPERIENCE
Senior Backend Engineer at CloudScale Inc (2021 - Present)
- Architected RESTful microservices processing 15M daily requests using FastAPI.
- Optimized PostgreSQL queries reducing latency by 40%.
- Spearheaded Kubernetes cluster deployment.

EDUCATION
B.S. in Software Engineering, Columbia University (2017 - 2021)
"""

@pytest.fixture(scope="module")
def auth_headers():
    reg_res = client.post("/api/v1/auth/register", json={
        "email": "builder_tester@resumeiq.ai",
        "full_name": "Emily Watson",
        "password": "Password123!",
        "role": "candidate"
    })
    if reg_res.status_code == 200:
        token = reg_res.json()["access_token"]
    else:
        login_res = client.post("/api/v1/auth/login", json={
            "email": "builder_tester@resumeiq.ai",
            "password": "Password123!"
        })
        token = login_res.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="module")
def uploaded_resume_id(auth_headers):
    file_bytes = io.BytesIO(RESUME_TEXT.encode("utf-8"))
    upload_res = client.post(
        "/api/v1/resumes/upload",
        headers=auth_headers,
        files={"file": ("resume.txt", file_bytes, "text/plain")}
    )
    assert upload_res.status_code == 200
    return upload_res.json()["id"]

def test_builder_wizard_endpoints(auth_headers, uploaded_resume_id):
    # 1. Get Wizard questions
    q_res = client.get(
        f"/api/v1/builder/wizard/questions/{uploaded_resume_id}",
        headers=auth_headers
    )
    assert q_res.status_code == 200
    q_data = q_res.json()
    assert "questions" in q_data

    # 2. Submit Wizard answers
    if q_data["questions"]:
        first_q = q_data["questions"][0]
        ans_res = client.post(
            "/api/v1/builder/wizard/answers",
            headers=auth_headers,
            json={
                "resume_id": uploaded_resume_id,
                "answers": [
                    {
                        "question_id": first_q["id"],
                        "answer_text": "Enhanced system resilience with 99.99% uptime.",
                        "confirmed_metric": "99.99%",
                        "confirmed_technologies": ["Docker"]
                    }
                ]
            }
        )
        assert ans_res.status_code == 200
        assert ans_res.json()["facts_added_count"] >= 1

def test_builder_quality_report_endpoint(auth_headers, uploaded_resume_id):
    res = client.get(
        f"/api/v1/builder/quality/{uploaded_resume_id}",
        headers=auth_headers
    )
    assert res.status_code == 200
    data = res.json()
    assert "overall_quality_score" in data
    assert "components" in data

def test_builder_generate_and_versioning_endpoints(auth_headers, uploaded_resume_id):
    # 1. Generate version
    gen_res = client.post(
        "/api/v1/builder/generate",
        headers=auth_headers,
        json={
            "resume_id": uploaded_resume_id,
            "mode": "role_targeted",
            "target_role": "Lead Backend Engineer",
            "template_id": "modern_minimal",
            "page_target": 1
        }
    )
    assert gen_res.status_code == 200
    v_data = gen_res.json()
    version_id = v_data["id"]
    assert v_data["mode"] == "role_targeted"
    assert v_data["template_id"] == "modern_minimal"

    # 2. Get list of versions
    v_list_res = client.get(
        f"/api/v1/builder/versions/{uploaded_resume_id}",
        headers=auth_headers
    )
    assert v_list_res.status_code == 200
    assert len(v_list_res.json()) >= 1

    # 3. Get single version detail
    v_detail_res = client.get(
        f"/api/v1/builder/version/{version_id}",
        headers=auth_headers
    )
    assert v_detail_res.status_code == 200

    # 4. Review diff if any diffs exist
    if v_data["diffs"]:
        first_diff = v_data["diffs"][0]
        review_res = client.post(
            "/api/v1/builder/diff/review",
            headers=auth_headers,
            json={
                "diff_id": first_diff["id"],
                "action": "accept"
            }
        )
        assert review_res.status_code == 200
        assert review_res.json()["status"] == "accepted"

    # 5. Test Exports: PDF, DOCX, TXT, JSON, HTML
    for fmt in ["pdf", "docx", "txt", "json", "html"]:
        exp_res = client.get(
            f"/api/v1/builder/export/{version_id}?format={fmt}",
            headers=auth_headers
        )
        assert exp_res.status_code == 200
        assert len(exp_res.content) > 100

def test_tracker_and_interview_prep_endpoints(auth_headers, uploaded_resume_id):
    # 1. Create tracker item
    tr_res = client.post(
        "/api/v1/builder/tracker",
        headers=auth_headers,
        json={
            "job_title": "Lead Backend Architect",
            "company_name": "Datadog",
            "stage": "applied",
            "notes": "Referred by senior director."
        }
    )
    assert tr_res.status_code == 200
    item_id = tr_res.json()["id"]

    # 2. Get tracker items
    list_res = client.get("/api/v1/builder/tracker", headers=auth_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 3. Update tracker item
    patch_res = client.patch(
        f"/api/v1/builder/tracker/{item_id}",
        headers=auth_headers,
        json={"stage": "interviewing", "notes": "Passed screen, technical interview scheduled."}
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["stage"] == "interviewing"

    # 4. Interview prep generation
    prep_res = client.post(
        "/api/v1/builder/interview-prep",
        headers=auth_headers,
        json={
            "resume_id": uploaded_resume_id,
            "target_role": "Lead Backend Architect"
        }
    )
    assert prep_res.status_code == 200
    prep_data = prep_res.json()
    assert prep_data["total_questions"] >= 1
    assert "star_skeleton" in prep_data["questions"][0]

    # 5. Delete tracker item
    del_res = client.delete(f"/api/v1/builder/tracker/{item_id}", headers=auth_headers)
    assert del_res.status_code == 200
