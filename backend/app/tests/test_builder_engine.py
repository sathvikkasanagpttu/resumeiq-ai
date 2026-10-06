import pytest
from app.core.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.resume import Resume, ResumeVersion, ResumeDiffItem
from app.services.parser.resume_pipeline import ResumePipeline
from app.services.builder.bullet_rewriter import BulletRewriter
from app.services.builder.template_engine import TemplateEngine
from app.services.builder.exporters import ResumeExporter
from app.services.builder.roundtrip_validator import RoundTripValidator
from app.services.builder.generation_engine import ResumeGenerator
from app.schemas.builder import GenerateResumeRequest

SAMPLE_RESUME_TEXT = """
JOHN DOE
Software Engineer | john.doe@example.com | (555) 123-4567 | San Francisco, CA
https://github.com/johndoe | https://linkedin.com/in/johndoe

PROFESSIONAL SUMMARY
Experienced backend engineer building cloud applications with Python and FastAPI.

SKILLS
Python, FastAPI, PostgreSQL, Docker, Redis

WORK EXPERIENCE
Senior Software Engineer at Horizon Tech (Jan 2021 - Present)
- Worked on payment API backend with FastAPI and PostgreSQL.
- Handled database performance optimization reducing query time by 35%.
- Assisted with Kubernetes deployments.

EDUCATION
B.S. in Computer Science, University of California, Berkeley (2016 - 2020)
"""

def test_bullet_rewriter_strict_no_hallucination():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "test_builder@example.com").first()
        if not user:
            user = User(email="test_builder@example.com", hashed_password="hashed_pwd", full_name="Test Builder")
            db.add(user)
            db.commit()

        resume = ResumePipeline.process_and_save(
            db=db,
            user_id=user.id,
            filename="resume.txt",
            file_bytes=SAMPLE_RESUME_TEXT.encode("utf-8")
        )

        from app.schemas.canonical_profile import CanonicalProfile
        profile = CanonicalProfile.model_validate(resume.parsed_data["canonical_profile"])

        # Test passive verb upgrade without hallucinating new metrics
        bullet1 = "Worked on payment API backend with FastAPI and PostgreSQL."
        rewritten = BulletRewriter.rewrite_bullet(bullet1, profile)
        assert rewritten["verified"] is True
        # Passive "Worked on" should be upgraded to strong verb like "Architected" or "Engineered"
        assert not rewritten["proposed_text"].startswith("Worked on")
        assert "FastAPI" in rewritten["proposed_text"]
        # Ensure no invented percentage was added
        assert "%" not in rewritten["proposed_text"]

        # Test bullet with existing real metric: 35% should be preserved
        bullet2 = "Handled database performance optimization reducing query time by 35%."
        rewritten2 = BulletRewriter.rewrite_bullet(bullet2, profile)
        assert rewritten2["verified"] is True
        assert "35%" in rewritten2["proposed_text"]
        assert not rewritten2["proposed_text"].startswith("Handled")

    finally:
        db.close()

def test_roundtrip_ats_validator():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "test_builder@example.com").first()
        resume = db.query(Resume).filter(Resume.user_id == user.id).order_by(Resume.created_at.desc()).first()
        from app.schemas.canonical_profile import CanonicalProfile
        profile = CanonicalProfile.model_validate(resume.parsed_data["canonical_profile"])

        res = RoundTripValidator.validate(profile)
        assert res["ats_loss_score"] <= 0.05
        assert res["is_safe"] is True
        assert res["status"] == "passed"
    finally:
        db.close()

def test_resume_generation_and_diff_review():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "test_builder@example.com").first()
        resume = db.query(Resume).filter(Resume.user_id == user.id).first()

        req = GenerateResumeRequest(
            resume_id=resume.id,
            mode="role_targeted",
            target_role="Senior Backend Engineer",
            template_id="modern_minimal",
            page_target=1
        )

        version = ResumeGenerator.generate_version(db=db, user_id=user.id, request=req)
        assert version is not None
        assert version.version_num >= 2
        assert version.template_id == "modern_minimal"
        assert version.ats_loss_score <= 0.05
        assert len(version.diffs) > 0

        # Review a diff item (accept)
        first_diff = version.diffs[0]
        assert first_diff.status == "pending"

        updated_diff = ResumeGenerator.review_diff(
            db=db,
            user_id=user.id,
            diff_id=first_diff.id,
            action="accept"
        )
        assert updated_diff.status == "accepted"

        # Check export generation for version's profile
        from app.schemas.canonical_profile import CanonicalProfile
        v_profile = CanonicalProfile.model_validate(version.canonical_profile)
        docx_bytes = ResumeExporter.to_docx(v_profile)
        pdf_bytes = ResumeExporter.to_pdf(v_profile)
        txt_str = ResumeExporter.to_txt(v_profile)
        html_str = ResumeExporter.to_html(v_profile, template_id="modern_minimal")

        assert len(docx_bytes) > 500
        assert len(pdf_bytes) > 500
        assert "JOHN DOE" in txt_str
        assert "Horizon Tech" in html_str
    finally:
        db.close()
