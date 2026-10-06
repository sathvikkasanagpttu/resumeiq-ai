# ResumeIQ AI Evaluation & Benchmark Suite

This document outlines the evaluation methodology, benchmark dataset, mathematical formulas, and empirical results for **ResumeIQ: Evidence-First AI Resume & Job Matching Engine**.

---

## 1. Evaluation Philosophy

Unlike typical LLM benchmarks that evaluate subjective writing aesthetics, ResumeIQ evaluates **factual fidelity**, **grounded retrieval accuracy**, and **anti-hallucination rigor**.

### Core Evaluation Tenets
1. **Zero Tolerance for Hallucinations:** The engine must never attribute an unevidenced skill or qualification to a candidate.
2. **Explicit Evidence Grounding:** Extracted skills marked as `verified` must be backed by verifiable contextual excerpts from the original resume.
3. **Calibrated Ranking Quality:** Highly aligned candidate profiles must rank higher than pivoted or mismatched profiles.
4. **Adversarial Robustness:** Direct injection attempts, unsupported claims, and keyword stuffing without contextual verbs must be detected and discounted.

---

## 2. Evaluation Metrics & Mathematical Formulations

### 2.1 Skill Extraction Metrics

Let:
- $TP$ (True Positives): Extracted skills that match ground truth required/preferred skills.
- $FP$ (False Positives): Extracted skills that are not relevant or were incorrectly parsed.
- $FN$ (False Negatives): Ground truth skills present in the resume that were omitted by the extractor.

$$\text{Precision} = \frac{TP}{TP + FP}$$

$$\text{Recall} = \frac{TP}{TP + FN}$$

$$\text{F1 Score} = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$$

### 2.2 Ranking Quality: MRR & NDCG

#### Mean Reciprocal Rank (MRR)
Measures the reciprocal rank of the first relevant candidate for a job requisition query:

$$\text{MRR} = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$$

#### Normalized Discounted Cumulative Gain (NDCG@k)
Measures whether candidate scores properly reflect expected compatibility hierarchies across test batches:

$$\text{DCG}_k = \sum_{i=1}^{k} \frac{2^{rel_i} - 1}{\log_2(i + 1)} \quad \text{or} \quad \sum_{i=1}^{k} \frac{\text{score}_i}{\log_2(i + 1)}$$

$$\text{NDCG}_k = \frac{\text{DCG}_k}{\text{IDCG}_k}$$

where $\text{IDCG}_k$ is the Ideal Discounted Cumulative Gain calculated from the monotonically sorted ground truth compatibility scores.

### 2.3 Verification & Anti-Hallucination Metrics

#### Hallucination Rate
The proportion of adversarial test claims regarding unsupported skills that the system erroneously certifies as `supported`:

$$\text{Hallucination Rate} = \frac{N_{\text{erroneously\_supported}}}{N_{\text{unsupported\_tests}}} \times 100\%$$

*Target Threshold: 0.00%*

#### Unsupported Claim Rejection Rate
The proportion of unsupported or fabricated claims correctly classified as `unsupported`, `missing`, or `uncertain`:

$$\text{Rejection Rate} = 100\% - \text{Hallucination Rate}$$

*Target Threshold: 100.00%*

#### Evidence Accuracy
The percentage of `verified` skills that possess substantiated source evidence ($>20$ characters of authentic textual context containing action verbs or metrics):

$$\text{Evidence Accuracy} = \frac{N_{\text{verified with valid excerpt}}}{N_{\text{total verified}}} \times 100\%$$

---

## 3. Evaluation Dataset

