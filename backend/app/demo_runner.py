"""
Demo runner script for Parakh.

Runs the 4 demo queries against the /chat endpoint and prints the responses.
Designed to showcase the system working end-to-end with pre-warmed cache.
"""

import asyncio
import json
from typing import Dict, Any
import httpx

DEMO_QUERIES = [
    {
        "question": "What is the standard for motorcycle helmets?",
        "language": "en",
        "description": "Product lookup (English)"
    },
    {
        "question": "Explain the ISI mark certification process.",
        "language": "en",
        "description": "Scheme explanation (English)"
    },
    {
        "question": "Verify BIS license CM/L-4151201",
        "language": "en",
        "description": "License verification (English)"
    },
    {
        "question": "दोपहिया वाहन चालकों के लिए हेलमेट का मानक क्या है?",
        "language": "hi",
        "description": "Hindi query"
    }
]

async def run_demo(api_base_url: str = "http://127.0.0.1:8000"):
        def safe_print(text):
            try:
                print(text)
            except UnicodeEncodeError:
                # Fallback to ASCII approximation or just skip problematic characters
                print(text.encode('ascii', 'ignore').decode('ascii'))

        safe_print("=" * 60)
        safe_print("           PARAKH DEMO RUNNER")
        safe_print("=" * 60)
        safe_print(f"Backend URL: {api_base_url}")
        safe_print(f"Number of demo queries: {len(DEMO_QUERIES)}\n")

        async with httpx.AsyncClient(timeout=10.0) as client:
            for i, demo in enumerate(DEMO_QUERIES, 1):
                safe_print(f"[{i}/{len(DEMO_QUERIES)}] {demo['description']}")
                safe_print(f"Q: {demo['question']}")
                try:
                    resp = await client.post(
                        f"{api_base_url}/chat",
                        json={"question": demo["question"], "language": demo["language"]},
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        answer = data.get("answer", "")
                        citations = data.get("citations", [])
                        confidence = data.get("confidence", 0.0)
                        lang = data.get("language", demo["language"])
                        from_cache = data.get("from_cache", False)

                        safe_print(f"A: {answer}")
                        if citations:
                            safe_print(f"Citations: {len(citations)} source(s)")
                            for cit in citations[:2]:  # Show first two citations
                                safe_print(f"  - {cit.get('source')}: {cit.get('section', 'N/A')}")
                        safe_print(f"Confidence: {confidence:.2f} | Language: {lang} | From Cache: {from_cache}")
                    else:
                        safe_print(f"Error: HTTP {resp.status_code}")
                        safe_print(f"Response: {resp.text}")
                except Exception as exc:
                    safe_print(f"Error: {exc}")

                safe_print("-" * 60)
                # Small delay between queries
                await asyncio.sleep(0.5)

        safe_print("\nDemo completed. Note: The first run may populate the cache; subsequent runs will be faster.\n")

if __name__ == "__main__":
    asyncio.run(run_demo())
