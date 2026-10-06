from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.services.rag.knowledge_base import SEED_KNOWLEDGE_DOCUMENTS
from app.services.rag.chunker import DocumentChunker, TextChunk
from app.services.matching.semantic_engine import semantic_engine
from app.services.matching.lexical_engine import lexical_engine
from app.models.rag import KnowledgeDocument, KnowledgeChunk
from app.core.logging import logger

class HybridRAGRetriever:
    """
    Hybrid RAG Retrieval Engine:
    Combines dense embedding retrieval + BM25 lexical search with Reciprocal Rank Fusion (RRF).
    Supports metadata filtering and clean context synthesis.
    """
    def __init__(self):
        self.in_memory_chunks: List[Dict[str, Any]] = []
        self._initialize_seed_knowledge()

    def _initialize_seed_knowledge(self):
        """
        Seeds knowledge chunks and precomputes dense vectors in memory.
        """
        for doc in SEED_KNOWLEDGE_DOCUMENTS:
            chunks = DocumentChunker.chunk_text(
                text=doc["content"],
                chunk_size_words=100,
                overlap_words=20,
                base_metadata={"title": doc["title"], "category": doc["category"]}
            )
            for c in chunks:
                emb = semantic_engine.get_embedding(c.content)
                self.in_memory_chunks.append({
                    "content": c.content,
                    "title": doc["title"],
                    "category": doc["category"],
                    "embedding": emb,
                    "metadata": c.metadata
                })
        logger.info(f"Hybrid RAG Retriever initialized with {len(self.in_memory_chunks)} knowledge chunks.")

    def sync_to_db(self, db: Session):
        """
        Synchronizes seed documents to database if not present.
        """
        existing_count = db.query(KnowledgeDocument).count()
        if existing_count > 0:
            return

        for doc_data in SEED_KNOWLEDGE_DOCUMENTS:
            db_doc = KnowledgeDocument(
                title=doc_data["title"],
                category=doc_data["category"],
                content=doc_data["content"].strip(),
                metadata_info=doc_data.get("metadata", {})
            )
            db.add(db_doc)
            db.flush()

            chunks = DocumentChunker.chunk_text(
                text=doc_data["content"],
                base_metadata={"category": doc_data["category"]}
            )
            for ch in chunks:
                emb = semantic_engine.get_embedding(ch.content)
                db_chunk = KnowledgeChunk(
                    document_id=db_doc.id,
                    chunk_index=ch.chunk_index,
                    content=ch.content,
                    embedding=emb,
                    metadata_info=ch.metadata
                )
                db.add(db_chunk)
        db.commit()

    def hybrid_search(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Performs dense vector retrieval + BM25 lexical ranking + Reciprocal Rank Fusion (RRF).
        """
        if not self.in_memory_chunks:
            return []

        filtered_chunks = self.in_memory_chunks
        if category:
            filtered_chunks = [c for c in self.in_memory_chunks if c["category"] == category]
            if not filtered_chunks:
                filtered_chunks = self.in_memory_chunks

        # 1. Dense Vector Scoring
        query_emb = semantic_engine.get_embedding(query)
        dense_ranked = []
        for idx, chunk in enumerate(filtered_chunks):
            sim = semantic_engine.cosine_similarity(query_emb, chunk["embedding"])
            dense_ranked.append((idx, sim))
        dense_ranked.sort(key=lambda x: x[1], reverse=True)

        # 2. BM25 Lexical Scoring
        lexical_ranked = []
        for idx, chunk in enumerate(filtered_chunks):
            bm25 = lexical_engine.compute_bm25_similarity(query, chunk["content"])
            lexical_ranked.append((idx, bm25))
        lexical_ranked.sort(key=lambda x: x[1], reverse=True)

        # 3. Reciprocal Rank Fusion (RRF)
        # RRF_Score = 1 / (60 + rank_dense) + 1 / (60 + rank_lexical)
        k_const = 60
        rrf_scores: Dict[int, float] = {idx: 0.0 for idx in range(len(filtered_chunks))}

        for rank, (idx, _) in enumerate(dense_ranked):
            rrf_scores[idx] += 1.0 / (k_const + rank + 1)

        for rank, (idx, _) in enumerate(lexical_ranked):
            rrf_scores[idx] += 1.0 / (k_const + rank + 1)

        sorted_indices = sorted(rrf_scores.keys(), key=lambda i: rrf_scores[i], reverse=True)

        results = []
        for idx in sorted_indices[:top_k]:
            chunk = filtered_chunks[idx]
            results.append({
                "title": chunk["title"],
                "category": chunk["category"],
                "content": chunk["content"],
                "score": round(rrf_scores[idx] * 100, 3)
            })

        return results

    def build_context(self, query: str, category: Optional[str] = None, top_k: int = 3) -> str:
        """
        Constructs clean context string from top retrieved chunks.
        """
        results = self.hybrid_search(query, category=category, top_k=top_k)
        if not results:
            return ""
        
        context_parts = []
        for i, r in enumerate(results):
            context_parts.append(f"--- KNOWLEDGE SOURCE [{i+1}: {r['title']}] ---\n{r['content']}")
        return "\n\n".join(context_parts)

rag_retriever = HybridRAGRetriever()