The evaluation suite utilizes [`eval_dataset.json`](file:///Users/kasanagotttusathvik/Downloads/AI%20_Resume_Builder/backend/app/tests/evaluation/eval_dataset.json) consisting of realistic, multi-scenario test cases:

### Case 1: `eval_case_1_backend_senior`
- **Candidate:** Senior Backend Engineer (Alex Morgan, 6 YOE, Python, FastAPI, PostgreSQL, AWS, Docker, Redis).
- **Target Job:** Senior Backend Architect (FinTech Global, 5+ YOE, Python, FastAPI/Flask, PostgreSQL, Docker, AWS, Redis).
- **Target Compatibility:** $\ge 80.0\%$ (Tier: High).
- **Adversarial Unsupported Tests:** Kubernetes, GraphQL, Java, Ruby.

### Case 2: `eval_case_2_data_analyst_pivot`
- **Candidate:** Business Intelligence Analyst (Jordan Taylor, 3 YOE, Power BI, DAX, Power Query, PostgreSQL, SQL).
- **Target Job:** Senior BI Specialist (E-Commerce Direct, Power BI, DAX, SQL, Advanced Data Modeling, Tableau, Python).
- **Target Compatibility:** $\approx 60.0\% - 75.0\%$ (Tier: Moderate).
- **Transferable Skill Test:** Tableau (candidate has Power BI $\to$ transferable BI tool).
- **Adversarial Unsupported Tests:** Python, AWS, PyTorch.

### Case 3: `eval_case_3_unaligned_junior`
- **Candidate:** Junior UI Designer (Chris Lee, 1 YOE, B.S. Graphic Design, Figma, Adobe XD, HTML/CSS).
- **Target Job:** Lead ML & Distributed Systems Engineer (7+ YOE, PyTorch, CUDA, C++, LLMs, RAG, Kubernetes, Go).
- **Target Compatibility:** $\le 40.0\%$ (Tier: Low).
- **Critical Gaps:** PyTorch, CUDA, Kubernetes, LLMs, RAG, Go.
- **Adversarial Unsupported Tests:** PyTorch, CUDA, Kubernetes, RAG.

---

## 4. Empirical Benchmark Results

Running the evaluation runner against the complete pipeline yields the following verified metrics:

```
============================================================
RUNNING RESUMEIQ AI PIPELINE EVALUATION BENCHMARK
============================================================
Case [eval_case_1_backend_senior]: Compatibility = 93.6% | Evidence Accuracy = 100.0%
Case [eval_case_2_data_analyst_pivot]: Compatibility = 73.1% | Evidence Accuracy = 100.0%
Case [eval_case_3_unaligned_junior]: Compatibility = 21.4% | Evidence Accuracy = 100.0%

============================================================
EVALUATION RESULTS SUMMARY:
• Precision:                           0.7143
• Recall:                              1.0000
• F1 Score:                            0.8333
• MRR:                                 1.0000
• NDCG:                                0.9342
• Evidence Accuracy:                   100.00%
• Hallucination Rate:                  0.00% (Target: 0.00%)
• Unsupported Claim Rejection Rate:    100.00%
============================================================
```

### Analysis of Results
1. **Recall (1.0000):** Every required skill present in the resume was accurately identified and matched by the multi-signal engine.
2. **Precision (0.7143):** Natural precision reflects the extractor capturing foundational secondary skills (e.g., Linux, JavaScript) alongside strict job requirements.
3. **MRR (1.0000) & NDCG (0.9342):** Candidate ranking cleanly stratified candidates: 93.6% (Case 1) $>$ 73.1% (Case 2) $>$ 21.4% (Case 3).
4. **Hallucination Rate (0.00%):** Out of 11 adversarial unsupported technology claims, zero were falsely classified as supported.
5. **Unsupported Claim Rejection Rate (100.00%):** All fabricated claims were accurately intercepted by the Verification Pipeline.

---

## 5. Running the Evaluation Suite

### Prerequisites
Ensure the virtual environment is activated and dependencies are installed:

```bash
cd backend
source .venv/bin/activate
```

### Run Evaluation Script
```bash
PYTHONPATH=. python app/tests/evaluation/run_evaluation.py
```

### Run Automated Pytest Test Suite
To run all 21 unit, integration, and security tests:
```bash
PYTHONPATH=. pytest app/tests/ -v
```

---

## 6. Continuous Evaluation & Regression Gates

In the automated CI pipeline (`.github/workflows/ci.yml`), PRs and commits are gated against these regression checks:
- Any run where `hallucination_rate > 0.0%` triggers an immediate build failure.
- Any run where `f1_score < 0.75` triggers a quality warning.
- Unit and integration tests must maintain 100% pass rate.
