import pytest
from app.services.ontology.taxonomy import ontology
from app.services.ontology.skill_matcher import skill_matcher

def test_ontology_normalization():
    assert ontology.normalize("postgres") == "PostgreSQL"
    assert ontology.normalize("k8s") == "Kubernetes"
    assert ontology.normalize("py") == "Python"
    assert ontology.normalize("fastapi framework") == "FastAPI"

def test_skill_matcher_exact():
    res = skill_matcher.compare_skill("FastAPI", ["FastAPI", "Docker", "PostgreSQL"])
    assert res.match_type == "exact"
    assert res.match_score == 1.0

def test_skill_matcher_child_skill():
    # Job asks for Python, candidate has FastAPI (child of Python)
    res = skill_matcher.compare_skill("Python", ["FastAPI", "Docker"])
    assert res.match_type == "related"
    assert res.match_score >= 0.85

def test_skill_matcher_parent_skill():
    # Job asks for FastAPI, candidate has Python
    res = skill_matcher.compare_skill("FastAPI", ["Python"])
    assert res.match_type == "related"
    assert res.match_score >= 0.70

def test_skill_matcher_transferable():
    # Candidate has AWS, job asks for GCP
    res = skill_matcher.compare_skill("Google Cloud Platform", ["AWS", "Docker"])
    assert res.match_type == "transferable"
    assert res.match_score >= 0.80

def test_skill_matcher_missing():
    res = skill_matcher.compare_skill("Kubernetes", ["HTML/CSS", "JavaScript"])
    assert res.match_type == "missing"
    assert res.match_score == 0.0
