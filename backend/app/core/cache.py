"""In-memory cache for chat responses with query normalization."""

import hashlib
import logging
import re
from typing import Dict, Any, Optional

from backend.app.config import settings

logger = logging.getLogger("parakh.cache")

# In-memory cache: {cache_key: response_dict}
_cache: Dict[str, Dict[str, Any]] = {}


def normalize_query(text: str) -> str:
    """Normalize a query for cache matching: lowercase, collapse whitespace, remove punctuation."""
    # Lowercase
    text = text.lower()
    # Remove punctuation except spaces
    text = re.sub(r"[^\w\s]", "", text)
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def make_cache_key(question: str, language: str = "en") -> str:
    """Generate a stable cache key from normalized query + language."""
    normalized = normalize_query(question)
    key_str = f"{normalized}:{language}"
    return hashlib.md5(key_str.encode("utf-8")).hexdigest()


def get_cached(question: str, language: str = "en") -> Optional[Dict[str, Any]]:
    """Retrieve cached response if it exists."""
    key = make_cache_key(question, language)
    if key in _cache:
        logger.info(f"Cache HIT for key={key[:8]}...")
        return _cache[key]
    logger.info(f"Cache MISS for key={key[:8]}...")
    return None


def set_cached(question: str, language: str, response: Dict[str, Any]) -> None:
    """Store a response in the cache."""
    key = make_cache_key(question, language)
    _cache[key] = response
    logger.info(f"Cached response for key={key[:8]}... (cache size: {len(_cache)})")


def clear_cache() -> None:
    """Clear all cached responses."""
    _cache.clear()
    logger.info("Cache cleared")
