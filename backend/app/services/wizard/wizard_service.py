import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from app.models.resume import Resume, ResumeVersion, UserConfirmedFact
from app.schemas.canonical_profile import CanonicalProfile, GroundedSocialProfile, GroundedSkillItem
from app.schemas.wizard import (
    WizardQuestion, WizardAnswer, WizardSessionResponse, WizardSubmitResponse
)
from app.services.quality.timeline_engine import TimelineEngine
from app.services.ontology.taxonomy import ontology
from app.core.logging import logger

class WizardService:
    """
    Missing-Info Wizard.
    Formulates targeted, non-presumptive questions for candidate gaps.
    Every answer is stored as user_confirmed evidence.
    """

    @classmethod
    def generate_questions(cls, resume: Resume, profile: CanonicalProfile) -> WizardSessionResponse:
        questions: List[WizardQuestion] = []

        # 1. Check for missing summary
        summary_val = str(profile.basics.summary.value or "").strip()
        if not summary_val or len(summary_val) < 25 or "experienced professional" in summary_val.lower():
            questions.append(WizardQuestion(
                id="q_summary_01",
                category="summary",
                target_section="Professional Summary",
                prompt_text="Your resume could benefit from a punchier professional summary. In 1-2 sentences, what is your primary engineering specialty and target focus?",
                context_hint="Grounded in your real background. Focus on your strongest languages and system types.",
                example_answers=[
                    "Senior Backend Engineer specializing in high-throughput distributed APIs with Python and PostgreSQL.",
                    "Frontend Developer focused on performant React and Next.js design systems."
                ]
            ))

        # 2. Check for missing links
        has_github = any(p.network.lower() == "github" for p in profile.basics.profiles)
        has_linkedin = any(p.network.lower() == "linkedin" for p in profile.basics.profiles)
        if not has_github or not has_linkedin:
            missing_links = []
            if not has_github: missing_links.append("GitHub")
            if not has_linkedin: missing_links.append("LinkedIn")
            questions.append(WizardQuestion(
                id="q_links_01",
                category="link",
                target_section="Basics & Links",
                prompt_text=f"Recruiters look for verifiable work. Do you have a {' or '.join(missing_links)} profile URL you would like to include?",
                context_hint="Adding your GitHub or LinkedIn URL enhances evidence verification.",
                example_answers=["https://github.com/myusername", "https://linkedin.com/in/myprofile"]
            ))

        # 3. Check bullets without impact in experience
        for exp in profile.experience:
            c_name = str(exp.company.value or "Recent Role")
            for b in exp.highlights:
                if not b.quantified_metrics and len(b.value.split()) > 6:
                    questions.append(WizardQuestion(
                        id=f"q_metric_{b.id or uuid.uuid4().hex[:6]}",
                        category="metric",
                        target_entity_id=b.id,
                        target_section=f"Experience @ {c_name}",
                        prompt_text=f"For your role at {c_name}: '{b.value}' — What was the measurable outcome or scale? (e.g. latency reduced, users served, requests/sec, or percentage)?",
                        context_hint="If no exact number exists, describe the qualitative improvement. Never fabricate metrics.",
                        example_answers=[
                            "Reduced query latency by 35% across 2M rows",
                            "Handled 15,000 requests/sec with zero downtime",
                            "Accelerated feature deployment cycles from 2 weeks to 3 days"
                        ],
                        has_metric_requested=True
                    ))
                    if len(questions) >= 4:
                        break
            if len(questions) >= 4:
                break

        # 4. Check for timeline gaps
        timeline = TimelineEngine.analyze_timeline(profile)
        for anomaly in timeline.anomalies:
            if anomaly.anomaly_type == "employment_gap":
                questions.append(WizardQuestion(
                    id="q_gap_01",
                    category="timeline_gap",
                    target_section="Work History Timeline",
                    prompt_text=f"We noticed a career interval between {anomaly.dates}. Did you complete independent projects, open-source work, certifications, or studies during this period?",
                    context_hint="Explaining gaps proactively gives recruiters confidence.",
                    example_answers=[
                        "Completed independent AWS Solutions Architect certification and built 2 full-stack cloud projects.",
                        "Undertook full-time professional career transition coursework."
                    ]
                ))
                break

        # Limit to top 5 questions
        final_questions = questions[:5]

        return WizardSessionResponse(
            resume_id=resume.id,
            total_questions=len(final_questions),
            questions=final_questions,
            summary_message=(
                f"Generated {len(final_questions)} targeted questions to substantiate your resume with verified evidence."
            )
        )

    @classmethod
    def apply_answers(
        cls,
        db: Session,
        user_id: str,
        resume_id: str,
        answers: List[WizardAnswer]
    ) -> WizardSubmitResponse:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            raise ValueError(f"Resume {resume_id} not found.")

        parsed_data = resume.parsed_data or {}
        raw_canonical = parsed_data.get("canonical_profile")
        if not raw_canonical:
            from app.services.parser.canonical_builder import CanonicalProfileBuilder
            raw_canonical = CanonicalProfileBuilder.build_from_parsed_data(
                raw_text=resume.raw_text,
                contacts=parsed_data.get("contacts", {}),
                sections_dict={s.section_type: s.raw_content for s in resume.sections},
                skills=resume.skills,
                experiences=resume.experiences,
                projects=resume.projects,
                educations=resume.educations,
                certifications=resume.certifications
            ).model_dump()

        profile = CanonicalProfile.model_validate(raw_canonical)
        facts_added = 0

        for ans in answers:
            if not ans.answer_text.strip():
                continue

            # 1. Record UserConfirmedFact in DB
            fact = UserConfirmedFact(
                id=str(uuid.uuid4()),
                user_id=user_id,
                resume_id=resume.id,
                fact_category="wizard_response",
                field_target=ans.question_id,
                claim_text=ans.answer_text.strip(),
                verification_source="wizard_answer"
            )
            db.add(fact)
            facts_added += 1

            # 2. Update CanonicalProfile
            if ans.question_id == "q_summary_01":
                profile.basics.summary.value = ans.answer_text.strip()
                profile.basics.summary.source = "user_confirmed"
                profile.basics.summary.confidence = 1.0

            elif ans.question_id == "q_links_01":
                url = ans.answer_text.strip()
                net = "GitHub" if "github" in url.lower() else "LinkedIn" if "linkedin" in url.lower() else "Portfolio"
                profile.basics.profiles.append(GroundedSocialProfile(
                    network=net,
                    url=url,
                    source="user_confirmed",
                    confidence=1.0
                ))

            elif ans.question_id.startswith("q_metric_"):
                # Append verified metric to the corresponding bullet
                target_bullet_id = ans.question_id.replace("q_metric_", "")
                for exp in profile.experience:
                    for b in exp.highlights:
                        if b.id == target_bullet_id or not b.quantified_metrics:
                            # Enhance bullet with user confirmed metric
                            if ans.confirmed_metric and ans.confirmed_metric not in b.value:
                                b.value = f"{b.value.rstrip('.')} ({ans.confirmed_metric})."
                                b.quantified_metrics.append(ans.confirmed_metric)
                            else:
                                b.value = f"{b.value.rstrip('.')} ({ans.answer_text.strip()})."
                                b.quantified_metrics.append(ans.answer_text.strip())
                            b.source = "user_confirmed"
                            b.confidence = 1.0
                            break

            # Add any confirmed technologies
            if ans.confirmed_technologies:
                for tech in ans.confirmed_technologies:
                    norm_t = ontology.normalize(tech) or tech
                    # Find category or append
                    if profile.skills:
                        profile.skills[0].skills.append(GroundedSkillItem(
                            id=str(uuid.uuid4()),
                            name=tech,
                            normalized_name=norm_t,
                            source="user_confirmed",
                            confidence=1.0,
                            evidence_strength="verified",
                            usage_depth="used_in_project"
                        ))

        # 3. Update Resume and latest ResumeVersion with enriched profile
        updated_dump = profile.model_dump()
        new_parsed = dict(resume.parsed_data) if resume.parsed_data else {}
        new_parsed["canonical_profile"] = updated_dump
        resume.parsed_data = new_parsed
        flag_modified(resume, "parsed_data")

        latest_version = db.query(ResumeVersion).filter(
            ResumeVersion.resume_id == resume.id
        ).order_by(ResumeVersion.version_num.desc()).first()

        if latest_version:
            latest_version.canonical_profile = updated_dump
            latest_version.content_snapshot = updated_dump
            latest_version.change_summary = f"Enriched with {facts_added} user-confirmed wizard facts."

        db.commit()
        logger.info(f"Enriched resume {resume_id} with {facts_added} user-confirmed wizard answers.")

        return WizardSubmitResponse(
            resume_id=resume.id,
            facts_added_count=facts_added,
            message=f"Successfully applied {facts_added} verified facts to your Canonical Profile."
        )
