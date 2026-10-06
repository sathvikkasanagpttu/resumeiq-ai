import pytest
from app.services.rag.chunker import DocumentChunker
from app.services.rag.retriever import rag_retriever

def test_document_chunker():
    sample_text = """
Paragraph 1 discusses backend architecture, FastAPI, and PostgreSQL. It contains various details on system throughput and design principles.

Paragraph 2 focuses on Redis caching, distributed task queues, and asynchronous jobs. It highlights the benefits of offloading long-running jobs.

Paragraph 3 explores cloud deployments, AWS EC2, and Docker containerization standards.
"""
    chunks = DocumentChunker.chunk_text(sample_text, chunk_size_words=20, overlap_words=5)
    assert len(chunks) >= 2
    for c in chunks:
        assert len(c.content.split()) > 0

def test_hybrid_rag_search():
    # Query for backend or caching
    results = rag_retriever.hybrid_search("FastAPI PostgreSQL database", top_k=3)
    assert len(results) > 0
    assert "content" in results[0]
    assert results[0]["score"] > 0.0

def test_rag_context_builder():
    context = rag_retriever.build_context("cover letter application guidelines", category="application_guidance")
    assert "KNOWLEDGE SOURCE" in context
    assert len(context) > 50
