"""
embeddings/embedder.py

Local embedding generation using SentenceTransformers all-MiniLM-L6-v2.
Fully free, runs on CPU, no API cost.

Model details:
- 384 dimensions (matches pgvector column in SpecSection model)
- ~80MB download on first run (cached afterwards)
- ~500 sentences/sec on CPU
"""

import logging
from functools import lru_cache
from typing import List

logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _get_model():
    """
    Load and cache the model — singleton pattern to avoid re-loading
    on every request (it takes ~2 seconds to load).
    """
    from sentence_transformers import SentenceTransformer
    logger.info(f"Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    logger.info("Embedding model loaded.")
    return model


def embed_text(text: str) -> List[float]:
    """
    Embed a single text string. Returns a 384-dim vector as a list of floats.
    """
    model = _get_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def embed_batch(texts: List[str], batch_size: int = 64) -> List[List[float]]:
    """
    Embed a batch of texts efficiently.
    batch_size=64 is a good default for CPU — adjust down if OOM.
    """
    model = _get_model()
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=len(texts) > 50,  # Show progress for large batches
    )
    return [e.tolist() for e in embeddings]


def similarity_search_vector(query: str) -> List[float]:
    """
    Convenience wrapper: embed a query string for pgvector similarity search.
    The returned vector can be passed directly to pgvector's <=> operator.
    """
    return embed_text(query)
