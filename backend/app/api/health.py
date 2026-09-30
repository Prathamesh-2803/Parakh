"""Health-check endpoint: returns app status, LLM provider status, DB & Chroma readiness."""

import os
import logging
from typing import Dict, Any
from fastapi import APIRouter
from sqlalchemy import text

from backend.app.config import settings
from backend.app.db.database import async_session
from backend.app.core.cache import _cache

router = APIRouter(tags=["health"])
logger = logging.getLogger("parakh.health")


@router.get("/health")
async def health() -> Dict[str, Any]:
    """
    Comprehensive health check:
    - App metadata (name, version, environment)
    - Database readiness (SQLite async connection)
    - Chroma vector DB status
    - LLM provider status (Gemini, Groq, Mock Mode) and quota indicators
    - In-memory cache status
    """
    # 1. Check Database
    db_status = "healthy"
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"unhealthy: {exc}"

    # 2. Check ChromaDB
    chroma_status = "healthy"
    chroma_path = settings.CHROMA_PERSIST_DIR
    if not os.path.exists(chroma_path):
        chroma_status = f"not_found (path: {chroma_path})"

    # 3. Check LLM Providers
    gemini_configured = bool(settings.GEMINI_API_KEY)
    groq_configured = bool(settings.GROQ_API_KEY)

    providers = {
        "mock_mode": settings.MOCK_LLM,
        "gemini": {
            "configured": gemini_configured,
            "model": settings.GEMINI_MODEL,
            "status": "ready" if (gemini_configured or settings.MOCK_LLM) else "missing_key",
        },
        "groq": {
            "configured": groq_configured,
            "model": settings.GROQ_MODEL,
            "status": "ready" if groq_configured else "not_configured",
        },
    }

    # 4. Cache statistics
    cache_stats = {
        "backend": settings.CACHE_BACKEND,
        "cached_entries_count": len(_cache),
        "status": "active",
    }

    overall_status = "ok" if (db_status == "healthy") else "degraded"

    return {
        "status": overall_status,
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": db_status,
        "vector_store": chroma_status,
        "llm_providers": providers,
        "cache": cache_stats,
    }
