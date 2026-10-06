import pytest
from app.schemas.canonical_profile import (
    CanonicalProfile, CanonicalBasics, CanonicalExperience,
    CanonicalProject, CanonicalEducation, CanonicalSkillCategory,
    GroundedField, GroundedBullet, GroundedSkillItem, SourceSpan
)

def test_canonical_profile_creation_and_rendering_filter():
    # Construct a sample CanonicalProfile
    profile = CanonicalProfile(
        basics=CanonicalBasics(
            name=GroundedField(value="Alex Morgan", source="extracted", confidence=1.0),
            label=GroundedField(value="Senior Backend Engineer", source="extracted", confidence=0.95),
            email=GroundedField(value="alex@example.com", source="extracted", confidence=1.0),
            phone=GroundedField(value="+1 555-0192", source="extracted", confidence=0.9),
            summary=GroundedField(value="Senior engineer with 6 years experience.", source="extracted", confidence=0.9),
            location=GroundedField(value={"city": "San Francisco", "region": "CA"}, source="extracted", confidence=0.9),
            profiles=[]
        ),
        experience=[
            CanonicalExperience(
                company=GroundedField(value="FinScale Tech", source="extracted"),
                position=GroundedField(value="Senior Engineer", source="extracted"),
                start_date=GroundedField(value="2021", source="extracted"),
                end_date=GroundedField(value="Present", source="extracted"),
                is_current=GroundedField(value=True, source="extracted"),
                highlights=[
                    GroundedBullet(
                        value="Built FastAPI backend handling 20,000 req/sec.",
                        source="extracted",
                        confidence=0.98,
                        quantified_metrics=["20,000 req/sec"]
                    ),
                    GroundedBullet(
                        value="User added note: Led team of 4 backend engineers.",
                        source="user_confirmed",
                        confidence=1.0
                    ),
                    GroundedBullet(
                        value="AI Hallucinated: Managed \\$50M AWS cloud spend.",
                        source="ai_suggested_pending",
                        is_accepted=False,
                        confidence=0.5
                    ),
                    GroundedBullet(
                        value="AI Suggestion accepted: Optimized database connection pooling by 30%.",
                        source="ai_suggested_pending",
                        is_accepted=True,
                        confidence=0.92
                    ),
                ],
                technologies=[]
            )
        ],
        projects=[],
        education=[],
        skills=[
            CanonicalSkillCategory(
                category_name="Languages",
                skills=[
                    GroundedSkillItem(
                        name="Python",
                        normalized_name="Python",
                        source="extracted",
                        evidence_strength="verified",
                        usage_depth="used_in_production_with_outcome"
                    ),
                    GroundedSkillItem(
                        name="Rust",
                        normalized_name="Rust",
                        source="ai_suggested_pending",
                        evidence_strength="missing"
                    )
                ]
            )
        ],
        certifications=[],
        achievements=[]
    )

    # Validate full profile contains all items
    assert len(profile.experience[0].highlights) == 4
    assert len(profile.skills[0].skills) == 2

    # Validate renderable copy strictly filters out pending AI suggestions
    renderable = profile.get_renderable_copy()
    exp_bullets = renderable.experience[0].highlights
    assert len(exp_bullets) == 3
    
    bullet_values = [b.value for b in exp_bullets]
    assert "Built FastAPI backend handling 20,000 req/sec." in bullet_values
    assert "User added note: Led team of 4 backend engineers." in bullet_values
    assert "AI Suggestion accepted: Optimized database connection pooling by 30%." in bullet_values
    # Ensure unaccepted AI suggestion was BLOCKED
    assert "AI Hallucinated: Managed \\$50M AWS cloud spend." not in bullet_values

    # Ensure unconfirmed skills were BLOCKED
    skill_names = [s.name for s in renderable.skills[0].skills]
    assert "Python" in skill_names
    assert "Rust" not in skill_names
