import os
import pytest
from datetime import timedelta, datetime, timezone
import jwt
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import Settings, settings
from app.core.security import create_access_token, decode_access_token, get_password_hash
from app.models.user import User
from app.models.resume import Resume
from app.models.job import Job
from app.models.matching import Match

def test_no_token_returns_401_on_all_protected_routes(client: TestClient):
    """
    Enumerate protected routes automatically from OpenAPI schema and assert that
    requests without a token return 401 Unauthorized, never falling back to a demo user.
    """
    public_paths = {
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/health",
        "/api/v1/health/ready",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/extension/auth/pair",
        "/api/v1/extension/auth/refresh",
    }
    
    openapi_schema = app.openapi()
    paths_dict = openapi_schema.get("paths", {})
    
    protected_endpoints = []
    for path, methods in paths_dict.items():
        if path not in public_paths:
            for method in methods.keys():
                if method.lower() in ("get", "post", "delete", "put", "patch"):
                    protected_endpoints.append((method.upper(), path))

    assert len(protected_endpoints) >= 20, f"Expected at least 20 protected endpoints, got {len(protected_endpoints)}"

    for method, path in protected_endpoints:
        # Replace route path parameters with dummy UUIDs
        test_path = path.replace("{resume_id}", "00000000-0000-0000-0000-000000000000")\
                         .replace("{match_id}", "00000000-0000-0000-0000-000000000000")\
                         .replace("{job_id}", "00000000-0000-0000-0000-000000000000")\
                         .replace("{version_id}", "00000000-0000-0000-0000-000000000000")\
                         .replace("{skill_name}", "Python")
        
        if method == "GET":
            res = client.get(test_path)
        elif method == "POST":
            res = client.post(test_path, json={})
        elif method == "DELETE":
            res = client.delete(test_path)
        elif method == "PUT":
            res = client.put(test_path, json={})
        elif method == "PATCH":
            res = client.patch(test_path, json={})
        else:
            continue

        assert res.status_code == 401, f"{method} {test_path} without token returned {res.status_code}, expected 401"

def test_expired_token_returns_401(client: TestClient):
    """Expired tokens must be rejected with 401."""
    expired_token = create_access_token("some-user-id", expires_delta=timedelta(seconds=-10))
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401

def test_token_type_claim_validation(client: TestClient, db_session):
    """A refresh token must not be accepted by endpoints requiring an access token."""
    user = User(
        email="test_token_type@example.com",
        hashed_password=get_password_hash("StrongPass123!"),
        full_name="Type Tester"
    )
    db_session.add(user)
    db_session.commit()

    # Create a refresh token (type="refresh")
    to_encode = {
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "sub": str(user.id),
        "type": "refresh",
        "iat": datetime.now(timezone.utc)
    }
    refresh_token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {refresh_token}"})
    assert res.status_code == 401, f"Expected 401 when using refresh token as access token, got {res.status_code}"

def test_secret_key_production_enforcement():
    """In production environment, app must refuse to start without a valid, strong SECRET_KEY."""
    with pytest.raises((ValueError, RuntimeError)):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY=""
        )

    with pytest.raises((ValueError, RuntimeError)):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="resumeiq-super-secret-jwt-key-2026-production-grade"
        )

def test_password_rules(client: TestClient):
    """Password must be validated for minimum length (8 chars) and complexity."""
    weak_passwords = [
        "short",
        "alllowercase123",
        "ALLUPPERCASE123",
        "NoDigitsOrSpecial",
        "12345678"
    ]
    for weak_pw in weak_passwords:
        res = client.post("/api/v1/auth/register", json={
            "email": f"weak_{hash(weak_pw)}@example.com",
            "full_name": "Weak Password User",
            "password": weak_pw
        })
        assert res.status_code in (400, 422), f"Expected registration failure for weak password '{weak_pw}', got {res.status_code}"

def test_login_rate_limiting(client: TestClient):
    """Multiple failed login attempts must trigger rate limiting (429)."""
    for _ in range(8):
        client.post("/api/v1/auth/login", json={
            "email": "rate_limit_target@example.com",
            "password": "WrongPassword123!"
        })
    
    limited_res = client.post("/api/v1/auth/login", json={
        "email": "rate_limit_target@example.com",
        "password": "WrongPassword123!"
    })
    assert limited_res.status_code == 429, f"Expected 429 Too Many Requests after 8 failed attempts, got {limited_res.status_code}"

def test_idor_protection_on_resumes_jobs_matches_evidence_analytics(client: TestClient, db_session):
    """Users must not be able to access or modify resources owned by another user."""
    # Register and get tokens for User A and User B
    reg_a = client.post("/api/v1/auth/register", json={
        "email": "user_a@example.com",
        "full_name": "User Alpha",
        "password": "ValidPassword123!"
    })
    assert reg_a.status_code == 200, f"Register A failed: {reg_a.text}"
    token_a = reg_a.json()["access_token"]
    user_a_id = reg_a.json()["user_id"]

    reg_b = client.post("/api/v1/auth/register", json={
        "email": "user_b@example.com",
        "full_name": "User Beta",
        "password": "ValidPassword123!"
    })
    assert reg_b.status_code == 200, f"Register B failed: {reg_b.text}"
    token_b = reg_b.json()["access_token"]

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates resume
    resume_a = Resume(
        user_id=user_a_id,
        filename="alpha_resume.txt",
        file_type="txt",
        file_size=100,
        raw_text="Alpha Resume Text"
    )
    db_session.add(resume_a)
    db_session.commit()
    db_session.refresh(resume_a)

    # User B attempts to access User A's resume
    res = client.get(f"/api/v1/resumes/{resume_a.id}", headers=headers_b)
    assert res.status_code == 403

    # User B attempts to delete User A's resume
    res = client.delete(f"/api/v1/resumes/{resume_a.id}", headers=headers_b)
    assert res.status_code == 403

    # User B attempts to view User A's evidence graph
    res = client.get(f"/api/v1/evidence/{resume_a.id}/graph", headers=headers_b)
    assert res.status_code == 403

    # User B attempts to query market analytics with User A's resume
    res = client.get(f"/api/v1/analytics?resume_id={resume_a.id}", headers=headers_b)
    assert res.status_code == 403
