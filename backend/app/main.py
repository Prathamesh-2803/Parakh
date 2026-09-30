"""Parakh FastAPI application — entry point."""

import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure the backend package is importable
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from backend.app.config import settings
from backend.app.core.logger import setup_logging
from backend.app.core.middleware import RequestIDMiddleware, RateLimitMiddleware
from backend.app.core.prewarm import prewarm_cache
from backend.app.db.database import init_db
from backend.app.api.health import router as health_router
from backend.app.api.chat import router as chat_router
from backend.app.api.recommend import router as recommend_router
from backend.app.api.feedback import router as feedback_router
from backend.app.api.verify import router as verify_router
from backend.app.api.scan import router as scan_router

# --- Logging ---
setup_logging("DEBUG" if settings.DEBUG else "INFO")
logger = logging.getLogger("parakh")


# --- Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    logger.info(
        "%s v%s starting (mock_llm=%s)",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.MOCK_LLM,
    )
    # Initialize DB tables
    await init_db()
    # Pre-warm demo cache
    prewarm_cache()
    yield
    logger.info("Shutting down %s", settings.APP_NAME)


# --- App ---
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI assistant for Indian Standards and BIS services",
    lifespan=lifespan,
)

# --- Middleware (order matters: first added = outermost) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    max_requests=settings.RATE_LIMIT_REQUESTS,
    window_seconds=settings.RATE_LIMIT_WINDOW,
)

# --- Routers ---
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(recommend_router)
app.include_router(feedback_router)
app.include_router(verify_router)
app.include_router(scan_router)
