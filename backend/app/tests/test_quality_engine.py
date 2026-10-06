import pytest
from app.schemas.canonical_profile import (
    CanonicalProfile, CanonicalBasics, CanonicalExperience,
    CanonicalSkillCategory, GroundedField, GroundedBullet, GroundedSkillItem
)
from app.services.quality.timeline_engine import TimelineEngine
from app.services.quality.representation_detector import RepresentationGapDetector
from app.services.quality.quality_analyzer import QualityAnalyzer

def test_timeline_engine_detects_anomalies():
    profile = CanonicalProfile(
        basics=CanonicalBasics(
            name=GroundedField(value="Test User"),
            label=GroundedField(value="Developer"),
            email=GroundedField(value="test@example.com"),
            phone=GroundedField(value="555-1234"),
            summary=GroundedField(value="Experienced engineer with 8+ years experience in distributed systems."),
            location=GroundedField(value={"city": "Austin"}),
            profiles=[]
        ),
        experience=[
            CanonicalExperience(
                company=GroundedField(value="Alpha Corp"),
                position=GroundedField(value="Junior Dev"),
                start_date=GroundedField(value="2022"),
                end_date=GroundedField(value="2023"),
                is_current=GroundedField(value=False),
                highlights=[GroundedBullet(value="Worked on internal tools.")]
            ),
            CanonicalExperience(
                company=GroundedField(value="Beta Inc"),
                position=GroundedField(value="Dev"),
                start_date=GroundedField(value="2022"),
                end_date=GroundedField(value="2024"),
                is_current=GroundedField(value=True),
                highlights=[GroundedBullet(value="Built microservices.")]
            )
        ],
        projects=[],
        education=[],
        skills=[],
        certifications=[],
        achievements=[]
    )

    res = TimelineEngine.analyze_timeline(profile)
    # Check that overlap was detected between Alpha Corp and Beta Inc
    assert any(a.anomaly_type == "overlap" for a in res.anomalies)
    # Check that duration contradiction was caught (claimed 8+ years vs ~2-3 year timeline)
    assert any(a.anomaly_type == "duration_contradiction" for a in res.anomalies)

def test_representation_gap_detector():
    profile = CanonicalProfile(
        basics=CanonicalBasics(
            name=GroundedField(value="Test User"),
            label=GroundedField(value="Developer"),
            email=GroundedField(value="test@example.com"),
            phone=GroundedField(value="555-1234"),
            summary=GroundedField(value="Developer"),
            location=GroundedField(value={"city": "Austin"}),
            profiles=[]
        ),
        experience=[
            CanonicalExperience(
                company=GroundedField(value="TechScale"),
                position=GroundedField(value="Backend Engineer"),
                start_date=GroundedField(value="2021"),
                end_date=GroundedField(value="2023"),
                is_current=GroundedField(value=False),
                highlights=[
                    GroundedBullet(value="Built high-throughput backend endpoints with FastAPI and PostgreSQL.")
                ]
            )
        ],
        projects=[],
        education=[],
        skills=[
            CanonicalSkillCategory(
                category_name="Frameworks",
                skills=[GroundedSkillItem(name="FastAPI", normalized_name="FastAPI")]
            )
        ],
        certifications=[],
        achievements=[]
    )

    gaps = RepresentationGapDetector.detect_gaps(profile)
    implied_skills = [g.implied_skill for g in gaps]
    # FastAPI implies Python, PostgreSQL implies SQL
    assert "Python" in implied_skills
    assert "SQL" in implied_skills

def test_quality_analyzer_report():
    profile = CanonicalProfile(
        basics=CanonicalBasics(
            name=GroundedField(value="Sarah Chen"),
            label=GroundedField(value="Senior Engineer"),
            email=GroundedField(value="sarah@example.com"),
            phone=GroundedField(value="555-0100"),
            summary=GroundedField(value="Senior engineer with 6 years experience building resilient distributed backend systems."),
            location=GroundedField(value={"city": "San Francisco"}),
            profiles=[]
        ),
        experience=[
            CanonicalExperience(
                company=GroundedField(value="FinScale Tech"),
                position=GroundedField(value="Senior Software Engineer"),
                start_date=GroundedField(value="2020"),
                end_date=GroundedField(value="Present"),
                is_current=GroundedField(value=True),
                highlights=[
                    GroundedBullet(
                        value="Architected FastAPI microservices handling 20,000 req/sec, reducing latency by 45%.",
                        quantified_metrics=["20,000 req/sec", "45%"]
                    ),
                    GroundedBullet(
                        value="Worked on database caching with Redis.",
                        quantified_metrics=[]
                    )
                ]
            )
        ],
        projects=[],
        education=[],
        skills=[
            CanonicalSkillCategory(
                category_name="Languages",
                skills=[GroundedSkillItem(name="Python", normalized_name="Python")]
            )
        ],
        certifications=[],
        achievements=[]
    )

    report = QualityAnalyzer.analyze_resume("test_resume_123", profile)
    assert report.overall_quality_score > 0
    assert len(report.components) == 8
    # Should flag the weak verb "Worked on"
    impact_comp = next(c for c in report.components if c.name == "Impact Language")
    assert any(i.issue_type == "weak_verb" for i in impact_comp.issues)
