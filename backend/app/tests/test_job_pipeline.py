import pytest
from app.services.job.job_pipeline import JobPipeline
from app.schemas.job import JobCreate

def test_job_pipeline_classification():
    job_text = """
Senior Python Engineer
FinCorp | Remote

Responsibilities:
• Architect scalable microservices in a fast-paced environment.

Required Qualifications:
• 4+ years of software development experience with Python.
• Must have strong SQL and PostgreSQL knowledge.

Preferred Qualifications:
• Experience with Docker and AWS is a plus.
• Familiarity with Redis.
"""
    reqs = JobPipeline._extract_requirements(job_text)
    categories = [r["category"] for r in reqs]
    assert "REQUIRED" in categories
    assert "PREFERRED" in categories
    assert "RESPONSIBILITY" in categories

    # Check importance weights
    for r in reqs:
        if r["category"] == "REQUIRED":
            assert r["weight"] >= 0.9
        elif r["category"] == "PREFERRED":
            assert r["weight"] <= 0.7

def test_job_skills_extraction():
    job_text = "Looking for a developer with FastAPI, PostgreSQL, and Docker experience."
    reqs = [{"text": job_text, "category": "REQUIRED", "weight": 1.0, "entities": ["FastAPI", "PostgreSQL", "Docker"]}]
    skills = JobPipeline._extract_skills(job_text, reqs)
    skill_names = [s["normalized"] for s in skills]
    assert "FastAPI" in skill_names
    assert "PostgreSQL" in skill_names
    assert "Docker" in skill_names
