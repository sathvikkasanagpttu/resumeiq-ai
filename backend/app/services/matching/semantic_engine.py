import hashlib
import numpy as np
from typing import List, Optional
from app.core.config import settings
from app.core.logging import logger

def _stable_hash(s: str) -> int:
    """Deterministic, process-independent 32-bit hash using SHA-256."""
    return int.from_bytes(hashlib.sha256(s.encode("utf-8")).digest()[:4], "big")

class SemanticEngine:
    """
    Computes dense semantic embeddings and cosine similarity.
    Uses Google GenAI embeddings when an API key is available,
    with an internal deterministic semantic feature vector fallback.
    """
    def __init__(self):
        self._client = None
        if settings.GEMINI_API_KEY:
            try:
                from google import genai
                self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
            except Exception as e:
                logger.warning(f"Failed to initialize Google GenAI Client: {e}. Using dense fallback.")

    def get_embedding(self, text: str) -> List[float]:
        cleaned = text.strip()
        if not cleaned:
            return [0.0] * 128

        if self._client:
            try:
                response = self._client.models.embed_content(
                    model=settings.EMBEDDING_MODEL,
                    contents=cleaned[:2000]
                )
                # Handle current google-genai response shape (response.embeddings[0].values)
                if response:
                    if hasattr(response, "embeddings") and response.embeddings:
                        first = response.embeddings[0]
                        if hasattr(first, "values") and first.values:
                            return list(first.values)
                    if hasattr(response, "embedding") and response.embedding:
                        if hasattr(response.embedding, "values") and response.embedding.values:
                            return list(response.embedding.values)
            except Exception as e:
                logger.warning(f"GenAI embedding call failed: {e}. Falling back to internal dense projector.")

        return self._generate_dense_fallback_embedding(cleaned)

    @staticmethod
    def _generate_dense_fallback_embedding(text: str, dim: int = 128) -> List[float]:
        """
        Deterministic, dense feature vector representation using sub-word n-gram hashing
        via process-stable SHA-256 (replaces randomized Python hash()).
        """
        vec = np.zeros(dim, dtype=np.float32)
        words = text.lower().split()
        if not words:
            return vec.tolist()

        for idx, word in enumerate(words):
            # Positional weight
            pos_weight = 1.0 / (1.0 + 0.005 * idx)
            # Hash word and character n-grams deterministically
            w_hash = _stable_hash(word) % dim
            vec[w_hash] += 1.0 * pos_weight

            # Character tri-grams
            if len(word) >= 3:
                for c_i in range(len(word) - 2):
                    trigram = word[c_i:c_i+3]
                    t_hash = _stable_hash(trigram) % dim
                    vec[t_hash] += 0.35 * pos_weight

        norm = np.linalg.norm(vec)
        if norm > 1e-6:
            vec = vec / norm
        return vec.tolist()

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        if not vec_a or not vec_b:
            return 0.0
        
        # Enforce dimension consistency: refuse to compare mismatched dimensions
        if len(vec_a) != len(vec_b):
            raise ValueError(
                f"Mismatched vector dimensions: {len(vec_a)} vs {len(vec_b)}. "
                "Refusing to compare embeddings generated from different models."
            )

        a = np.array(vec_a, dtype=np.float32)
        b = np.array(vec_b, dtype=np.float32)
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a < 1e-6 or norm_b < 1e-6:
            return 0.0
        sim = float(dot / (norm_a * norm_b))
        # Bound to 0.0 - 1.0 and scale to 0 - 100
        normalized = max(0.0, min(1.0, sim)) * 100.0
        return round(normalized, 2)

    def compute_semantic_similarity(self, text_a: str, text_b: str) -> float:
        emb_a = self.get_embedding(text_a)
        emb_b = self.get_embedding(text_b)
        return self.cosine_similarity(emb_a, emb_b)


semantic_engine = SemanticEngine()
