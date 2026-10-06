# Contributing to ResumeIQ

Thank you for your interest in contributing to **ResumeIQ: Evidence-First AI Resume & Job Matching Engine**! We welcome contributions that uphold our core mission of creating transparent, evidence-grounded career intelligence.

---

## 1. Prime Directive

> **"Never optimize a candidate's application by inventing candidate experience."**

Every pull request, algorithm addition, prompt modification, or feature must strictly uphold this rule:
- Do not fabricate skills, employment periods, metrics, or technologies.
- Do not add ungrounded claims into cover letters or resume optimization suggestions.
- If evidence is absent, the system must report a gap or mark the claim as missing/uncertain.

---

## 2. Development Workflow

### 2.1 Branching Convention
- `feature/<feature-name>`: New capabilities (e.g., `feature/custom-ontology-importer`).
- `fix/<bug-name>`: Bug fixes (e.g., `fix/pdf-two-column-parsing`).
- `docs/<doc-name>`: Documentation improvements.

### 2.2 Code Quality Standards

#### Python / Backend
- **Format & Style:** Follow PEP 8 guidelines.
- **Type Annotations:** All functions and methods must have full type annotations (`typing` and Pydantic models).
- **Validation:** Always use Pydantic schemas for request and response serialization.
- **Database:** All schema changes must be accompanied by an Alembic migration script.
- **Error Handling:** Use custom domain exceptions derived from `ResumeIQException` rather than generic `HTTPException`.

#### TypeScript / Frontend
- **Format & Style:** Clean React 18 functional components with hooks.
- **Styling:** Use Tailwind CSS utility classes; avoid inline styles.
- **Type Safety:** Maintain strict TypeScript compliance; avoid `any`.
- **Accessibility:** All modals, buttons, and interactive elements must have accessible labels and keyboard focus states.

---

## 3. Testing & Verification Checklist

Before submitting a Pull Request, you must verify that all automated quality checks pass:

### 1. Run Python Unit and Integration Tests
```bash
cd backend
source .venv/bin/activate
PYTHONPATH=. pytest app/tests/ -v
```
*Requirement: All 21+ tests must pass.*

### 2. Run the AI Anti-Hallucination Evaluation Benchmark
```bash
cd backend
source .venv/bin/activate
PYTHONPATH=. python app/tests/evaluation/run_evaluation.py
```
*Requirement: Hallucination Rate must be exactly 0.00% and Unsupported Claim Rejection Rate must be 100.00%.*

### 3. Verify Frontend TypeScript Compilation & Build
```bash
cd frontend
npm run build
```
*Requirement: Zero TypeScript errors or warnings during the production Vite build.*

---

## 4. Submitting a Pull Request

1. Fork the repository and create your branch from `main`.
2. Ensure commit messages are descriptive (e.g., `feat(matching): add configurable education alignment weight`).
3. Include relevant test cases for any new parser, matcher, or service logic.
4. Open a Pull Request referencing any related issues.
5. Provide a summary of changes and attach test execution output.

Thank you for helping build an ethical, evidence-grounded AI career intelligence engine!
