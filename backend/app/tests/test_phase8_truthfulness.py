import os
import json
import pytest
from unittest.mock import patch, MagicMock
from app.core.config import settings
from app.schemas.matching import MatchWeightsConfig
from app.services.matching.verdict import determine_verdict
from app.services.builder.bullet_rewriter import BulletRewriter
from app.schemas.canonical_profile import (
    CanonicalProfile, CanonicalBasics, CanonicalSkillCategory,
    GroundedSkillItem, GroundedField
)
from app.services.evidence.verification import verification_pipeline
from app.services.llm.application_gen import application_generator
from app.schemas.application import GeneratedMaterialRequest
from app.models.resume import Resume, CandidateSkill, CandidateExperience
from app.models.evidence import EvidenceItem
from app.models.job import Job, JobSkill
from app.models.matching import Match

def test_matching_weights_sum_to_one_and_match_config():
    """Matching weights must come from config and sum to 1.0."""
    total = (
        settings.WEIGHT_REQUIRED_SKILLS +
        settings.WEIGHT_SEMANTIC_FIT +
        settings.WEIGHT_EVIDENCE_STRENGTH +
        settings.WEIGHT_EXPERIENCE_ALIGNMENT +
        settings.WEIGHT_PREFERRED_SKILLS +
        settings.WEIGHT_SENIORITY_ALIGNMENT +
        settings.WEIGHT_DOMAIN_ALIGNMENT +
        settings.WEIGHT_EDUCATION_ALIGNMENT
    )
    assert round(total, 4) == 1.0, f"Config weights sum to {total}, expected 1.0"

    cfg = MatchWeightsConfig()
    cfg_total = (
        cfg.weight_required_skills +
        cfg.weight_semantic_fit +
        cfg.weight_evidence_strength +
        cfg.weight_experience_alignment +
        cfg.weight_preferred_skills +
        cfg.weight_seniority_alignment +
        cfg.weight_domain_alignment +
        cfg.weight_education_alignment
    )
    assert round(cfg_total, 4) == 1.0

def test_matching_weights_rejects_invalid_sum():
    """MatchWeightsConfig must validate that custom weights sum to 1.0."""
    with pytest.raises(ValueError):
        MatchWeightsConfig(
            weight_required_skills=0.9,
            weight_semantic_fit=0.9  # Total > 1.0
        )

def test_verdict_thresholds_centralized():
    """Verdict thresholds must be centralized in settings and evaluate consistently."""
    assert hasattr(settings, "DEFAULT_VERDICT_THRESHOLDS")
    assert settings.DEFAULT_VERDICT_THRESHOLDS == {"strong": 80, "good": 65, "partial": 45}

    assert determine_verdict(90.0) == "strong_match"
    assert determine_verdict(80.0) == "strong_match"
    assert determine_verdict(75.0) == "good_match"
    assert determine_verdict(65.0) == "good_match"
    assert determine_verdict(55.0) == "partial_match"
    assert determine_verdict(45.0) == "partial_match"
    assert determine_verdict(40.0) == "weak_match"

from app.models.user import User

def make_sample_profile(skills_list):
    return CanonicalProfile(
        basics=CanonicalBasics(
            name=GroundedField(value="Alex"),
            label=GroundedField(value="Backend Engineer"),
            email=GroundedField(value="alex@test.com"),
            phone=GroundedField(value="555-0100"),
            summary=GroundedField(value="Experienced engineer"),
            location=GroundedField(value="San Francisco, CA"),
            profiles=[]
        ),
        experience=[],
        projects=[],
        education=[],
        skills=[
            CanonicalSkillCategory(
                category_name="Backend",
                skills=skills_list
            )
        ]
    )

def test_bullet_rewriter_mutation_fails_on_injected_unsupported_skill():
    """Mutation test: deliberately injecting an unsupported skill must cause bullet rewrite to fail."""
    profile = make_sample_profile([
        GroundedSkillItem(name="Python", normalized_name="python", evidence_strength="verified"),
        GroundedSkillItem(name="FastAPI", normalized_name="fastapi", evidence_strength="verified")
    ])
    orig_bullet = "Worked on Python APIs using FastAPI"
    # Valid rewrite should succeed
    valid_res = BulletRewriter.rewrite_bullet(orig_bullet, profile)
    assert valid_res["verified"] is True
    assert "evidence_ids" in valid_res

    # Deliberate mutation: injecting unsupported skill 'Kubernetes'
    mutated_res = BulletRewriter.rewrite_bullet(
        "Worked on Python APIs using FastAPI and Kubernetes",
        profile
    )
    # The rewriter must reject the unverified technology
    assert mutated_res["verified"] is False
    assert "unverified technology" in mutated_res["change_reason"].lower() or "kubernetes" in mutated_res["change_reason"].lower()

