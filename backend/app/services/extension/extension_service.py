import hashlib
import re
import time
import uuid
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.resume import Resume, ResumeVersion, ApplicationTrackerItem
from app.models.job import Job
from app.models.matching import Match
from app.schemas.extension import (
    JDCaptureRequest, JDCaptureResponse,
    QuickMatchRequest, QuickMatchResultResponse,
    MatchedSkillItem, MatchedSkillEvidence,
    TransferableSkillItem, GapItem, MatchComponentDetail,
    ExtensionActionRequest, ExtensionActionResponse,
    ExtensionTrackerSaveRequest, CompareRequest, CompareResponse, CompareItem
)
from app.schemas.job import JobCreate
from app.services.job.job_pipeline import JobPipeline
from app.services.matching.hybrid_matcher import HybridMatcher
from app.services.ontology.skill_matcher import skill_matcher
from app.services.ontology.taxonomy import ontology
from app.services.llm.application_gen import application_generator
from app.core.exceptions import ResourceNotFoundError, AuthorizationError

class ExtensionService:
    """
    Core backend intelligence engine for RESUMEIQ v2.1 Chrome/Edge Extension.
    """

    @classmethod
    def sanitize_and_defend_jd(cls, raw_text: str) -> Tuple[str, List[str]]:
        """
        Prompt-injection defense and text cleaning for untrusted webpage text.
        Strips hidden/zero-width unicode characters and flags injection attempts.
        """
        warnings: List[str] = []

        # 1. Strip zero-width / invisible unicode characters
        cleaned = re.sub(r"[\u200b\u200c\u200d\u200e\u200f\ufeff]", "", raw_text)

        # 2. Check for truncation / "see more" indicators
        if len(cleaned.strip()) < 250:
            warnings.append("Job description appears very brief or truncated. Consider expanding 'See More' on the job page.")
        if re.search(r"(\.\.\.\s*see more|show more\s*\.\.\.|read more\b)", cleaned, re.IGNORECASE):
            warnings.append("Collapsed section detected in page. Make sure you expanded the full job description.")

        # 3. Detect prompt-injection signatures
        injection_patterns = [
            r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
            r"system\s*prompt",
            r"disregard\s+(above|all)",
            r"give\s+a\s+100%\s+score",
            r"output\s+only\s+the\s+word"
        ]
        for pat in injection_patterns:
            if re.search(pat, cleaned, re.IGNORECASE):
                warnings.append("Security Notice: Potential prompt-injection text detected in JD source; ignored by verification engine.")
                cleaned = re.sub(pat, "[FILTERED PROMPT INJECTION]", cleaned, flags=re.IGNORECASE)

        return cleaned.strip(), warnings

    @classmethod
    def classify_is_job_post(cls, text: str) -> Tuple[bool, float]:
        """
        Heuristic job post classifier to prevent analyzing non-job web pages.
        Returns (is_job_post, confidence).
        """
        lower = text.lower()
        job_keywords = [
            "responsibility", "responsibilities", "requirement", "requirements",
            "qualifications", "experience", "skills", "job description", "salary",
            "benefits", "role", "candidate", "about the role", "what you'll do",
            "what you will do", "must have", "nice to have", "years of experience"
        ]
        matches = sum(1 for kw in job_keywords if kw in lower)
        
        # Must have at least 2 distinct job indicators and minimum length
        if len(text.split()) < 30:
            return False, 0.2
        if matches >= 3:
            return True, min(0.99, 0.5 + (matches * 0.08))
        if matches >= 2:
            return True, 0.70
        return False, 0.40

    @classmethod
    def capture_jd(
        cls,
        db: Session,
        user_id: str,
        req: JDCaptureRequest
    ) -> JDCaptureResponse:
        """
        Store, clean, and deduplicate captured JD by SHA-256 content hash.
        """
        cleaned_text, warnings = cls.sanitize_and_defend_jd(req.description_text)
        is_job, job_conf = cls.classify_is_job_post(cleaned_text)

        if not is_job:
            warnings.append("Notice: Text does not strongly resemble a standard job posting.")

        # Compute SHA-256 content hash for deduplication
        content_hash = hashlib.sha256(cleaned_text.encode("utf-8")).hexdigest()

        # Check existing cached job for this user with same hash
        existing = db.query(Job).filter(
            Job.user_id == user_id,
            Job.is_active == True
        ).all()

        for j in existing:
            if (j.parsed_data or {}).get("content_hash") == content_hash:
                return JDCaptureResponse(
                    jd_id=j.id,
                    content_hash=content_hash,
                    title=j.title,
                    company=j.company,
                    location=j.location,
                    is_cached=True,
                    is_valid_job=is_job,
                    requirements_count=len(j.requirements),
                    skills_count=len(j.skills),
                    warnings=warnings,
                    capture_method=req.capture_method,
                    capture_confidence=req.capture_confidence
                )

        # Parse and persist new Job record
        title = req.title or "Position Opportunity"
        company = req.company or "Company"
        
        # Attempt heuristic title / company extraction if missing
        lines = [l.strip() for l in cleaned_text.split("\n") if l.strip()]
        if (not req.title or req.title.strip() == "") and len(lines) > 0:
            title = lines[0][:100]
        if (not req.company or req.company.strip() == "") and len(lines) > 1:
            company = lines[1][:100]

        job = JobPipeline.parse_and_save(
            db=db,
            user_id=user_id,
            job_in=JobCreate(
                title=title,
                company=company,
                description=cleaned_text,
                location=req.location,
                work_model=req.work_model or "remote"
            )
        )

        # Store metadata and hash
        from sqlalchemy.orm.attributes import flag_modified
        p_data = dict(job.parsed_data or {})
        p_data["content_hash"] = content_hash
        p_data["source_url"] = req.source_url
        p_data["salary_text"] = req.salary_text
        p_data["capture_method"] = req.capture_method
        job.parsed_data = p_data
        flag_modified(job, "parsed_data")
        db.add(job)
        db.commit()
        db.refresh(job)

        return JDCaptureResponse(
            jd_id=job.id,
            content_hash=content_hash,
            title=job.title,
            company=job.company,
            location=job.location,
            is_cached=False,
            is_valid_job=is_job,
            requirements_count=len(job.requirements),
            skills_count=len(job.skills),
            warnings=warnings,
            capture_method=req.capture_method,
            capture_confidence=req.capture_confidence
        )

    @classmethod
    def compute_quick_match(
        cls,
        db: Session,
        user_id: str,
        req: QuickMatchRequest
    ) -> QuickMatchResultResponse:
        """
        Fast-tier deterministic match computation meeting Section E schema.
        """
        t0 = time.perf_counter()

        # 1. Resolve Resume
        resume = db.query(Resume).filter(Resume.id == req.resume_id).first()
        if not resume:
            raise ResourceNotFoundError(f"Resume {req.resume_id} not found.")
        if resume.user_id != user_id:
            raise AuthorizationError("Access denied to requested resume.")

        # 2. Resolve Job (via jd_id, job_id, raw_jd_text, or job_data)
        warnings: List[str] = []
        target_jd_id = req.jd_id or req.job_id
        target_raw_text = req.raw_jd_text
        target_title = req.title
        target_company = req.company
        target_source_url = req.source_url

        if not target_raw_text and req.job_data and isinstance(req.job_data, dict):
            target_raw_text = (
                req.job_data.get("description")
                or req.job_data.get("description_text")
                or req.job_data.get("raw_jd_text")
            )
            target_title = target_title or req.job_data.get("title")
            target_company = target_company or req.job_data.get("company")
            target_source_url = target_source_url or req.job_data.get("url") or req.job_data.get("source_url")

        if target_jd_id:
            job = db.query(Job).filter(Job.id == target_jd_id).first()
            if not job:
                raise ResourceNotFoundError(f"Job {target_jd_id} not found.")
        elif target_raw_text:
            capture_res = cls.capture_jd(
                db=db,
                user_id=user_id,
                req=JDCaptureRequest(
                    title=target_title or "Target Position",
                    company=target_company or "Target Company",
                    description_text=target_raw_text,
                    source_url=target_source_url,
                    capture_method=req.capture_method or "selection",
                    capture_confidence=req.capture_confidence or 0.95
                )
            )
            warnings.extend(capture_res.warnings)
            job = db.query(Job).filter(Job.id == capture_res.jd_id).first()
        else:
            raise ValueError("Either jd_id or raw_jd_text must be provided.")

        t_resolve = (time.perf_counter() - t0) * 1000

        # 3. Check for resume freshness warnings
        if len(resume.experiences) == 0:
            warnings.append("Resume contains no dated work experience records.")
        if len(resume.skills) < 3:
            warnings.append("Resume contains very few extracted skills.")

        # 4. Compute Match
        t_match_start = time.perf_counter()
        match = HybridMatcher.compute_match(db=db, resume=resume, job=job)
        t_match = (time.perf_counter() - t_match_start) * 1000

        # 5. Determine Verdict from configurable thresholds
        thresholds = req.verdict_thresholds or {"strong": 80, "good": 65, "partial": 45}
        score = int(round(match.compatibility_score))

        if score >= thresholds.get("strong", 80):
            verdict = "strong_match"
        elif score >= thresholds.get("good", 65):
            verdict = "good_match"
        elif score >= thresholds.get("partial", 45):
            verdict = "partial_match"
        else:
            verdict = "weak_match"

        # 6. Build Matched Skills with Evidence
        cand_skills = {s.normalized_skill.lower(): s for s in resume.skills}
        cand_ev_map = {}
        for ev in resume.evidence_items:
            cand_ev_map.setdefault(ev.entity_name.lower(), []).append(ev)

        matched_skills_list: List[MatchedSkillItem] = []
        transferable_list: List[TransferableSkillItem] = []
        gaps_list: List[GapItem] = []

        for j_sk in job.skills:
            compare_res = skill_matcher.compare_skill(
                j_sk.normalized_skill,
                list(cand_skills.keys())
            )

            req_type = "required" if j_sk.is_required else "preferred"

            if compare_res.match_type in ["exact", "child_skill", "parent_skill"]:
                matched_name = (compare_res.matched_candidate_skill or "").lower()
                ev_items = cand_ev_map.get(matched_name, [])
                evidence_snippets = [
                    MatchedSkillEvidence(
                        text=e.context_snippet,
                        section=e.source_section,
                        strength=e.evidence_strength
                    )
                    for e in ev_items[:2]
                ]
                if not evidence_snippets and matched_name in cand_skills:
                    c_sk = cand_skills[matched_name]
                    evidence_snippets.append(MatchedSkillEvidence(
                        text=c_sk.source_evidence or f"Listed under {c_sk.category}",
                        section=c_sk.source_section or "Skills",
                        strength=c_sk.evidence_strength or "weak"
                    ))

                matched_skills_list.append(MatchedSkillItem(
                    skill=j_sk.skill_name,
                    requirement_type=req_type,
                    evidence=evidence_snippets
                ))
            elif compare_res.match_type == "transferable":
                trans_name = (compare_res.matched_candidate_skill or "").lower()
                trans_ev = ""
                if trans_name in cand_skills:
                    trans_ev = cand_skills[trans_name].source_evidence
                transferable_list.append(TransferableSkillItem(
                    skill=j_sk.skill_name,
                    transferable_from=compare_res.matched_candidate_skill or "",
                    affinity=round(compare_res.match_score, 2),
                    evidence=trans_ev or f"Demonstrated through {compare_res.matched_candidate_skill}"
                ))
            else:
                # Skill Gap
                severity = "critical" if j_sk.is_required else "moderate"
                gaps_list.append(GapItem(
                    skill=j_sk.skill_name,
                    severity=severity,
                    type="missing",
                    recommendation=f"Highlight relevant experience or complete targeted project for {j_sk.skill_name}.",
                    confidence=0.88
                ))

        # Check representation gaps
        for exp in resume.experiences:
            desc = " ".join(exp.bullet_points or [])
            for j_sk in job.skills:
                if j_sk.skill_name.lower() in desc.lower() and j_sk.normalized_skill.lower() not in cand_skills:
                    gaps_list.append(GapItem(
                        skill=j_sk.skill_name,
                        severity="representation",
                        type="representation",
                        recommendation=f"You mentioned {j_sk.skill_name} in your experience at {exp.company}; add it explicitly to your skills section.",
                        confidence=0.92
                    ))

        # 7. Build Components Map
        components_map: Dict[str, MatchComponentDetail] = {}
        for comp in match.components:
            components_map[comp.component_name] = MatchComponentDetail(
                score=round(comp.raw_score, 1),
                weight=round(comp.weight, 2),
                explanation=comp.explanation
            )

        t_total = (time.perf_counter() - t0) * 1000

        explanation_headline = match.explanation_summary.get("headline") if match.explanation_summary else None
        explanation_body = match.explanation_summary.get("overall_assessment") if match.explanation_summary else None
        full_explanation = f"{explanation_headline}. {explanation_body}" if explanation_headline else "Deterministic evaluation completed."

        return QuickMatchResultResponse(
            schema_version="1.0",
            match_id=match.id,
            resume_id=resume.id,
            jd_id=job.id,
            verdict=verdict,
            verdict_thresholds=thresholds,
            compatibility_score=score,
            components=components_map,
            matched_skills=matched_skills_list,
            transferable=transferable_list,
            gaps=gaps_list,
            explanation=full_explanation,
            warnings=warnings,
            capture={
                "method": req.capture_method or (job.parsed_data or {}).get("capture_method", "site_adapter"),
                "confidence": req.capture_confidence or 0.95,
                "job_title": job.title,
                "company": job.company,
                "location": job.location
            },
            timings_ms={
                "resolve_ms": round(t_resolve, 2),
                "matching_ms": round(t_match, 2),
                "total_ms": round(t_total, 2)
            }
        )

    @classmethod
    def execute_action(
        cls,
        db: Session,
        user_id: str,
        req: ExtensionActionRequest
    ) -> ExtensionActionResponse:
        """
        Execute one-click tailoring, cover letter, or recruiter outreach.
        """
        match = None
        if req.match_id:
            match = db.query(Match).filter(Match.id == req.match_id).first()
        elif req.resume_id:
            query = db.query(Match).filter(Match.resume_id == req.resume_id)
            if req.job_id:
                query = query.filter(Match.job_id == req.job_id)
            match = query.order_by(Match.created_at.desc()).first()

        if not match:
            raise ResourceNotFoundError(f"Match not found for action {req.action_type}.")
        if match.resume.user_id != user_id:
            raise AuthorizationError("Access denied to match data.")

        job = match.job
        resume = match.resume

        if req.action_type == "cover_letter":
            mat = application_generator.generate_material(
                db=db,
                user_id=user_id,
                request=type("Req", (), {"doc_type": "cover_letter"})(),
                match=match
            )
            return ExtensionActionResponse(
                action_type="cover_letter",
                status="success",
                title=f"Cover Letter for {job.title} @ {job.company}",
                content=mat.content,
                cited_evidence=[c.model_dump() for c in mat.grounded_citations],
                unsupported_rejected=mat.unsupported_claims_rejected,
                confidence_score=mat.confidence_score
            )
        elif req.action_type == "recruiter_message":
            mat = application_generator.generate_material(
                db=db,
                user_id=user_id,
                request=type("Req", (), {"doc_type": "recruiter_message"})(),
                match=match
            )
            return ExtensionActionResponse(
                action_type="recruiter_message",
                status="success",
                title=f"Outreach Note for {job.company} Recruiter",
                content=mat.content,
                cited_evidence=[c.model_dump() for c in mat.grounded_citations],
                unsupported_rejected=mat.unsupported_claims_rejected,
                confidence_score=mat.confidence_score
            )
        else:  # tailor
            # Suggest truthful bullet optimizations from evidence
            from app.services.llm.optimizer import resume_optimizer
            opt = resume_optimizer.optimize(db=db, match=match)
            tailor_bullets = []
            for m in opt.modifications:
                tailor_bullets.append(f"• Section {m.section}:\n  Original: {m.original_text}\n  Tailored: {m.optimized_text}\n  Grounded Proof: {m.grounded_evidence}")
            
            content_text = f"Tailored Alignment for {job.title} at {job.company}:\n\n" + "\n\n".join(tailor_bullets)
            return ExtensionActionResponse(
                action_type="tailor",
                status="success",
                title=f"Tailored Experience Highlights for {job.title}",
                content=content_text,
                cited_evidence=[{"section": m.section, "evidence": m.grounded_evidence} for m in opt.modifications],
                unsupported_rejected=[],
                confidence_score=0.95
            )

    @classmethod
    def save_tracker_item(
        cls,
        db: Session,
        user_id: str,
        req: ExtensionTrackerSaveRequest
    ) -> Dict[str, Any]:
        match = None
        if req.match_id:
            match = db.query(Match).filter(Match.id == req.match_id).first()
        elif req.job_id:
            match = db.query(Match).join(Resume).filter(
                Resume.user_id == user_id,
                Match.job_id == req.job_id
            ).order_by(Match.created_at.desc()).first()

        if not match:
            raise ResourceNotFoundError("Match not found.")
        if match.resume.user_id != user_id:
            raise AuthorizationError("Access denied.")

        stage = req.stage or req.status or "saved"

        item = ApplicationTrackerItem(
            id=str(uuid.uuid4()),
            user_id=user_id,
            job_id=match.job_id,
            resume_version_id=None,
            role_title=match.job.title,
            company=match.job.company,
            status=stage,
            outcome_notes=req.notes or f"Saved from ResumeIQ Chrome Extension (Compatibility: {int(match.compatibility_score)}%)"
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return {
            "status": "success",
            "tracker_id": item.id,
            "job_title": item.role_title,
            "company": item.company,
            "stage": item.status,
            "message": f"Successfully saved {item.role_title} at {item.company} to application tracker."
        }

    @classmethod
    def compare_resumes(
        cls,
        db: Session,
        user_id: str,
        req: CompareRequest
    ) -> CompareResponse:
        """
        Compare 2-3 resume versions against the same job description.
        """
        # Resolve Job
        target_jd_id = req.jd_id or req.job_id
        target_raw_text = req.raw_jd_text
        target_title = req.title
        target_company = req.company

        if not target_raw_text and req.job_data and isinstance(req.job_data, dict):
            target_raw_text = (
                req.job_data.get("description")
                or req.job_data.get("description_text")
                or req.job_data.get("raw_jd_text")
            )
            target_title = target_title or req.job_data.get("title")
            target_company = target_company or req.job_data.get("company")

        if target_jd_id:
            job = db.query(Job).filter(Job.id == target_jd_id).first()
            if not job:
                raise ResourceNotFoundError(f"Job {target_jd_id} not found.")
        elif target_raw_text:
            cap = cls.capture_jd(
                db=db,
                user_id=user_id,
                req=JDCaptureRequest(
                    title=target_title or "Target Position",
                    company=target_company or "Target Company",
                    description_text=target_raw_text
                )
            )
            job = db.query(Job).filter(Job.id == cap.jd_id).first()
        else:
            raise ValueError("Either jd_id or raw_jd_text must be provided.")

        comparisons: List[CompareItem] = []
        best_score = -1
        best_resume_id = req.resume_ids[0]
        best_resume_name = "Resume"

        for r_id in req.resume_ids:
            resume = db.query(Resume).filter(Resume.id == r_id, Resume.user_id == user_id).first()
            if not resume:
                continue

            match = HybridMatcher.compute_match(db=db, resume=resume, job=job)
            sc = int(round(match.compatibility_score))
            verdict = "strong_match" if sc >= 80 else ("good_match" if sc >= 65 else ("partial_match" if sc >= 45 else "weak_match"))

            strengths = match.explanation_summary.get("top_strengths", []) if match.explanation_summary else []
            concerns = match.explanation_summary.get("critical_concerns", []) if match.explanation_summary else []

            comparisons.append(CompareItem(
                resume_id=resume.id,
                resume_name=resume.filename,
                compatibility_score=sc,
                verdict=verdict,
                top_strengths=strengths[:3],
                critical_gaps_count=len(concerns)
            ))

            if sc > best_score:
                best_score = sc
                best_resume_id = resume.id
                best_resume_name = resume.filename

        reason = f"'{best_resume_name}' scores highest ({best_score}%) due to greater verified skill coverage and stronger experience alignment for {job.title}."

        return CompareResponse(
            winning_resume_id=best_resume_id,
            winning_resume_name=best_resume_name,
            winning_score=best_score,
            recommendation_reason=reason,
            comparisons=comparisons
        )

extension_service = ExtensionService()
