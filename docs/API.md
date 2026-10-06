# ResumeIQ API Specification (v1)

ResumeIQ exposes a versioned, RESTful API under the `/api/v1` namespace. Interactive documentation is available out of the box via Swagger UI at `http://localhost:8000/docs` and ReDoc at `http://localhost:8000/redoc`.

---

## 1. Global API Standards

### Headers & Observability
Every request returns the following tracking headers:
- `X-Request-ID`: Unique UUID assigned to the request lifecycle.
- `X-Response-Time-MS`: Processing latency in milliseconds.

### Error Handling Schema
All errors conform to a consistent JSON structure:
```json
{
  "error_code": "NOT_FOUND",
  "detail": "Resume with ID 42 not found.",
  "extra": {},
  "request_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
}
```

### Authentication
Endpoints marked with 🔒 require an `Authorization: Bearer <JWT>` header obtained via the login endpoint.

---

## 2. Authentication Endpoints (`/api/v1/auth`)

### `POST /api/v1/auth/register`
Create a new user account.
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "full_name": "Jane Doe",
    "role": "candidate"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "id": 1,
    "email": "user@example.com",
    "full_name": "Jane Doe",
    "role": "candidate",
    "is_active": true
  }
  ```

### `POST /api/v1/auth/login`
Authenticate with OAuth2 password grant to retrieve a JWT bearer token.
- **Request Body:** `application/x-www-form-urlencoded`
  - `username`: Email address
  - `password`: Password
- **Response (200 OK):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1Ni...",
    "token_type": "bearer"
  }
  ```

### `GET /api/v1/auth/me` 🔒
Retrieve the authenticated user's profile.

---

## 3. Resume Intelligence (`/api/v1/resumes`)

### `POST /api/v1/resumes/upload` 🔒
Upload and parse a resume document (`.pdf`, `.docx`, or `.txt`).
- **Request:** `multipart/form-data`
  - `file`: Binary document file
- **Response (200 OK):**
  ```json
  {
    "id": 1,
    "filename": "sarah_chen_resume.pdf",
    "file_type": "pdf",
    "created_at": "2026-10-07T00:00:00Z",
    "summary": "Senior Backend & AI Systems Engineer with 6+ years...",
    "skills": [
      {
        "id": 1,
        "original_text": "Built a FastAPI microservice",
        "normalized_skill": "FastAPI",
        "category": "framework",
        "confidence": 0.95,
        "evidence_strength": "verified",
        "source_section": "experience",
        "source_evidence": "Built a high-throughput microservices architecture with FastAPI and PostgreSQL handling 20,000 req/sec"
      }
    ],
    "experiences": [ ... ],
    "educations": [ ... ],
    "projects": [ ... ]
  }
  ```

### `GET /api/v1/resumes/` 🔒
List all resumes owned by the current user.

### `GET /api/v1/resumes/{resume_id}` 🔒
Retrieve full extracted structured profile for a specific resume.

### `DELETE /api/v1/resumes/{resume_id}` 🔒
Delete a resume and all associated skills, experiences, and evidence nodes.

---

## 4. Job Intelligence (`/api/v1/jobs`)

### `POST /api/v1/jobs/` 🔒
Parse, structure, and save a job description.
- **Request Body:**
  ```json
  {
    "title": "Senior AI Systems Architect",
    "company": "DeepTech Innovations",
    "description": "We are seeking a Senior AI Systems Architect with 5+ years of experience...",
    "location": "San Francisco, CA",
    "work_model": "hybrid"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "id": 1,
    "title": "Senior AI Systems Architect",
    "company": "DeepTech Innovations",
    "seniority_level": "Senior",
    "requirements": [
      {
        "id": 1,
        "requirement_type": "REQUIRED",
        "category": "technical_skill",
        "skill_name": "FastAPI",
        "text": "Production experience building backends with FastAPI",
        "importance_weight": 0.95
      }
    ]
  }
  ```

### `GET /api/v1/jobs/` 🔒
List all analyzed jobs.

### `GET /api/v1/jobs/{job_id}` 🔒
Retrieve structured requirements, responsibilities, and metadata for a job.

---

## 5. Hybrid Matching Engine (`/api/v1/matching`)

### `POST /api/v1/matching/calculate` 🔒
Calculate a multi-signal Candidate–Job Compatibility Score.
- **Request Body:**
  ```json
  {
    "resume_id": 1,
    "job_id": 1,
    "weights": {
      "semantic_fit": 0.25,
      "required_skills": 0.30,
      "preferred_skills": 0.10,
      "evidence_strength": 0.15,
      "experience_alignment": 0.10,
      "domain_fit": 0.05,
      "education_fit": 0.05
    }
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "id": 1,
    "resume_id": 1,
    "job_id": 1,
    "compatibility_score": 91.4,
    "tier": "Strong Match",
    "component_scores": {
      "semantic_fit": 94.2,
      "required_skill_coverage": 100.0,
      "preferred_skill_coverage": 80.0,
      "evidence_strength": 92.0,
      "experience_alignment": 100.0,
      "domain_fit": 85.0,
      "education_fit": 100.0
    },
    "score_explanation": "Strong candidate match driven by high required skill coverage and verified evidence...",
    "matched_skills": [ ... ]
  }
  ```

