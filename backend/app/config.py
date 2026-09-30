"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Central configuration — all values come from env vars or .env file."""

    # --- App ---
    APP_NAME: str = "Parakh"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # --- LLM: Gemini (primary) ---
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # --- LLM: Groq (fallback) ---
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # --- LLM behaviour ---
    MOCK_LLM: bool = True  # safe default for dev
    LLM_MAX_RETRIES: int = 3
    LLM_RETRY_BASE_DELAY: float = 1.0  # seconds, exponential backoff base

    # --- Rate Limiting ---
    RATE_LIMIT_REQUESTS: int = 120  # requests per window
    RATE_LIMIT_WINDOW: int = 60     # per minute

    # --- ChromaDB ---
    CHROMA_PERSIST_DIR: str = "./data/chroma"

    # --- SQLite / SQLAlchemy ---
    # Keep the existing file name so a rename does not orphan persisted data.
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/pramaan.db"

    # --- Cache ---
    CACHE_BACKEND: str = "memory"  # "memory" or "redis"
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL: int = 3600  # seconds

    # --- OCR / Tesseract ---
    TESSERACT_CMD: str = ""  # e.g. "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

    # --- Multilingual ---
    SUPPORTED_LANGUAGES: list[str] = ["en", "hi", "mr", "ta"]  # English, Hindi, Marathi, Tamil
    DEFAULT_LANGUAGE: str = "en"
    # Optional Bhashini adapter behind feature flag
    ENABLE_BHASHINI: bool = False
    BHASHINI_USER_ID: str = ""
    BHASHINI_API_KEY: str = ""
    BHASHINI_PIPELINE_ID: str = ""
    BHASHINI_INFERENCE_URL: str = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


# Singleton — import this everywhere
settings = Settings()
