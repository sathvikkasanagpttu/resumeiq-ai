import pytest
from app.core.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.resume import Resume, ResumeVersion, UserConfirmedFact
from app.schemas.canonical_profile import (
    CanonicalProfile, CanonicalBasics, CanonicalExperience,
    GroundedField, GroundedBullet
)
from app.schemas.wizard import WizardAnswer
from app.services.wizard.wizard_service import WizardService

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()

def test_wizard_question_generation_and_answer_application(db_session):
    # 1. Setup user and resume
    user = db_session.query(User).filter(User.email == "wizard_test@resumeiq.ai").first()
    if not user:
        user = User(email="wizard_test@resumeiq.ai", hashed_password="hash", full_name="Wizard Tester")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

    profile = CanonicalProfile(
        basics=CanonicalBasics(
            name=GroundedField(value="Morgan Taylor"),
            label=GroundedField(value="Software Engineer"),
            email=GroundedField(value="morgan@example.com"),
            phone=GroundedField(value="555-0199"),
            summary=GroundedField(value=""),  # Empty summary triggers question
            location=GroundedField(value={"city": "Seattle"}),
            profiles=[]  # No links triggers question
        ),
        experience=[
            CanonicalExperience(
                company=GroundedField(value="CloudTech"),
                position=GroundedField(value="Backend Developer"),
                start_date=GroundedField(value="2021"),
                end_date=GroundedField(value="Present"),
                is_current=GroundedField(value=True),
                highlights=[
                    GroundedBullet(
                        id="b_100",
                        value="Implemented internal customer telemetry service without any numbers.",
                        quantified_metrics=[]  # Empty metrics triggers question
                    )
                ]
            )
        ],
        projects=[],
        education=[],
        skills=[],
        certifications=[],
        achievements=[]
    )

    resume = Resume(
        user_id=user.id,
        filename="morgan_resume.txt",
        file_type="txt",
        file_size=1024,
        raw_text="Morgan Taylor\nSoftware Engineer",
        parsed_data={"canonical_profile": profile.model_dump()}
    )
    db_session.add(resume)
    db_session.flush()

    version = ResumeVersion(
        resume_id=resume.id,
        version_num=1,
        content_snapshot=profile.model_dump(),
        canonical_profile=profile.model_dump()
    )
    db_session.add(version)
    db_session.commit()

    # 2. Test Question Generation
    session_res = WizardService.generate_questions(resume, profile)
    assert session_res.total_questions >= 2
    categories = [q.category for q in session_res.questions]
    assert "summary" in categories
    assert "link" in categories

    # 3. Test Answer Submission
    answers = [
        WizardAnswer(
            question_id="q_summary_01",
            answer_text="Backend Engineer specializing in resilient microservices with Go and PostgreSQL."
        ),
        WizardAnswer(
            question_id="q_links_01",
            answer_text="https://github.com/morgantaylor"
        ),
        WizardAnswer(
            question_id="q_metric_b_100",
            answer_text="Reduced latency by 40%",
            confirmed_metric="reduced latency by 40%"
        )
    ]

    submit_res = WizardService.apply_answers(
        db=db_session,
        user_id=user.id,
        resume_id=resume.id,
        answers=answers
    )

    assert submit_res.facts_added_count == 3

    # 4. Verify Canonical Profile has been updated with user_confirmed sources
    db_session.refresh(resume)
    updated_profile_data = resume.parsed_data["canonical_profile"]
    updated_profile = CanonicalProfile.model_validate(updated_profile_data)

    assert "Go and PostgreSQL" in str(updated_profile.basics.summary.value)
    assert updated_profile.basics.summary.source == "user_confirmed"
    assert any("github.com/morgantaylor" in p.url for p in updated_profile.basics.profiles)
    assert any("reduced latency by 40%" in b.value.lower() for b in updated_profile.experience[0].highlights)

    # Verify UserConfirmedFact entries exist in DB
    facts = db_session.query(UserConfirmedFact).filter(UserConfirmedFact.resume_id == resume.id).all()
    assert len(facts) >= 3
