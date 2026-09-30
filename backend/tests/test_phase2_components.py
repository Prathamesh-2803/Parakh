"""Simplified Phase 2 test: validate core components without full integration."""

import pytest
from backend.app.core.router import classify_intent
from backend.app.core.cache import normalize_query, make_cache_key, get_cached, set_cached, clear_cache
from backend.app.core.memory import add_turn, get_history, clear_session
from backend.app.core.prompts import build_grounded_query, get_safe_fallback


def test_intent_router():
    """Test intent classification."""
    assert classify_intent("What standard applies to helmets?") == "find_standard"
    assert classify_intent("What is IS 1239?") == "find_standard"
    assert classify_intent("Explain ISI mark scheme") == "explain_scheme"
    assert classify_intent("Where can I test my product?") == "find_lab"
    assert classify_intent("What is hallmarking?") == "hallmarking"
    assert classify_intent("Verify license CM/L 123") == "verify_license"
    assert classify_intent("How do I file a consumer complaint?") == "consumer_query"
    assert classify_intent("What is BIS?") == "general_faq"


def test_cache_normalization():
    """Test query normalization for cache."""
    q1 = "What is IS 1239?"
    q2 = "what is is 1239???"
    q3 = "WHAT IS IS 1239"

    assert normalize_query(q1) == normalize_query(q2)
    assert normalize_query(q2) == normalize_query(q3)
    assert make_cache_key(q1) == make_cache_key(q2)


def test_cache_operations():
    """Test cache set and get."""
    clear_cache()

    q = "What is IS 1239?"
    resp = {"answer": "Test answer", "citations": []}

    # Miss
    assert get_cached(q) is None

    # Set
    set_cached(q, "en", resp)

    # Hit
    cached = get_cached(q, "en")
    assert cached is not None
    assert cached["answer"] == "Test answer"


def test_conversation_memory():
    """Test conversation history tracking."""
    clear_session("s1")

    add_turn("s1", "What is IS 1239?", "It is a standard for steel tubes.")
    add_turn("s1", "Is it mandatory?", "No, it is voluntary.")

    history = get_history("s1")
    assert "IS 1239" in history
    assert "mandatory" in history


def test_grounded_prompt_builder():
    """Test grounded prompt construction."""
    prompt = build_grounded_query(
        question="What is IS 1239?",
        context="IS 1239 covers steel tubes.",
        language="en",
    )

    assert "What is IS 1239?" in prompt
    assert "IS 1239 covers steel tubes" in prompt
    assert "CONTEXT" in prompt
    assert "JSON" in prompt


def test_safe_fallback():
    """Test safe fallback responses."""
    fallback_en = get_safe_fallback("en")
    assert "bis.gov.in" in fallback_en["answer"]
    assert fallback_en["confidence"] == 0.0

    fallback_hi = get_safe_fallback("hi")
    assert "bis.gov.in" in fallback_hi["answer"]
    assert fallback_hi["confidence"] == 0.0


@pytest.mark.asyncio
async def test_sql_tools():
    """Test SQL tool functions."""
    from backend.app.tools.standards import lookup_by_standard_no, search_standards_by_product
    from backend.app.db.database import init_db
    from backend.app.ingestion.loaders import DataLoader
    from pathlib import Path

    await init_db()
    seed_file = Path("./data/seed/demo_products.json")
    if seed_file.exists():
        await DataLoader.load_seed_data(seed_file)

    # Test standard lookup
    result = await lookup_by_standard_no("IS 4151")
    assert result is not None
    assert "Helmets" in result.get("product_name", "")

    # Test product search
    results = await search_standards_by_product("helmet")
    assert len(results) > 0
    assert any("Helmet" in p.get("product_name", "") for p in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
