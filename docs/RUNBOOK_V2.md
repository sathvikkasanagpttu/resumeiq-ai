# RESUMEIQ v2: Operational Runbook
## Setup, Execution, Evaluation Benchmark & Deployment Guide

---

### 1. Prerequisites & Environment Setup

#### Python Environment (Backend)
- Python 3.10+ (tested on Python 3.12 / 3.14)
- PostgreSQL (or local SQLite fallback `resumeiq.db` for rapid offline dev)
- Redis 6+ (for background Celery workers and caching)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### Node.js Environment (Frontend)
- Node.js 18+
- npm 9+

```bash
cd frontend
npm install
```

---

### 2. Running Services Locally

#### 2.1 Backend Server (FastAPI)
```bash
cd backend
source .venv/bin/activate
# Start development server on port 8000
PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- API Base URL: `http://localhost:8000/api/v1`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/v1/health`

#### 2.2 Frontend Studio (React + Vite)
```bash
cd frontend
npm run dev
```
- Web Application: `http://localhost:5173`
- Previews the full suite including **Resume Studio v2**, **Application Tracker**, and **Interview Prep STAR Engine**.

#### 2.3 Docker Compose (All Services)
```bash
# Start backend, frontend, PostgreSQL, and Redis in isolated containers
docker compose up -d --build
```

---

### 3. Automated Test Suite Execution

RESUMEIQ v2 maintains a 100% passing test suite across all parser, generator, verification, and API components.

```bash
cd backend
source .venv/bin/activate
PYTHONPATH=. pytest app/tests/ -v
```

Expected output:
```
============================== 33 passed in 2.36s ==============================
```

---

### 4. Running the 30-Case v2 Evaluation Benchmark

The v2 evaluation benchmark runs against a diverse test dataset of 30 distinct technical personas (Junior Frontend, Senior Distributed Systems Architect, Data Scientist, ML Engineer, DevOps/SRE, Product Manager, Security Engineer, Fresher, Career Switcher, Executive, etc.).

```bash
cd backend
source .venv/bin/activate
python scripts/run_v2_eval.py
```

#### CI Quality Gates & Pass Thresholds

| Metric | Measured Value | CI Gate Requirement | Status |
| :--- | :---: | :---: | :---: |
| **Extraction Accuracy** | **100.00%** | $\ge 90.00\%$ | **PASS** |
| **Verification Precision** | **100.00%** | $\ge 95.00\%$ | **PASS** |
| **Hallucination Rate** | **0.00%** | $\mathbf{0.00\%}$ | **PASS** |
| **ATS Round-Trip Success** | **100.00%** | $\ge 95.00\%$ | **PASS** |
| **End-to-End Latency (p50)** | **0.02s** | $\le 3.00\text{s}$ | **PASS** |
| **End-to-End Latency (p95)** | **0.05s** | $\le 8.00\text{s}$ | **PASS** |

---

### 5. API Verification via cURL

#### 5.1 Generate an Auto-Built Resume Version
```bash
curl -X POST "http://localhost:8000/api/v1/builder/generate" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "REPLACE_WITH_RESUME_UUID",
    "mode": "clean_rebuild",
    "template_id": "modern_minimal",
    "page_target": 1
  }'
```

#### 5.2 Review a Bullet Diff
```bash
curl -X POST "http://localhost:8000/api/v1/builder/diff/review" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "diff_id": "REPLACE_WITH_DIFF_UUID",
    "action": "accept"
  }'
```

#### 5.3 Export Formats (PDF, DOCX, TXT, JSON, HTML)
```bash
# Standard ATS-Safe PDF
curl -O -J "http://localhost:8000/api/v1/builder/export/<VERSION_ID>?format=pdf" \
  -H "Authorization: Bearer <YOUR_TOKEN>"

# Blind Screening Redacted PDF
curl -O -J "http://localhost:8000/api/v1/builder/export/<VERSION_ID>?format=pdf&redact_pii=true" \
  -H "Authorization: Bearer <YOUR_TOKEN>"

# DOCX Format
curl -O -J "http://localhost:8000/api/v1/builder/export/<VERSION_ID>?format=docx" \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

#### 5.4 Run Quality & Gap Audit
```bash
curl -X GET "http://localhost:8000/api/v1/builder/quality/<RESUME_ID>" \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

#### 5.5 Synthesize Interview Prep STAR Questions
```bash
curl -X POST "http://localhost:8000/api/v1/builder/interview-prep" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "REPLACE_WITH_RESUME_UUID",
    "target_role": "Staff Backend Engineer"
  }'
```

---

### 6. Production Deployment Notes

1. **Environment Variables**:
   - `DATABASE_URL`: Production PostgreSQL connection string (with connection pooling, e.g. PgBouncer).
   - `REDIS_URL`: Production Redis URL for distributed task queue and caching.
   - `SECRET_KEY`: High-entropy 256-bit secret string for JWT authentication.
   - `ALLOW_AI_SUGGESTIONS_PENDING_RENDER`: Kept strictly `False` to maintain the core zero-hallucination principle.

2. **Frontend Production Build**:
   ```bash
   cd frontend
   npm run build
   # Outputs optimized static bundle into dist/
   ```

3. **Circuit Breakers & Privacy Safeguards**:
   - All AI calls enforce a fallback circuit breaker: if an LLM generates unverifiable content, the bullet rewriter automatically falls back to deterministic AST extraction.
   - PII redaction eliminates names, phone numbers, personal email handles, and physical addresses during export when `redact_pii=True` is requested.
