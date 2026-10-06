import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.resume import Resume, InterviewPrepSession
from app.schemas.canonical_profile import CanonicalProfile
from app.schemas.builder import InterviewPrepResponse, InterviewPrepQuestion
from app.services.builder.template_engine import get_val
from app.core.logging import logger

class InterviewPrepService:
    """
    Evidence-Grounded Interview Preparation Service.
    Generates behavioral, architectural, and situational questions linked
    directly to verified candidate evidence items with STAR talking point skeletons.
    """

    @classmethod
    def generate_prep(
        cls,
        db: Session,
        user_id: str,
        resume_id: str,
        target_role: Optional[str] = None
    ) -> InterviewPrepResponse:
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
        effective_role = target_role or get_val(profile.basics.label, "Software Engineer")

        questions: List[InterviewPrepQuestion] = []

        # 1. Generate questions from verified experience highlights
        for exp in profile.experience:
            comp_name = get_val(exp.company, "Enterprise")
            pos_name = get_val(exp.position, "Engineer")

            for highlight in exp.highlights:
                bullet_val = highlight.value.strip()
                if not bullet_val:
                    continue

                # Architecture question
                if any(w in bullet_val.lower() for w in ["api", "architected", "system", "backend", "microservices"]):
                    questions.append(InterviewPrepQuestion(
                        id=str(uuid.uuid4()),
                        question=f"Can you walk me through the system architecture you designed at {comp_name}?",
                        category="System Architecture",
                        evidence_id=highlight.id,
                        context_evidence=bullet_val,
                        star_skeleton={
                            "Situation": f"Working as {pos_name} at {comp_name}.",
                            "Task": f"Address complex workflow requirements: {bullet_val[:80]}...",
                            "Action": f"Employed engineering best practices and verified tools ({', '.join(highlight.technologies or ['core backend stack'])}).",
                            "Result": f"Delivered: {highlight.quantified_metrics[0] if highlight.quantified_metrics else 'Reliable, highly available production service.'}"
                        }
                    ))

                # Performance / Scale question
                elif any(w in bullet_val.lower() for w in ["performance", "optimized", "scale", "reduced", "database", "query"]):
                    questions.append(InterviewPrepQuestion(
                        id=str(uuid.uuid4()),
                        question=f"Tell me about a time you optimized performance or resolved a technical bottleneck at {comp_name}.",
                        category="Performance & Scalability",
                        evidence_id=highlight.id,
                        context_evidence=bullet_val,
                        star_skeleton={
                            "Situation": f"Observed latency/bottleneck in system during tenure at {comp_name}.",
                            "Task": "Identify root causes and optimize database/compute layer.",
                            "Action": f"Executed targeted optimizations as evidenced in: '{bullet_val}'.",
                            "Result": f"Achieved measurable efficiency gains: {highlight.quantified_metrics[0] if highlight.quantified_metrics else 'Significant latency reduction.'}"
                        }
                    ))

                # General impact / STAR question
                elif len(questions) < 5 and highlight.quantified_metrics:
                    questions.append(InterviewPrepQuestion(
                        id=str(uuid.uuid4()),
                        question=f"Describe a key initiative where you delivered measurable business or technical results.",
                        category="Impact & Delivery",
                        evidence_id=highlight.id,
                        context_evidence=bullet_val,
                        star_skeleton={
                            "Situation": f"Engaged in core product engineering at {comp_name}.",
                            "Task": "Deliver verified engineering milestones.",
                            "Action": f"Spearheaded implementation: {bullet_val}.",
                            "Result": f"Quantified outcome: {highlight.quantified_metrics[0]}."
                        }
                    ))

        # Limit to top 5 questions
        final_questions = questions[:5]

        # Save session in DB
        session_record = InterviewPrepSession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            resume_id=resume.id,
            qa_pairs=[q.model_dump() for q in final_questions]
        )
        db.add(session_record)
        db.commit()

        logger.info(f"Generated {len(final_questions)} interview prep questions for user {user_id}.")

        return InterviewPrepResponse(
            id=session_record.id,
            resume_id=resume.id,
            target_role=effective_role,
            total_questions=len(final_questions),
            questions=final_questions
        )
