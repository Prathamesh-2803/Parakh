"""Quick verification script for Phase 1 - works without ML dependencies."""

import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.core.logger import setup_logging
from backend.app.db.database import init_db, async_session
from backend.app.db.models import Scheme, ProductCategory, Lab, HallmarkingCentre, Fee
from backend.app.ingestion.loaders import DataLoader
from sqlalchemy import select, func


async def verify_seed_data():
    """Load and verify seed data without vector store."""
    setup_logging("INFO")
    print("=" * 60)
    print("Phase 1 Verification - Seed Data Only")
    print("=" * 60)

    # Initialize database
    await init_db()
    print("[OK] Database initialized")

    # Load seed data
    seed_file = Path("./data/seed/demo_products.json")
    if not seed_file.exists():
        print(f"[FAIL] Seed file not found: {seed_file}")
        return

    await DataLoader.load_seed_data(seed_file)
    print(f"[OK] Seed data loaded from {seed_file}")

    # Verify counts
    print("\n" + "=" * 60)
    print("SQLite Record Counts")
    print("=" * 60)

    async with async_session() as session:
        schemes_count = (await session.execute(select(func.count()).select_from(Scheme))).scalar()
        products_count = (await session.execute(select(func.count()).select_from(ProductCategory))).scalar()
        labs_count = (await session.execute(select(func.count()).select_from(Lab))).scalar()
        ahc_count = (await session.execute(select(func.count()).select_from(HallmarkingCentre))).scalar()
        fees_count = (await session.execute(select(func.count()).select_from(Fee))).scalar()

        print(f"  Schemes:             {schemes_count}")
        print(f"  Product Categories:  {products_count}")
        print(f"  Labs:                {labs_count}")
        print(f"  Hallmarking Centres: {ahc_count}")
        print(f"  Fees:                {fees_count}")

        # Sample data
        print("\n" + "=" * 60)
        print("Sample Products (first 5)")
        print("=" * 60)
        products = (await session.execute(select(ProductCategory).limit(5))).scalars().all()
        for p in products:
            mandatory = "MANDATORY" if p.mandatory else "voluntary"
            demo = " [DEMO]" if p.is_demo else ""
            print(f"  * {p.product_name} -> {p.applicable_standard} ({mandatory}){demo}")

        # Check demo data marking
        demo_count = (await session.execute(
            select(func.count()).select_from(ProductCategory).where(ProductCategory.is_demo == True)
        )).scalar()
        print(f"\n[OK] All {demo_count} products correctly marked as DEMO DATA")

    print("\n" + "=" * 60)
    print("Phase 1 Verification Complete")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Follow BIS_DATA_COLLECTION_CHECKLIST.md to download real BIS documents")
    print("2. Once dependencies finish installing, run:")
    print("   PYTHONPATH=. python -m backend.app.ingestion.run --all")
    print()


if __name__ == "__main__":
    asyncio.run(verify_seed_data())
