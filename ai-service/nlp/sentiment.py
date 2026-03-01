"""
Sentiment Analysis Module for DebateX.

Analyzes the emotional tone and impact of debate arguments.
Uses HuggingFace transformers sentiment pipeline.
"""

from typing import Optional

# Global pipeline instance (lazy loaded)
_pipeline = None


def _get_pipeline():
    """Lazy-load the sentiment analysis pipeline."""
    global _pipeline
    if _pipeline is None:
        try:
            from transformers import pipeline
            _pipeline = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                top_k=None,
            )
        except Exception:
            _pipeline = "FALLBACK"
    return _pipeline


def analyze_sentiment(text: str) -> dict:
    """
    Analyze the sentiment of a text.

    Returns:
        {
            "label": "POSITIVE" | "NEGATIVE",
            "positive_score": float,
            "negative_score": float,
            "compound": float  (-1 to 1)
        }
    """
    pipe = _get_pipeline()

    if pipe == "FALLBACK":
        return _fallback_sentiment(text)

    try:
        results = pipe(text[:512])  # Truncate to model max length
        scores = {r["label"]: r["score"] for r in results[0]}

        pos_score = scores.get("POSITIVE", 0.5)
        neg_score = scores.get("NEGATIVE", 0.5)
        compound = pos_score - neg_score  # -1 to 1

        return {
            "label": "POSITIVE" if compound >= 0 else "NEGATIVE",
            "positive_score": round(pos_score, 4),
            "negative_score": round(neg_score, 4),
            "compound": round(compound, 4),
        }
    except Exception:
        return _fallback_sentiment(text)


def compute_emotional_impact(argument: str) -> float:
    """
    Compute the emotional impact score of an argument (0-10 scale).

    Higher scores mean stronger emotional resonance.
    Considers both the intensity and direction of sentiment.
    """
    sentiment = analyze_sentiment(argument)
    intensity = abs(sentiment["compound"])

    # Strong sentiment (either direction) = higher emotional impact
    # Scale: intensity (0-1) → score (2-10)
    score = 2.0 + intensity * 8.0

    # Bonus for mixed sentiment (nuanced arguments)
    if 0.3 < sentiment["positive_score"] < 0.7:
        score = min(10, score + 0.5)

    return round(score, 2)


def compute_sentiment_trajectory(arguments: list[str]) -> list[float]:
    """
    Compute sentiment trajectory over multiple arguments.
    Returns list of compound sentiment scores for timeline visualization.
    """
    return [analyze_sentiment(arg)["compound"] for arg in arguments]


def _fallback_sentiment(text: str) -> dict:
    """
    Keyword-based fallback sentiment analysis.
    Used when the transformer model is not available.
    """
    text_lower = text.lower()

    positive_words = {
        "good", "great", "excellent", "benefit", "advantage", "progress",
        "improve", "positive", "success", "effective", "hope", "justice",
        "compassion", "evidence", "proven", "clearly", "strong",
    }
    negative_words = {
        "bad", "terrible", "harmful", "danger", "risk", "fail", "wrong",
        "negative", "problem", "weak", "fallacy", "flawed", "inconsistent",
        "false", "misleading", "destroy", "fear",
    }

    words = set(text_lower.split())
    pos_count = len(words & positive_words)
    neg_count = len(words & negative_words)
    total = max(pos_count + neg_count, 1)

    pos_score = pos_count / total
    neg_score = neg_count / total
    compound = pos_score - neg_score

    return {
        "label": "POSITIVE" if compound >= 0 else "NEGATIVE",
        "positive_score": round(pos_score, 4),
        "negative_score": round(neg_score, 4),
        "compound": round(compound, 4),
    }
