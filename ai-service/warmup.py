"""
DebateX AI Service — NLP Model Warmup
=====================================
Pre-downloads and caches models needed for judge evaluation.
Run this before starting the main service to avoid hangs during first debate.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Warmup")

def warmup_nlp():
    """Download and cache all required NLP models."""
    logger.info("🔥 Starting NLP Model Warmup...")
    
    # 1. Sentence Transformers (Topic Relevance & Coherence)
    try:
        from nlp.embeddings import _get_model
        logger.info("📥 Loading SentenceTransformer ('all-MiniLM-L6-v2')...")
        model = _get_model()
        if model != "FALLBACK":
            logger.info("✅ SentenceTransformer ready.")
        else:
            logger.warning("⚠️ SentenceTransformer initialization failed (using fallback).")
    except Exception as e:
        logger.error(f"❌ Failed to load SentenceTransformer: {e}")

    # 2. Sentiment Analysis (Emotional Impact)
    try:
        from nlp.sentiment import _get_pipeline
        logger.info("📥 Loading Sentiment Analysis Pipeline ('distilbert-base-uncased-finetuned-sst-2-english')...")
        pipe = _get_pipeline()
        if pipe != "FALLBACK":
            logger.info("✅ Sentiment Analysis Pipeline ready.")
        else:
            logger.warning("⚠️ Sentiment Analysis Pipeline initialization failed (using fallback).")
    except Exception as e:
        logger.error(f"❌ Failed to load Sentiment Pipeline: {e}")

    logger.info("✨ Warmup Complete! All models cached.")

if __name__ == "__main__":
    # Add parent directory to path for imports
    sys.path.append(os.getcwd())
    warmup_nlp()
