"""Evaluation script for compliance recommendation accuracy (Top-1 and Top-3)."""

import asyncio
import json
import logging
from pathlib import Path

from backend.app.core.logger import setup_logging
from backend.app.db.database import init_db
from backend.app.tools.recommend import recommend_compliance

logger = logging.getLogger("parakh.eval")


async def run_evaluation(test_set_path: Path) -> None:
    """Run recommendation evaluation against test set."""
    if not test_set_path.exists():
        print(f"Error: Test set not found at {test_set_path}")
        return

    with open(test_set_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    total_cases = len(test_cases)
    top1_correct = 0
    top3_correct = 0
    ambiguity_triggers = 0

    print(f"\n=======================================================")
    print(f"  PARAKH COMPLIANCE RECOMMENDATION EVALUATION REPORT")
    print(f"  Test cases: {total_cases}")
    print(f"=======================================================\n")

    for tc in test_cases:
        tc_id = tc["id"]
        inp = tc["input"]
        exp_prod = tc["expected_product"]

        candidates, is_ambiguous, clarifying_q = await recommend_compliance(inp, top_k=3)

        cand_names = [c["product_name"] for c in candidates]
        is_top1 = len(cand_names) > 0 and cand_names[0] == exp_prod
        is_top3 = exp_prod in cand_names

        if is_top1:
            top1_correct += 1
        if is_top3:
            top3_correct += 1
        if is_ambiguous:
            ambiguity_triggers += 1

        status = "[TOP-1 OK]" if is_top1 else ("[TOP-3 OK]" if is_top3 else "[FAIL]")
        ambig_str = " (Ambiguous -> Asked Clarification)" if is_ambiguous else ""

        print(f"Test #{tc_id:02d} {status}{ambig_str}")
        print(f"  Query   : \"{inp}\"")
        print(f"  Expected: {exp_prod}")
        print(f"  Top Match: {cand_names[0] if cand_names else 'None'} (Confidence: {candidates[0]['confidence'] if candidates else 0.0})")
        if is_ambiguous and clarifying_q:
            print(f"  Clarification: \"{clarifying_q}\"")
        print()

    top1_acc = (top1_correct / total_cases) * 100
    top3_acc = (top3_correct / total_cases) * 100

    print(f"=======================================================")
    print(f"  SUMMARY RESULTS")
    print(f"=======================================================")
    print(f"  Total Test Cases : {total_cases}")
    print(f"  Top-1 Accuracy   : {top1_correct}/{total_cases} ({top1_acc:.1f}%)")
    print(f"  Top-3 Accuracy   : {top3_correct}/{total_cases} ({top3_acc:.1f}%)")
    print(f"  Ambiguous Queries Detected: {ambiguity_triggers}")
    print(f"=======================================================\n")


async def main():
    setup_logging("WARNING")
    await init_db()
    test_set_path = Path("./data/seed/recommend_test_set.json")
    await run_evaluation(test_set_path)


if __name__ == "__main__":
    asyncio.run(main())
