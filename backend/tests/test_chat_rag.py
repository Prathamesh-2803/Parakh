"""Integration test suite for Phase 2: Core RAG pipeline with 15 test questions across all intents."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.cache import clear_cache
from backend.app.core.memory import clear_session
from backend.app.db.database import init_db
from backend.app.ingestion.loaders import DataLoader
from pathlib import Path

client = TestClient(app)


import pytest
import asyncio
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.cache import clear_cache
from backend.app.core.memory import clear_session
from backend.app.db.database import init_db
from backend.app.ingestion.loaders import DataLoader
from pathlib import Path

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def setup_test_data():
    """Ensure database has seed data once per session."""
    async def _init():
        await init_db()
        seed_file = Path("./data/seed/demo_products.json")
        if seed_file.exists():
            await DataLoader.load_seed_data(seed_file)

    asyncio.run(_init())
    clear_cache()


# ---------------------------------------------------------------------------
# 15 Test Questions across all 7 intents
# ---------------------------------------------------------------------------

TEST_QUESTIONS = [
    # Intent: find_standard (4 questions)
    ("What standard applies to helmets for two-wheeler riders?", "find_standard"),
    ("Which standard covers mild steel tubes?", "find_standard"),
    ("Is IS 16102 mandatory for LED lamps?", "find_standard"),
    ("What is the standard for packaged drinking water?", "find_standard"),

    # Intent: explain_scheme (3 questions)
    ("Explain the ISI mark certification scheme and process.", "explain_scheme"),
    ("What is the Compulsory Registration Scheme (CRS)?", "explain_scheme"),
    ("How does the Foreign Manufacturers Certification Scheme (FMCS) work?", "explain_scheme"),

    # Intent: find_lab (2 questions)
    ("Where can I find testing labs in Delhi for electronics?", "find_lab"),
    ("List recognized laboratories for construction materials in Mumbai.", "find_lab"),

    # Intent: hallmarking (2 questions)
    ("What is HUID and why is gold hallmarking mandatory?", "hallmarking"),
    ("Find Assaying and Hallmarking Centres in Delhi.", "hallmarking"),

    # Intent: verify_license (1 question)
    ("How do I verify a BIS license number?", "verify_license"),

    # Intent: consumer_query (2 questions)
    ("How do I file a complaint about substandard ISI marked goods?", "consumer_query"),
    ("What is the BIS Care App used for?", "consumer_query"),

    # Intent: general_faq (1 question)
    ("What is the Bureau of Indian Standards and what is its role?", "general_faq"),
]


@pytest.mark.parametrize("question,expected_intent", TEST_QUESTIONS)
def test_all_intents_return_responses(question: str, expected_intent: str):
    """Test that all 15 questions across intents return valid responses."""
    resp = client.post("/chat", json={"question": question})
    assert resp.status_code == 200

    data = resp.json()
    assert "answer" in data
    assert len(data["answer"]) > 0
    assert "citations" in data
    assert "request_id" in data
    assert data["from_cache"] is False


def test_cache_hits_on_repeated_question():
    """Test that a repeated question hits the cache."""
    clear_cache()
    q = "What standard applies to helmets for two-wheeler riders?"

    # First call: cache miss
    resp1 = client.post("/chat", json={"question": q})
    assert resp1.status_code == 200
    assert resp1.json()["from_cache"] is False

    # Second call: cache hit
    resp2 = client.post("/chat", json={"question": q})
    assert resp2.status_code == 200
    assert resp2.json()["from_cache"] is True
    assert resp2.json()["answer"] == resp1.json()["answer"]


def test_cache_normalisation():
    """Test that minor variations in punctuation/casing still hit the cache."""
    clear_cache()
    q1 = "What standard applies to helmets?"
    q2 = "what standard applies to helmets???"

    resp1 = client.post("/chat", json={"question": q1})
    assert resp1.json()["from_cache"] is False

    resp2 = client.post("/chat", json={"question": q2})
    assert resp2.json()["from_cache"] is True


def test_unknown_question_returns_safe_fallback():
    """Test that an unknown/out-of-domain question returns a safe fallback."""
    q = "What is the recipe for chocolate cake with strawberry frosting?"
    resp = client.post("/chat", json={"question": q})
    assert resp.status_code == 200

    data = resp.json()
    # Should contain BIS portal link or safe fallback language
    assert "https://www.bis.gov.in" in data["answer"] or "bis" in data["answer"].lower()


def test_conversation_memory():
    """Test that conversation memory accumulates turns."""
    clear_session("test_session_1")

    # Turn 1
    resp1 = client.post(
        "/chat",
        json={"question": "What is IS 1239?", "session_id": "test_session_1"},
    )
    assert resp1.status_code == 200

    # Turn 2
    resp2 = client.post(
        "/chat",
        json={"question": "Is it mandatory?", "session_id": "test_session_1"},
    )
    assert resp2.status_code == 200
    assert resp2.json()["session_id"] == "test_session_1"
