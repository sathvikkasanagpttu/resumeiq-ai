import os
import sys
import json
import time
from typing import Dict, Any, List
import numpy as np

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.resume import Resume
from app.services.parser.resume_pipeline import ResumePipeline
from app.services.parser.canonical_builder import CanonicalProfileBuilder
from app.services.evidence.verification import VerificationPipeline
from app.services.builder.bullet_rewriter import BulletRewriter
from app.services.builder.roundtrip_validator import RoundTripValidator
from app.schemas.canonical_profile import CanonicalProfile
from app.schemas.builder import GenerateResumeRequest
from app.services.builder.generation_engine import ResumeGenerator
from app.services.ontology.taxonomy import ontology

BENCHMARK_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app", "tests", "evaluation", "eval_dataset_v2.json"))

def run_v2_evaluation():
    print("=" * 80)
    print("RESUMEIQ v2 AI SYSTEM BENCHMARK & QUALITY GATES EVALUATION")
    print("=" * 80)
    print(f"Loading benchmark dataset from: {BENCHMARK_PATH}")

    with open(BENCHMARK_PATH, "r") as f:
        cases = json.load(f)

    print(f"Loaded {len(cases)} diverse candidate test cases.")
    print("-" * 80)

    db = SessionLocal()
    eval_user = db.query(User).filter(User.email == "v2_eval_runner@resumeiq.ai").first()
    if not eval_user:
        eval_user = User(
            email="v2_eval_runner@resumeiq.ai",
            hashed_password="dummy_hashed_password",
            full_name="V2 Evaluation Runner"
        )
        db.add(eval_user)
        db.commit()

    latencies: List[float] = []
    extraction_accuracies: List[float] = []
    verification_precisions: List[float] = []
    hallucination_counts: List[int] = []
    total_generated_bullets: List[int] = []
    ats_loss_scores: List[float] = []
    ats_pass_count = 0

    print(f"{'Case ID':<30} | {'Extr Acc':<9} | {'Verif Prec':<10} | {'Halluc':<7} | {'ATS Loss':<8} | {'Latency':<7}")
    print("-" * 80)

    for case in cases:
        case_id = case["id"]
        resume_text = case["resume_text"]
        gt = case["ground_truth"]
        expected_skills = [(ontology.normalize(s) or s).lower() for s in gt.get("expected_skills", [])]
        unsupported_claims = gt.get("unsupported_claims", [])

        t0 = time.time()

        # 1. Pipeline extraction
        resume = ResumePipeline.process_and_save(
            db=db,
            user_id=eval_user.id,
            filename=f"{case_id}.txt",
            file_bytes=resume_text.encode("utf-8")
        )

        canonical_dump = resume.parsed_data.get("canonical_profile")
        profile = CanonicalProfile.model_validate(canonical_dump)

        # Measure Extraction Accuracy
        extracted_skills = []
        for cat in profile.skills:
            for sk in cat.skills:
                extracted_skills.append(sk.normalized_name.lower())

        found_count = sum(1 for es in expected_skills if es in extracted_skills)
        extr_acc = (found_count / len(expected_skills)) if expected_skills else 1.0
        extraction_accuracies.append(extr_acc)

        # 2. Measure Evidence Verification Precision
        # Supported claims (expected skills present in resume should be supported)
        correct_verifs = 0
        total_verifs = 0
        test_supported = [s for s in expected_skills if s in extracted_skills][:3]
        for es in test_supported:
            claim = VerificationPipeline.verify_claim(resume, f"Candidate is proficient in {es}", es)
            if claim.status in ["supported", "partially_supported"]:
                correct_verifs += 1
            total_verifs += 1

        # Unsupported claims (must be rejected / unsupported)
        for uc in unsupported_claims:
            claim = VerificationPipeline.verify_claim(resume, f"Candidate is proficient in {uc}", uc)
            if claim.status in ["unsupported", "missing", "uncertain"]:
                correct_verifs += 1
            total_verifs += 1

        verif_prec = (correct_verifs / total_verifs) if total_verifs > 0 else 1.0
        verification_precisions.append(verif_prec)

        # 3. Auto-Build Generation & Hallucination Audit
        gen_req = GenerateResumeRequest(
            resume_id=resume.id,
            mode="clean_rebuild",
            template_id="classic",
            page_target=1
        )
        version = ResumeGenerator.generate_version(db=db, user_id=eval_user.id, request=gen_req)

        # Audit diffs for hallucinations
        case_hallucinations = 0
        case_bullets_count = 0
        for diff in version.diffs:
            case_bullets_count += 1
            # Check proposed text against candidate's profile
            is_valid, _, flagged = VerificationPipeline.validate_generated_text(resume, diff.proposed_text)
            if not is_valid:
                case_hallucinations += len(flagged)
            # Check numbers
            rewriter_metrics = BulletRewriter.extract_metrics(diff.proposed_text)
            orig_metrics = BulletRewriter.extract_metrics(diff.original_text or "")
            for m in rewriter_metrics:
                if m not in orig_metrics:
                    case_hallucinations += 1

        hallucination_counts.append(case_hallucinations)
        total_generated_bullets.append(max(1, case_bullets_count))

        # 4. ATS Round-Trip Test
        ats_loss = version.ats_loss_score
        ats_loss_scores.append(ats_loss)
        if ats_loss <= 0.05:
            ats_pass_count += 1

        elapsed = round(time.time() - t0, 3)
        latencies.append(elapsed)

        print(
            f"{case_id:<30} | {extr_acc*100:>7.1f}% | {verif_prec*100:>8.1f}% | "
            f"{case_hallucinations:>7d} | {ats_loss*100:>6.1f}% | {elapsed:>6.2f}s"
        )

    db.close()

    # Aggregate Metrics
    avg_extr_acc = float(np.mean(extraction_accuracies))
    avg_verif_prec = float(np.mean(verification_precisions))
    total_hallucs = sum(hallucination_counts)
    total_bullets = sum(total_generated_bullets)
    halluc_rate = (total_hallucs / total_bullets) if total_bullets > 0 else 0.0
    ats_success_rate = ats_pass_count / len(cases)
    p50_latency = float(np.percentile(latencies, 50))
    p95_latency = float(np.percentile(latencies, 95))

    print("=" * 80)
    print("BENCHMARK SUMMARY RESULTS & QUALITY GATES:")
    print("=" * 80)
    print(f"• Total Resumes Evaluated:            {len(cases)}")
    print(f"• Extraction Accuracy:                {avg_extr_acc*100:.2f}%  (Gate Target: > 90.00%)")
    print(f"• Verification Precision:             {avg_verif_prec*100:.2f}%  (Gate Target: > 95.00%)")
    print(f"• Hallucination Rate:                 {halluc_rate*100:.2f}%  (Gate Target: 0.00%)")
    print(f"• ATS Round-Trip Success Rate:        {ats_success_rate*100:.2f}%  (Gate Target: > 95.00%)")
    print(f"• End-to-End Latency (p50):           {p50_latency:.2f}s   (Gate Target: < 3.00s)")
    print(f"• End-to-End Latency (p95):           {p95_latency:.2f}s   (Gate Target: < 8.00s)")
    print("=" * 80)

    # Validate Gates
    gates_passed = True
    if avg_extr_acc < 0.90:
        print("❌ FAIL: Extraction Accuracy below 90% threshold.")
        gates_passed = False
    if avg_verif_prec < 0.95:
        print("❌ FAIL: Verification Precision below 95% threshold.")
        gates_passed = False
    if halluc_rate > 0.0001:
        print(f"❌ FAIL: Hallucination Rate ({halluc_rate*100:.2f}%) exceeds 0.00% target.")
        gates_passed = False
    if ats_success_rate < 0.95:
        print(f"❌ FAIL: ATS Success Rate ({ats_success_rate*100:.2f}%) below 95% threshold.")
        gates_passed = False
    if p50_latency > 3.0:
        print(f"❌ FAIL: p50 Latency ({p50_latency:.2f}s) exceeds 3.0s threshold.")
        gates_passed = False
    if p95_latency > 8.0:
        print(f"❌ FAIL: p95 Latency ({p95_latency:.2f}s) exceeds 8.0s threshold.")
        gates_passed = False

    if gates_passed:
        print("✅ ALL CI QUALITY GATES PASSED (100% Zero-Hallucination & ATS-Safety).")
        return 0
    else:
        print("❌ CI QUALITY GATES FAILED.")
        return 1

if __name__ == "__main__":
    code = run_v2_evaluation()
    sys.exit(code)
