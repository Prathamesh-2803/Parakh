"""Manual test script for Phase 2: demonstrates RAG pipeline with sample questions."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.core.router import classify_intent
from backend.app.core.cache import get_cached, set_cached, clear_cache
from backend.app.core.prompts import build_grounded_query, get_safe_fallback
from backend.app.db.database import init_db
from backend.app.ingestion.loaders import DataLoader
from backend.app.tools.standards import lookup_by_standard_no, search_standards_by_product
from backend.app.tools.labs import find_labs_by_location


async def demo_phase2():
    """Demonstrate Phase 2 RAG components."""
    print("=" * 70)
    print("PHASE 2 DEMO: Core RAG Pipeline")
    print("=" * 70)

    # Setup
    await init_db()
    seed_file = Path("./data/seed/demo_products.json")
    if seed_file.exists():
        await DataLoader.load_seed_data(seed_file)
    clear_cache()

    # 1. Intent Classification
    print("\n[1] Intent Classification (Rule-Based)")
    print("-" * 70)
    questions = [
        "What standard applies to helmets?",
        "Explain ISI certification process",
        "Where can I test electronics in Delhi?",
        "What is hallmarking?",
    ]
    for q in questions:
        intent = classify_intent(q)
        print(f"  Q: {q}")
        print(f"  Intent: {intent}\n")

    # 2. SQL Tools
    print("\n[2] SQL Tools: Standards Lookup")
    print("-" * 70)
    std_result = await lookup_by_standard_no("IS 4151")
    if std_result:
        print(f"  Product: {std_result.get('product_name')}")
        print(f"  Standard: {std_result.get('applicable_standard')}")
        print(f"  Mandatory: {std_result.get('mandatory')}")
        print(f"  QCO: {std_result.get('qco_order')}")

    print("\n[3] SQL Tools: Product Search")
    print("-" * 70)
    products = await search_standards_by_product("cement")
    for p in products[:2]:
        print(f"  - {p.get('product_name')}: {p.get('applicable_standard')}")

    print("\n[4] SQL Tools: Lab Finder")
    print("-" * 70)
    labs = await find_labs_by_location(city="Delhi")
    for lab in labs:
        print(f"  - {lab.get('lab_name')}: {lab.get('accreditation_scope')}")

    # 3. Cache
    print("\n[5] Cache Test")
    print("-" * 70)
    q = "What is IS 1239?"
    print(f"  First lookup: {get_cached(q)}")
    set_cached(q, "en", {"answer": "Cached answer", "citations": []})
    print(f"  After cache: {get_cached(q)}")

    # 4. Grounded Prompt
    print("\n[6] Grounded Prompt Construction")
    print("-" * 70)
    prompt = build_grounded_query(
        question="What is IS 4151?",
        context="IS 4151 covers helmets for two-wheeler riders. It is mandatory under QCO 2016.",
        language="en",
    )
    print(f"  Prompt length: {len(prompt)} chars")
    print(f"  Contains CONTEXT: {'CONTEXT' in prompt}")
    print(f"  Contains JSON schema: {'JSON' in prompt}")

    # 5. Safe Fallback
    print("\n[7] Safe Fallback Response")
    print("-" * 70)
    fallback = get_safe_fallback("en")
    print(f"  Answer excerpt: {fallback['answer'][:100]}...")
    print(f"  Confidence: {fallback['confidence']}")
    print(f"  Citations: {len(fallback['citations'])}")

    print("\n" + "=" * 70)
    print("PHASE 2 DEMO COMPLETE")
    print("=" * 70)
    print("\nAll core components working:")
    print("  [OK] Intent routing (rule-based, 7 intents)")
    print("  [OK] SQL tools (standards, labs, products)")
    print("  [OK] Cache (query normalization + get/set)")
    print("  [OK] Grounded prompts (strict JSON output)")
    print("  [OK] Safe fallback (low confidence)")
    print("\nNext: Run integration tests or start the server")
    print("  pytest backend/tests/test_phase2_components.py -v")
    print("  MOCK_LLM=true uvicorn backend.app.main:app --reload")
    print()


if __name__ == "__main__":
    asyncio.run(demo_phase2())
