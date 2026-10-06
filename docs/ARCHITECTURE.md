# RESUMEIQ — System Architecture

## 1. Architectural Overview

RESUMEIQ is engineered following a clean, decoupled service architecture designed for high availability, deterministic verification, and strict evidence grounding. Unlike conventional keyword ATS tools or naive LLM wrappers, RESUMEIQ establishes a formal mathematical and relational boundary between **candidate facts** and **job description demands**.

```
+-----------------------------------------------------------------------------------------+
|                                    USER INTERFACE                                       |
|  React 18 + TypeScript + Tailwind CSS (Vite SPA)                                        |
|  - Dashboard                      - Resume Intelligence        - Job Analyzer           |
|  - Match Analysis (8 Signals)     - Skill Gap Diagnostics      - Resume Optimizer       |
|  - Application Generator          - Career Roadmap             - Market Analytics       |
+-----------------------------------------------------------------------------------------+
                                          | REST API (JSON)
                                          v
+-----------------------------------------------------------------------------------------+
|                                   BACKEND SERVICES                                      |
|  FastAPI (Python 3.12/3.14)                                                             |
|  - Security & JWT Auth            - Section & Entity Extraction - Skill Ontology         |
|  - Hybrid Matching Engine         - Evidence Graph Lineage     - Anti-Hallucination V1   |
|  - RAG Hybrid Retriever           - Structured LLM Client      - Task Queue Worker      |
+-----------------------------------------------------------------------------------------+
          |                                  |                                |
          v                                  v                                v
+----------------------+           +-------------------+            +---------------------+
|      DATABASE        |           |   RAG KNOWLEDGE   |            |   AI & EMBEDDINGS   |
| PostgreSQL / SQLite  |           | Curated Taxonomy  |            | Google GenAI        |
| 20+ Normalized       |           | Hybrid BM25 +     |            | (text-embedding-004)|
| Relational Tables    |           | Dense Retrieval   |            | Dense Fallback      |
+----------------------+           +-------------------+            +---------------------+
```

---

## 2. Component Decoupling & Principles

### A. Separation of Extraction and Judgment
The ingestion pipelines (`ResumePipeline` and `JobPipeline`) extract and structure raw text into normalized database entities without scoring or judgment. This ensures that changes to scoring weights or models do not invalidate candidate profile facts.

### B. Anti-Fabrication Boundary
All generated documents (cover letters, recruiter messages, bullet rewrites) pass through `VerificationPipeline`. If an LLM or heuristic mentions a technology, metric, or title that does not have supporting evidence in the candidate profile, the claim is rejected or flagged as `unsupported`.

### C. Multi-Signal Matching Over Single Prompt
Instead of passing the entire resume and job description to an LLM prompt (which suffers from attention dilution, position bias, and non-deterministic scoring), RESUMEIQ calculates 8 component signals deterministically:
1. Lexical Similarity (BM25)
2. Semantic Embedding Cosine Similarity
3. Required Skill Coverage
4. Preferred Skill Coverage
5. Evidence Strength
6. Experience Alignment
7. Seniority Alignment
8. Domain Alignment

---

## 3. Database Schema Overview

The database contains over 20 normalized tables across 7 domain modules:

| Table | Purpose |
|---|---|
| `users` | User credentials, roles, and authorization |
| `candidate_profiles` | Headline, career years, seniority, and target titles |
| `resumes` | Uploaded raw text, metadata, and active state |
| `resume_sections` | Header, summary, experience, education, skills boundaries |
| `candidate_skills` | Normalized skills with evidence strength (`verified`, `weak`, etc.) |
| `candidate_experience` | Verified employment history, duration, bullets, and technologies |
| `candidate_projects` | Project title, outcomes, repository URL, technologies |
| `candidate_education` | Degrees, institutions, graduation dates, and GPA |
| `candidate_certifications` | Professional credentials and issuing organizations |
| `evidence_items` | Relational bridge: exact resume quotes, action verbs, metrics |
| `jobs` | Target job title, company, work model, seniority, experience range |
| `job_requirements` | Requirements classified as REQUIRED, PREFERRED, RESPONSIBILITY, etc. |
| `job_skills` | Normalized target skills with importance weights |
| `matches` | Candidate-Job Compatibility Score (0-100) and calculation snapshot |
| `match_components` | Component-level breakdown, weights, and explanations |
| `skill_gaps` | Severity-graded gaps (critical, moderate, minor, transferable, representation) |
| `recommendations` | Evidence-grounded action items |
| `generated_documents` | Cover letters, outreach, and Q&A with cited evidence quotes |
| `knowledge_documents` | RAG corpus documents across standards, engineering, and roles |
| `knowledge_chunks` | Dense-vectorized semantic chunks for hybrid search |
| `audit_logs` | Security and action logging |
| `background_tasks` | Async task status and progress lifecycle |
