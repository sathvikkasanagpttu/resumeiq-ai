from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from app.services.parser.document_reader import DocumentReader
from app.services.parser.section_detector import SectionDetector
from app.services.parser.entity_extractor import EntityExtractor
from app.models.resume import (
    Resume, ResumeVersion, ResumeSection, CandidateSkill,
    CandidateExperience, CandidateProject, CandidateEducation, CandidateCertification
)
from app.models.evidence import EvidenceItem
from app.models.user import CandidateProfile
from app.core.exceptions import DocumentParsingError
from app.core.logging import logger

class ResumePipeline:
    @classmethod
    def process_and_save(
        cls,
        db: Session,
        user_id: str,
        filename: str,
        file_bytes: bytes
    ) -> Resume:
        """
        Executes full resume parsing pipeline:
        validation -> text extraction -> sections -> entities -> evidence -> DB persistence
        """
        # 1. Text extraction & format validation
        raw_text, file_type = DocumentReader.extract_text(filename, file_bytes)
        file_size = len(file_bytes)

        if len(raw_text.strip()) < 50:
            raise DocumentParsingError("Extracted resume text is too short to be a valid resume (under 50 characters).")

        # 2. Section detection
        detected_sections = SectionDetector.detect_sections(raw_text)
        sections_dict = {sec.section_type: sec.content for sec in detected_sections}

        # 3. Entity & evidence extraction
        contacts = EntityExtractor.extract_contacts(raw_text)
        skills, evidence_items = EntityExtractor.extract_skills_with_evidence(sections_dict, raw_text)
        
        experiences = EntityExtractor.extract_experiences(sections_dict.get("experience", ""))
        projects = EntityExtractor.extract_projects(sections_dict.get("projects", ""))
        educations = EntityExtractor.extract_education(sections_dict.get("education", ""))
        certifications = EntityExtractor.extract_certifications(sections_dict.get("certifications", ""))

        # 4. Create Resume Model
        resume = Resume(
            user_id=user_id,
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            raw_text=raw_text,
            parsed_data={
                "contacts": contacts,
                "sections_detected": [s.section_type for s in detected_sections],
                "skills_count": len(skills),
                "experience_count": len(experiences),
                "projects_count": len(projects)
            }
        )
        db.add(resume)
        db.flush()

        # 5. Save Sections
        for sec in detected_sections:
            db_sec = ResumeSection(
                resume_id=resume.id,
                section_type=sec.section_type,
                title=sec.title,
                raw_content=sec.content,
                start_index=sec.start_line,
                end_index=sec.end_line
            )
            db.add(db_sec)

        # 6. Save Skills
        for sk in skills:
            db_sk = CandidateSkill(
                resume_id=resume.id,
                original_text=sk.original_text,
                normalized_skill=sk.normalized_skill,
                category=sk.category,
                source_section=sk.source_section,
                source_evidence=sk.source_evidence,
                confidence=sk.confidence,
                evidence_strength=sk.evidence_strength
            )
            db.add(db_sk)

        # 7. Save Experiences
        for exp in experiences:
            db_exp = CandidateExperience(
                resume_id=resume.id,
                company=exp.company,
                role=exp.role,
                location=exp.location,
                start_date=exp.start_date,
                end_date=exp.end_date,
                is_current=exp.is_current,
                duration_months=exp.duration_months,
                description=exp.description,
                bullet_points=exp.bullet_points,
                technologies=exp.technologies
            )
            db.add(db_exp)

        # 8. Save Projects
        for proj in projects:
            db_proj = CandidateProject(
                resume_id=resume.id,
                title=proj.title,
                role=proj.role,
                description=proj.description,
                technologies=proj.technologies,
                outcomes=proj.outcomes,
                url=proj.url
            )
            db.add(db_proj)

        # 9. Save Educations
        for edu in educations:
            db_edu = CandidateEducation(
                resume_id=resume.id,
                institution=edu.institution,
                degree=edu.degree,
                field_of_study=edu.field_of_study,
                graduation_year=edu.graduation_year,
                gpa=edu.gpa
            )
            db.add(db_edu)

        # 10. Save Certifications
        for cert in certifications:
            db_cert = CandidateCertification(
                resume_id=resume.id,
                name=cert.name,
                issuing_org=cert.issuing_org,
                issue_date=cert.issue_date,
                expiration_date=cert.expiration_date,
                credential_id=cert.credential_id
            )
            db.add(db_cert)

        # 11. Save Evidence Items
        for ev in evidence_items:
            db_ev = EvidenceItem(
                resume_id=resume.id,
                entity_type=ev.entity_type,
                entity_name=ev.entity_name,
                context_snippet=ev.context_snippet,
                source_section=ev.source_section,
                evidence_strength=ev.evidence_strength,
                confidence_score=ev.confidence_score,
                action_verb=ev.action_verb,
                quantified_impact=ev.quantified_impact,
                metadata_info=ev.metadata_info
            )
            db.add(db_ev)

        # 12. Create Initial ResumeVersion
        version = ResumeVersion(
            resume_id=resume.id,
            version_num=1,
            change_summary="Initial document upload and parsing",
            content_snapshot={
                "skills": [s.normalized_skill for s in skills],
                "experiences": [{"role": e.role, "company": e.company} for e in experiences]
            }
        )
        db.add(version)

        # 13. Update or create CandidateProfile
        profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
        if not profile:
            profile = CandidateProfile(
                user_id=user_id,
                headline=experiences[0].role if experiences else "Software Professional",
                summary=sections_dict.get("summary", "Experienced professional"),
                total_experience_years=len(experiences) * 1.5,
                seniority_level="Senior" if len(experiences) >= 3 else "Mid",
                location=contacts.get("location", "Remote")
            )
            db.add(profile)
        else:
            if experiences:
                profile.headline = experiences[0].role
            profile.total_experience_years = max(profile.total_experience_years, len(experiences) * 1.5)

        db.commit()
        db.refresh(resume)
        logger.info(f"Resume {resume.id} successfully processed for user {user_id}: {len(skills)} skills extracted")
        return resume
