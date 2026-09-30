"""Ingestion CLI entry point: python -m backend.app.ingestion.run [--source <name>] [--all]"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from backend.app.core.logger import setup_logging
from backend.app.db.database import init_db
from backend.app.ingestion.scrapers import FAQScraper, SchemeManualScraper, QCOScraper
from backend.app.ingestion.parsers import DocumentParser
from backend.app.ingestion.chunker import StructureChunker
from backend.app.ingestion.loaders import DataLoader

logger = logging.getLogger("parakh.ingestion")

# Available sources
SOURCES = {
    "faqs": FAQScraper,
    "schemes": SchemeManualScraper,
    "qco": QCOScraper,
    "seed": None,  # seed data is loaded separately
}


async def ingest_source(source_name: str) -> None:
    """Run ingestion for one source."""
    if source_name == "seed":
        await ingest_seed()
        return

    if source_name not in SOURCES:
        logger.error(f"Unknown source: {source_name}. Available: {list(SOURCES.keys())}")
        return

    logger.info(f"=== Ingesting source: {source_name} ===")

    # 1. Scrape (if scraper exists)
    scraper_class = SOURCES[source_name]
    if scraper_class:
        scraper = scraper_class()
        try:
            saved_files = await scraper.scrape_all()
            logger.info(f"Scraped {len(saved_files)} files for {source_name}")
        finally:
            await scraper.close()
    else:
        logger.info(f"No scraper for {source_name}, using existing files in data/raw/")
        saved_files = list(Path("./data/raw").glob("*"))

    # 2. Parse files from data/raw that match this source
    raw_dir = Path("./data/raw")
    if not raw_dir.exists():
        logger.warning("data/raw/ does not exist. Run scrapers first or add files manually.")
        return

    # Use saved_files if available, or filter files by source prefix/stem
    if 'saved_files' in locals() and saved_files:
        files = [f for f in saved_files if f.suffix in (".html", ".pdf")]
    else:
        prefix = source_name.rstrip("s")
        files = [f for f in raw_dir.glob("*.html") if prefix in f.stem]
        files += [f for f in raw_dir.glob("*.pdf") if prefix in f.stem]

    if not files:
        prefix = source_name.rstrip("s")
        files = [f for f in raw_dir.glob("*.html") if prefix in f.stem]
        files += [f for f in raw_dir.glob("*.pdf") if prefix in f.stem]

    if not files:
        logger.warning(f"No files found for source {source_name} in data/raw/")
        return

    all_chunks = []
    for filepath in files:
        try:
            logger.info(f"Parsing: {filepath}")
            parsed = DocumentParser.parse_file(filepath)
            chunks = StructureChunker.chunk_document(parsed)
            all_chunks.extend(chunks)
        except Exception as e:
            logger.error(f"Failed to parse {filepath}: {e}")

    # 3. Load chunks into ChromaDB
    if all_chunks:
        DataLoader.load_chunks_to_vector(all_chunks)
    else:
        logger.warning(f"No chunks generated for source {source_name}")

    logger.info(f"=== Completed ingestion for {source_name} ({len(all_chunks)} chunks) ===")


async def ingest_seed() -> None:
    """Load seed data from data/seed/ into SQLite."""
    logger.info("=== Loading seed data ===")
    seed_file = Path("./data/seed/demo_products.json")
    if seed_file.exists():
        await DataLoader.load_seed_data(seed_file)

    mat_file = Path("./data/seed/material_codes.json")
    if mat_file.exists():
        await DataLoader.load_seed_data(mat_file)

    logger.info("=== Seed data loaded ===")


async def ingest_all() -> None:
    """Run ingestion for all sources."""
    logger.info("=== Ingesting ALL sources ===")
    await ingest_seed()
    for source in SOURCES.keys():
        if source != "seed":
            await ingest_source(source)
    logger.info("=== All ingestion complete ===")


async def print_counts() -> None:
    """Print record counts from SQLite and ChromaDB."""
    from backend.app.db.database import async_session
    from backend.app.db.models import Standard, Scheme, ProductCategory, Lab, HallmarkingCentre, Fee, MaterialCode
    from backend.app.db.vector import get_or_create_collection
    from sqlalchemy import func, select

    logger.info("=== Data Store Counts ===")

    # SQLite counts
    async with async_session() as session:
        schemes_count = (await session.execute(select(func.count()).select_from(Scheme))).scalar()
        products_count = (await session.execute(select(func.count()).select_from(ProductCategory))).scalar()
        labs_count = (await session.execute(select(func.count()).select_from(Lab))).scalar()
        ahc_count = (await session.execute(select(func.count()).select_from(HallmarkingCentre))).scalar()
        fees_count = (await session.execute(select(func.count()).select_from(Fee))).scalar()
        material_codes_count = (await session.execute(select(func.count()).select_from(MaterialCode))).scalar()

        print(f"  Schemes: {schemes_count}")
        print(f"  Products: {products_count}")
        print(f"  Labs: {labs_count}")
        print(f"  Hallmarking Centres: {ahc_count}")
        print(f"  Fees: {fees_count}")
        print(f"  Material Codes: {material_codes_count}")

    # ChromaDB count
    collection = get_or_create_collection()
    print(f"  Vector Chunks: {collection.count()}")
    print()


async def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Parakh knowledge base ingestion")
    parser.add_argument("--source", type=str, help=f"Source to ingest: {list(SOURCES.keys())}")
    parser.add_argument("--all", action="store_true", help="Ingest all sources")
    parser.add_argument("--counts", action="store_true", help="Print data store counts")
    args = parser.parse_args()

    setup_logging("INFO")

    # Initialize database
    await init_db()

    if args.counts:
        await print_counts()
    elif args.all:
        await ingest_all()
        await print_counts()
    elif args.source:
        await ingest_source(args.source)
        await print_counts()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
