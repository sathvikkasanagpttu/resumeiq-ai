# RESUMEIQ — Retrieval-Augmented Generation (RAG) Architecture

## 1. Overview

The RESUMEIQ RAG engine grounds AI reasoning, gap recommendations, and resume rewriting in an authoritative knowledge corpus. Candidate PII is never sent indiscriminately to vector databases; instead, only sanitized requirement scopes and general principles are retrieved.

---

## 2. RAG Pipeline Architecture

```
Knowledge Documents (Markdown & Standards)
      |
      v
Semantic Chunking (100 words, 20-word overlap)
      |
      v
Dense Embeddings (text-embedding-004 + Fallback Projector)
      |
      v
Hybrid Storage (Postgres pgvector / In-Memory Vector Store)
      |
      +-----------------------------------------+
      |                                         |
      v                                         v
Dense Semantic Search                     BM25 Lexical Search
(Cosine Distance)                         (Term Frequency / IDF)
      |                                         |
      +-------------------+---------------------+
                          |
                          v
            Reciprocal Rank Fusion (RRF)
                          |
                          v
                  Context Assembly
                          |
                          v
             Structured LLM Prompt Wrapper
```

---

## 3. Reciprocal Rank Fusion (RRF) Formulation

To eliminate bias from disparate scoring scales between dense cosine similarity and BM25, RESUMEIQ combines ranks using Reciprocal Rank Fusion:

$$\text{RRF\_Score}(d) = \frac{1}{k + \text{rank}_{\text{dense}}(d)} + \frac{1}{k + \text{rank}_{\text{BM25}}(d)}$$

Where $k = 60$ is the standard smoothing parameter. The top $K$ chunks are formatted into structured context blocks and injected into prompt boundaries.
