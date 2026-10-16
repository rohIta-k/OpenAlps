"""Hybrid sentence retrieval using BM25 and multilingual embeddings."""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_MODEL = (
    Path(__file__).resolve().parents[1]
    / "models"
    / "paraphrase-multilingual-MiniLM-L12-v2"
)
RRF_K = 60

# Preserve numbers, dates, abbreviations and negation as searchable tokens.
_TOKEN_RE = re.compile(r"\d+(?:[.,:/\-]\d+)*|[^\W\d_]+", flags=re.UNICODE,)

_NEGATIONS = {
    "no", "not", "never", "neither", "nor", "without",
    "kein", "keine", "keinen", "keiner", "nicht", "nie",
    "aucun", "aucune", "pas", "ne", "jamais", "senza",
    "nessun", "nessuna", "non", "mai",
}

def normalize_text(text: str) -> str:
    """Normalize text for matching without changing source quotations."""
    text = unicodedata.normalize("NFKC", text).casefold()
    text = "".join( char for char in unicodedata.normalize("NFD", text) if unicodedata.category(char) != "Mn")
    return text

def tokenize(text: str) -> list[str]:
    """Tokenize normalized text while retaining numeric and negation terms."""
    return _TOKEN_RE.findall(normalize_text(text))

class HybridRetriever:
    """Rank sentence units with BM25 and multilingual semantic similarity."""
    def __init__(self, sentence_units: list[dict], model_name: str | Path = DEFAULT_MODEL):
        self.sentence_units = sentence_units
        self.model_name = model_name
        self.documents = [tokenize(sentence["text"])for sentence in sentence_units]
        self.doc_lengths = [len(doc) for doc in self.documents]
        self.avg_doc_length = (sum(self.doc_lengths) / len(self.doc_lengths) if self.doc_lengths else 0.0)
        self.doc_frequencies = Counter()
        for document in self.documents:
            self.doc_frequencies.update(set(document))
        self._model = None
        self._embeddings = None

    def _load_embeddings(self) -> None:
        if self._embeddings is not None:
           return
        model_path = Path(self.model_name)
        if model_path.is_dir():
            self._model = SentenceTransformer(str(model_path),local_files_only=True,)
        else:
           model_path.parent.mkdir(parents=True, exist_ok=True)
           self._model = SentenceTransformer(MODEL_NAME)
           self._model.save(str(model_path))
        if not self.sentence_units:
            self._embeddings = np.empty((0, 0), dtype=np.float32)
            return
        texts = [sentence["text"] for sentence in self.sentence_units]
        self._embeddings = self._model.encode(texts,convert_to_numpy=True, normalize_embeddings=True,show_progress_bar=False,)

    def _bm25_scores(self, query_tokens: list[str], k1: float = 1.5, b: float = 0.75,) -> list[float]:
        """Calculate BM25 scores over the sentence collection."""
        count = len(self.documents)
        scores = [0.0] * count
        if not count or not query_tokens:
            return scores
        query_counts = Counter(query_tokens)
        for index, document in enumerate(self.documents):
            if not document:
                continue
            term_counts = Counter(document)
            length_factor = (1 - b + b * self.doc_lengths[index]/ max(self.avg_doc_length, 1e-12))
            score = 0.0
            for term, query_frequency in query_counts.items():
                frequency = term_counts.get(term, 0)
                if not frequency:
                    continue
                df = self.doc_frequencies[term]
                idf = math.log( 1 + (count - df + 0.5) / (df + 0.5))
                term_score = (idf * frequency * (k1 + 1)/ (frequency + k1 * length_factor))
                score += term_score * (1 + math.log(query_frequency))
            scores[index] = score
        return scores

    @staticmethod
    def _rank_indices(scores: list[float]) -> list[int]:
        """Sort by score descending, breaking ties by original order."""
        return sorted(range(len(scores)),key=lambda index: (-scores[index], index),)

    def retrieve(self, claim: str, top_k: int = 30, rrf_k: int = RRF_K, bm25_weight: float = 1.0, vector_weight: float = 1.0,) -> list[dict]:
        """Return hybrid-ranked sentence units with retrieval scores."""
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        if rrf_k < 1:
            raise ValueError("rrf_k must be at least 1")
        if bm25_weight < 0 or vector_weight < 0:
            raise ValueError("Retrieval weights must be non-negative")
        if bm25_weight + vector_weight == 0:
            raise ValueError("At least one retrieval weight must be positive")
        if not self.sentence_units or not claim.strip():
            return []
        bm25_scores = self._bm25_scores(tokenize(claim))
        bm25_order = self._rank_indices(bm25_scores)
        self._load_embeddings()
        query_embedding = self._model.encode([claim], convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False,)[0]
        vector_scores = (self._embeddings @ query_embedding).tolist()
        vector_order = self._rank_indices(vector_scores)
        fused_scores = [0.0] * len(self.sentence_units)
        # RRF combines ranks rather than incomparable raw score scales.
        for weight, ranking in ((bm25_weight, bm25_order), (vector_weight, vector_order),):
            for rank, index in enumerate(ranking, start=1):
                fused_scores[index] += weight / (rrf_k + rank)
        final_order = sorted( range(len(self.sentence_units)), key=lambda index: (-fused_scores[index], index),)
        results = []
        for index in final_order[:top_k]:
            sentence = self.sentence_units[index].copy()
            sentence["bm25_score"] = bm25_scores[index]
            sentence["vector_score"] = vector_scores[index]
            sentence["rrf_score"] = fused_scores[index]
            results.append(sentence)
        return results
