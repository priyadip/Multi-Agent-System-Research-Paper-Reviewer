"""
PaperRAG - a per-paper retrieval store.

Chunks the whole paper (all pages), builds a semantic embedding index, and
retrieves the most relevant chunks for a query. Falls back to lexical TF-IDF
if sentence-transformers is unavailable, so the app never breaks.
"""

import re
from typing import List, Callable, Optional
import numpy as np


class PaperRAG:
    """In-memory retrieval store for a single paper."""

    def __init__(self, embed_fn: Optional[Callable[[List[str]], np.ndarray]] = None):
        """
        Args:
            embed_fn: callable(list[str]) -> np.ndarray of shape (n, dim). If None,
                      a lexical TF-IDF index is used instead.
        """
        self.embed_fn = embed_fn
        self.chunks: List[str] = []
        self._emb = None          # semantic embeddings matrix
        self._tfidf = None        # TfidfVectorizer (fallback)
        self._matrix = None       # tf-idf sparse matrix (fallback)
        self.mode = "none"

    @staticmethod
    def _chunk(text: str, size: int = 1200, overlap: int = 200) -> List[str]:
        """Split text into overlapping character windows covering the whole paper."""
        text = re.sub(r"\s+", " ", text or "").strip()
        if not text:
            return []
        chunks, i = [], 0
        step = max(1, size - overlap)
        while i < len(text):
            chunks.append(text[i:i + size])
            i += step
        return chunks

    def build(self, full_text: str) -> "PaperRAG":
        """Chunk the whole paper and index it (semantic if possible, else TF-IDF)."""
        self.chunks = self._chunk(full_text)
        if not self.chunks:
            self.mode = "empty"
            return self

        if self.embed_fn is not None:
            try:
                self._emb = np.asarray(self.embed_fn(self.chunks), dtype=np.float32)
                self.mode = "semantic"
                return self
            except Exception as e:
                print(f"[PaperRAG] semantic embedding failed ({e}); using TF-IDF.")

        # Lexical fallback
        from sklearn.feature_extraction.text import TfidfVectorizer
        self._tfidf = TfidfVectorizer(stop_words="english")
        self._matrix = self._tfidf.fit_transform(self.chunks)
        self.mode = "tfidf"
        return self

    def retrieve(self, query: str, k: int = 4) -> List[str]:
        """Return the top-k most relevant chunks for the query."""
        if not self.chunks:
            return []

        if self.mode == "semantic" and self._emb is not None:
            q = np.asarray(self.embed_fn([query]), dtype=np.float32)[0]
            denom = (np.linalg.norm(self._emb, axis=1) * np.linalg.norm(q)) + 1e-9
            sims = (self._emb @ q) / denom
            idx = np.argsort(-sims)[:k]
        else:
            from sklearn.metrics.pairwise import cosine_similarity
            qv = self._tfidf.transform([query])
            sims = cosine_similarity(qv, self._matrix)[0]
            idx = np.argsort(-sims)[:k]

        return [self.chunks[int(i)] for i in idx]
