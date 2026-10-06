import re
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class TextChunk:
    chunk_index: int
    content: str
    metadata: Dict[str, Any]

class DocumentChunker:
    @staticmethod
    def chunk_text(
        text: str,
        chunk_size_words: int = 120,
        overlap_words: int = 25,
        base_metadata: Dict[str, Any] = None
    ) -> List[TextChunk]:
        """
        Splits text into overlapping semantic chunks, preserving paragraph and sentence boundaries.
        """
        base_meta = base_metadata or {}
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks: List[TextChunk] = []
        chunk_idx = 0

        current_words: List[str] = []

        for para in paragraphs:
            para_words = para.split()
            if not para_words:
                continue

            if len(current_words) + len(para_words) <= chunk_size_words:
                current_words.extend(para_words)
            else:
                # Flush current words as a chunk
                if current_words:
                    chunks.append(TextChunk(
                        chunk_index=chunk_idx,
                        content=" ".join(current_words),
                        metadata=base_meta.copy()
                    ))
                    chunk_idx += 1
                    # Keep overlap
                    current_words = current_words[-overlap_words:] if len(current_words) > overlap_words else []
                current_words.extend(para_words)

        if current_words:
            chunks.append(TextChunk(
                chunk_index=chunk_idx,
                content=" ".join(current_words),
                metadata=base_meta.copy()
            ))

        return chunks
