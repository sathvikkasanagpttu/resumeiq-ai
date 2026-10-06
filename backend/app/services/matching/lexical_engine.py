import re
import math
from typing import List, Dict, Set
from collections import Counter

class LexicalEngine:
    """
    Computes BM25 and token-level lexical similarity between candidate text and job description.
    """
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

    @staticmethod
    def tokenize(text: str) -> List[str]:
        # Lowercase, alphanumeric tokens, remove common english stop words
        tokens = re.findall(r"\b[a-z0-9+#\.]+\b", text.lower())
        stopwords = {
            "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
            "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but",
            "by", "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from",
            "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him",
            "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just",
            "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once",
            "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same",
            "she", "should", "so", "some", "such", "than", "that", "the", "their", "theirs", "them",
            "themselves", "then", "there", "these", "they", "this", "those", "through", "to", "too",
            "under", "until", "up", "very", "was", "we", "were", "what", "when", "where", "which",
            "while", "who", "whom", "why", "with", "would", "you", "your", "yours", "yourself"
        }
        return [t for t in tokens if t not in stopwords and len(t) > 1]

    def compute_bm25_similarity(self, query_text: str, doc_text: str) -> float:
        """
        Calculates normalized BM25 score (0.0 to 100.0) between query (job requirements) and doc (resume).
        """
        query_tokens = self.tokenize(query_text)
        doc_tokens = self.tokenize(doc_text)
        
        if not query_tokens or not doc_tokens:
            return 0.0

        doc_len = len(doc_tokens)
        avg_doc_len = max(doc_len, 250)  # normalized baseline doc length
        doc_freqs = Counter(doc_tokens)
        query_freqs = Counter(query_tokens)

        score = 0.0
        max_possible = 0.0

        for term, q_tf in query_freqs.items():
            tf = doc_freqs.get(term, 0)
            # IDF approximation for single-pair comparison
            idf = math.log(1.0 + (100.0 / (1.0 + (1.0 if tf > 0 else 0.0))))
            
            # BM25 term score
            numerator = tf * (self.k1 + 1.0)
            denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / avg_doc_len))
            term_score = idf * (numerator / max(denominator, 1e-6))
            score += term_score

            # Optimal term score if query term was richly matched
            opt_num = 3.0 * (self.k1 + 1.0)
            opt_den = 3.0 + self.k1 * (1.0 - self.b + self.b)
            max_possible += idf * (opt_num / opt_den)

        if max_possible == 0.0:
            return 0.0
            
        normalized = min(100.0, max(0.0, (score / max_possible) * 100.0))
        return round(normalized, 2)

    def compute_jaccard_similarity(self, text_a: str, text_b: str) -> float:
        tokens_a = set(self.tokenize(text_a))
        tokens_b = set(self.tokenize(text_b))
        if not tokens_a or not tokens_b:
            return 0.0
        intersection = tokens_a.intersection(tokens_b)
        union = tokens_a.union(tokens_b)
        return round((len(intersection) / len(union)) * 100.0, 2)

lexical_engine = LexicalEngine()