### `GET /api/v1/matching/{match_id}` 🔒
Retrieve a previously calculated match assessment.

---

## 6. Evidence Graph & Verification (`/api/v1/evidence`)

### `GET /api/v1/evidence/graph/{resume_id}` 🔒
Retrieve the complete candidate knowledge graph (`nodes` and `links`).
- **Response Structure:**
  ```json
  {
    "resume_id": 1,
    "nodes": [
      { "id": "candidate_1", "name": "Sarah Chen", "type": "candidate", "category": "Candidate", "strength": "verified" },
      { "id": "skill_FastAPI", "name": "FastAPI", "type": "skill", "category": "Framework", "strength": "verified" }
    ],
    "links": [
      { "source": "candidate_1", "target": "skill_FastAPI", "relationship": "demonstrates" }
    ]
  }
  ```

### `POST /api/v1/evidence/verify-claim` 🔒
Submit an arbitrary statement to the AI Verification Pipeline to test grounding.
- **Request Body:**
  ```json
  {
    "resume_id": 1,
    "claim_text": "Candidate has 5 years of production Kubernetes cluster administration experience",
    "target_entity": "Kubernetes"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "claim": "Candidate has 5 years of production Kubernetes cluster administration experience",
    "status": "unsupported",
    "confidence": 0.15,
    "evidence_strength": 0.0,
    "supporting_evidence": null,
    "explanation": "No evidence found in candidate resume supporting Kubernetes."
  }
  ```

---

## 7. Skill Gap Engine (`/api/v1/gaps`)

### `GET /api/v1/gaps/{match_id}` 🔒
Identify critical, moderate, minor, transferable, and representation gaps.
- **Response (200 OK):**
  ```json
  {
    "match_id": 1,
    "critical_gaps": [],
    "moderate_gaps": [
      {
        "skill": "AWS",
        "severity": "moderate",
        "job_requirement": "Preferred cloud experience with AWS",
        "candidate_evidence": "Candidate lists general cloud deployments but lacks AWS specifics",
        "explanation": "Preferred skill missing from active project descriptions",
        "recommendation": "Build a sample deployment project using AWS ECS or Lambda"
      }
    ],
    "transferable_skills": [ ... ],
    "representation_gaps": [ ... ]
  }
  ```

---

## 8. Resume Optimization (`/api/v1/optimization`)

### `POST /api/v1/optimization/optimize` 🔒
Generate evidence-grounded resume improvement recommendations (XYZ formula).
- **Request Body:**
  ```json
  {
    "resume_id": 1,
    "job_id": 1
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "resume_id": 1,
    "job_id": 1,
    "suggestions": [
      {
        "section": "experience",
        "original_text": "Managed backend APIs for web services.",
        "recommended_text": "Architected high-throughput FastAPI and PostgreSQL REST endpoints handling 20k req/sec, reducing latency by 45%.",
        "grounded_evidence": "Verbatim candidate metric: 20k req/sec, 45% latency reduction.",
        "rationale": "Incorporates quantifiable metric and target framework to align with job description.",
        "confidence": 0.95
      }
    ]
  }
  ```

---

## 9. Application Generator (`/api/v1/applications`)

### `POST /api/v1/applications/generate` 🔒
Generate an evidence-grounded cover letter, recruiter outreach message, and interview Q&A.
- **Request Body:**
  ```json
  {
    "resume_id": 1,
    "job_id": 1,
    "material_type": "cover_letter"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "material_type": "cover_letter",
    "generated_content": "Dear Hiring Manager,\n\nI am writing to express my strong interest...",
    "cited_evidence": [
      {
        "claim": "Built distributed services handling 20,000 req/sec",
        "source_evidence": "Senior Software Engineer at FinScale Tech"
      }
    ],
    "verification_status": "supported",
    "confidence": 0.98
  }
  ```

---

## 10. Career Roadmaps & Recommendations (`/api/v1/career`)

### `GET /api/v1/career/roadmap/{match_id}` 🔒
Generate a prioritized, step-by-step learning roadmap for identified gaps.

### `GET /api/v1/career/recommendations/{resume_id}` 🔒
Get ranked job recommendations based on candidate evidence profile.

---

## 11. Market Analytics (`/api/v1/analytics`)

### `GET /api/v1/analytics/overview` 🔒
Retrieve aggregated labor market intelligence: top required skills, salary benchmarks, and demand trends.

---

## 12. RAG Knowledge Base (`/api/v1/rag`)

### `POST /api/v1/rag/search`
Query the hybrid RAG index (Dense embeddings + Lexical BM25 + RRF) for career knowledge.
- **Request Body:**
  ```json
  {
    "query": "What is the Google XYZ resume bullet formula?",
    "top_k": 3
  }
  ```

---

## 13. Health & Observability

### `GET /api/v1/health`
Health check endpoint reporting database, vector index, and pipeline status.
- **Response (200 OK):**
  ```json
  {
    "status": "healthy",
    "timestamp": "2026-10-07T00:00:00Z",
    "database": "connected",
    "vector_store": "ready",
    "version": "1.0.0"
  }
  ```

### `GET /api/v1/metrics`
Basic runtime metrics for monitoring and alerting.
