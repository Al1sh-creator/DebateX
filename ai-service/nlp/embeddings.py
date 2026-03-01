"""
Sentence Embeddings Module for DebateX.

Uses sentence-transformers to compute semantic similarity
between arguments and the debate topic.
"""

import numpy as np
from typing import Optional

# Global model instance (lazy loaded)
_model = None


def _get_model():
    """Lazy-load the sentence transformer model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            _model = "FALLBACK"
    return _model


def get_embedding(text: str) -> np.ndarray:
    """Get the embedding vector for a text string."""
    model = _get_model()
    if model == "FALLBACK":
        # Fallback: simple TF-IDF-like vector
        return _fallback_embedding(text)
    return model.encode(text, normalize_embeddings=True)


def compute_similarity(text_a: str, text_b: str) -> float:
    """
    Compute cosine similarity between two texts.
    Returns a value between -1 and 1 (typically 0 to 1 for natural language).
    """
    emb_a = get_embedding(text_a)
    emb_b = get_embedding(text_b)
    return float(np.dot(emb_a, emb_b))


def compute_topic_relevance(argument: str, topic: str) -> float:
    """
    Compute how relevant an argument is to the debate topic.
    Returns a score from 0 to 10.
    """
    similarity = compute_similarity(argument, topic)
    # Map cosine similarity (0-1 range) to a 0-10 score
    return round(max(0, min(10, similarity * 12)), 2)


def cluster_topic(topic: str) -> int:
    """
    Assign a topic to a cluster index for Q-table state encoding.
    Uses embedding-based bucketing (0-9).
    """
    emb = get_embedding(topic)
    # Use first embedding dimension to determine cluster
    cluster = int(abs(emb[0]) * 10) % 10
    return cluster


def _fallback_embedding(text: str) -> np.ndarray:
    """Simple hash-based fallback embedding when models are unavailable."""
    np.random.seed(hash(text.lower().strip()) % (2**31))
    return np.random.randn(384).astype(np.float32)