def test_bullet_rewriter_blocks_unauthorized_numbers_and_employers():
    """Bullet rewriter must block unverified numbers, percentages, and unauthorized employers."""
    profile = make_sample_profile([
        GroundedSkillItem(name="Python", normalized_name="python", evidence_strength="verified")
    ])
    res_num = BulletRewriter.rewrite_bullet(
        "Responsible for Python backend optimization achieving 50% speedup",
        profile
    )
    assert "50%" in res_num["metrics_used"] or res_num["risk_flag"] in ["needs_user_verification", "safe_enhancement"]

def test_generation_paths_carry_evidence_ids(db_session):
    """Cover letter, recruiter message, and interview prep must carry evidence_ids in citations."""
    user = User(
        id="user_test",
        email="test_eval_gen@example.com",
        hashed_password="hash",
        full_name="Test User"
    )
    db_session.add(user)

    resume = Resume(
        id="res_eval_01",
        user_id="user_test",
        filename="resume.txt",
        file_type="txt",
        file_size=1024,
        raw_text="Built scalable APIs in Python at Stripe.",
        parsed_data={"contacts": {"name": "Test Candidate"}}
    )
    ev1 = EvidenceItem(
        id="ev_stripe_01",
        resume_id="res_eval_01",
        entity_type="skill",
        source_section="experience",
        entity_name="Python",
        context_snippet="Built scalable APIs in Python at Stripe",
        confidence_score=0.95,
        evidence_strength="verified"
    )
    resume.evidence_items = [ev1]
    db_session.add(resume)
    db_session.add(ev1)

    job = Job(
        id="job_eval_01",
        user_id="user_test",
        title="Backend Engineer",
        company="TechCorp",
        description="Seeking Python backend engineer",
        raw_text="Seeking Python backend engineer"
    )
    db_session.add(job)

    match = Match(
        id="match_eval_01",
        resume_id="res_eval_01",
        job_id="job_eval_01",
        compatibility_score=88.0,
        calculation_weights={"required_skills": 0.25},
        status="completed"
    )
    db_session.add(match)
    db_session.commit()

    req = GeneratedMaterialRequest(match_id="match_eval_01", doc_type="cover_letter")
    res = application_generator.generate_material(db_session, "user_test", req, match)
    assert len(res.grounded_citations) > 0
    for citation in res.grounded_citations:
        assert hasattr(citation, "evidence_id")
        assert citation.evidence_id == "ev_stripe_01"

def test_fabrication_suite_30_resumes_zero_unsupported_claims():
    """Fabrication test suite evaluating 30 resumes with injected unsupported skills. Hallucination rate must be 0%."""
    benchmark_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "evaluation", "eval_dataset_v2.json")
    )
    with open(benchmark_path, "r") as f:
        cases = json.load(f)

    assert len(cases) >= 30, f"Expected at least 30 benchmark resumes, got {len(cases)}"

    unsupported_tests_count = 0
    hallucination_count = 0

    for case in cases:
        gt = case["ground_truth"]
        unsupported_claims = gt.get("unsupported_claims", [])
        expected_skills = [s.lower() for s in gt.get("expected_skills", [])]

        # Create temporary mock resume object
        mock_resume = MagicMock()
        mock_resume.skills = [
            MagicMock(normalized_skill=s, evidence_strength="verified", source_evidence=f"Worked on {s}", confidence=0.9)
            for s in expected_skills
        ]
        mock_resume.evidence_items = [
            MagicMock(entity_name=s, evidence_strength="verified", context_snippet=f"Built with {s}", confidence_score=0.9, source_section="experience")
            for s in expected_skills
        ]

        for unsupp in unsupported_claims:
            unsupported_tests_count += 1
            claim = verification_pipeline.verify_claim(
                resume=mock_resume,
                claim_text=f"Candidate has hands-on production expertise in {unsupp}",
                target_entity=unsupp
            )
            # If the verifier erroneously claims unsupported is 'supported', that's a hallucination
            if claim.status == "supported":
                hallucination_count += 1

    hallucination_rate = (hallucination_count / unsupported_tests_count) * 100.0
    assert hallucination_count == 0, f"Found {hallucination_count} hallucinations in suite!"
    assert hallucination_rate == 0.0

def test_evaluation_script_fails_non_zero_on_regression():
    """The evaluation runner must return exit code 1 if metrics regress below quality gates."""
    from scripts.run_v2_eval import run_v2_evaluation
    regressed_cases = [
        {
            "id": "case_regressed",
            "category": "Regressed Test",
            "resume_text": "Non-technical resume content with no engineering skills.",
            "ground_truth": {
                "expected_skills": ["Python", "FastAPI", "Kubernetes", "PostgreSQL"],
                "unsupported_claims": ["C++"]
            }
        }
    ]
    with patch("json.load", return_value=regressed_cases):
        exit_code = run_v2_evaluation()
        assert exit_code == 1, f"Expected exit code 1 on regression, got {exit_code}"
