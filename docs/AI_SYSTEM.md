# RESUMEIQ — AI System Design & Evidence Pipeline

## 1. Core Product Principle

> **"Never optimize a candidate's application by inventing candidate experience."**

In conventional AI career platforms, LLMs frequently fabricate achievements, invent metrics (e.g., claiming "improved performance by 30%" when no percentage exists in the source text), or introduce technologies the candidate has never practiced.

RESUMEIQ enforces a strict evidence grounding layer. Every statement generated or recommended must cite an exact, verifiable snippet from the candidate's actual record.

---

## 2. Evidence Strength Classification

The system categorizes every technical skill or capability claim into five distinct evidence tiers:

```
[ Verified Evidence ] ---> Active project/job sentence with action verbs ('built', 'architected') and/or metrics ('40%')
[ Weak Evidence ]     ---> Listed in a skills section or bullet list without operational context
[ Inferred / Trans. ] ---> Derived from parent skill or transferable affinity matrix (e.g., AWS -> GCP)
[ Missing Evidence ]  ---> Explicitly absent from candidate profile
[ Uncertain ]         ---> Passive or ambiguous mention without clear candidate ownership
```

### Distinction Example
* **Weak Evidence:** `Python` (Listed under Technical Skills: "Python, Java, C++")
* **Verified Evidence:** `"Architected high-throughput REST APIs using FastAPI, Python, and PostgreSQL, handling 40,000 requests/sec with sub-25ms latency."`

---

## 3. Evidence Graph Architecture

The Evidence Graph builds a bidirectional relational lineage:

$$\text{Candidate} \longrightarrow \text{Skill} \longrightarrow \text{Project / Role} \longrightarrow \text{Verbatim Evidence Quote}$$

This answers the fundamental explainability query:
> *"Why does the system believe this candidate has [Skill] experience?"*

When asked about Python:
1. Retrieval locates the candidate skill node for `Python`.
2. Locates associated employment roles (`Senior Software Engineer @ CloudScale AI`).
3. Extracts the exact bullet point: `"Architected high-throughput REST APIs and asynchronous workers using FastAPI, Python, and PostgreSQL..."`
4. Detects action verb: `"Architected"`
5. Detects quantified metric: `"sub-25ms p99 latency"`
6. Computes system confidence: `0.95`
7. Assigns status: `supported`

---

## 4. Anti-Hallucination & Verification Pipeline

Before any generated output (cover letter, recruiter message, interview answer, or bullet rewrite) is returned:

```
Generated Text
      |
      v
Entity Extraction (Detect all technologies & frameworks mentioned)
      |
      v
Evidence Retrieval (Search Candidate Evidence Graph)
      |
      v
Support Check (Is each entity 'verified' or 'weak'?)
      |
      +---> If entity is absent / unsupported:
      |        FLAG & REJECT unverified claim
      |
      +---> If entity is verified:
               GROUND claim with explicit citation and high confidence score
```
