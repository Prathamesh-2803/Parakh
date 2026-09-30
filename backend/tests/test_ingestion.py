"""Tests for the ingestion pipeline."""

import json
from pathlib import Path
import pytest
from sqlalchemy import select, func

from backend.app.db.database import async_session, init_db
from backend.app.db.models import Scheme, ProductCategory, Lab, HallmarkingCentre, Fee
from backend.app.ingestion.parsers import DocumentParser
from backend.app.ingestion.chunker import StructureChunker
from backend.app.ingestion.loaders import DataLoader


@pytest.mark.asyncio
async def test_seed_data_loader():
    """Test loading seed data into SQLite."""
    await init_db()
    seed_file = Path("./data/seed/demo_products.json")
    assert seed_file.exists()

    await DataLoader.load_seed_data(seed_file)

    async with async_session() as session:
        # Check schemes loaded
        schemes = (await session.execute(select(Scheme))).scalars().all()
        assert len(schemes) >= 4

        # Check products loaded
        products = (await session.execute(select(ProductCategory))).scalars().all()
        assert len(products) >= 15

        # Check that demo data is properly marked
        demo_products = [p for p in products if p.is_demo]
        assert len(demo_products) == len(products)

        # Check labs
        labs = (await session.execute(select(Lab))).scalars().all()
        assert len(labs) >= 2


def test_html_parser():
    """Test HTML parsing."""
    html_content = """
    <html>
      <body>
        <h1>Test Section</h1>
        <p>This is test content for standard IS 1239.</p>
        <h2>Clause 4.1 Scope</h2>
        <p>This standard covers steel tubes.</p>
      </body>
    </html>
    """
    tmp_file = Path("./data/raw/test_sample.html")
    tmp_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_file.write_text(html_content, encoding="utf-8")

    try:
        parsed = DocumentParser.parse_file(tmp_file)
        assert len(parsed["sections"]) >= 2
        assert "IS 1239" in parsed["full_text"]
    finally:
        if tmp_file.exists():
            tmp_file.unlink()


def test_structure_chunker():
    """Test structure-aware chunking and metadata extraction."""
    parsed_doc = {
        "full_text": "Clause 4.1 Scope\n\nThis standard IS 1239 covers mild steel tubes for water and gas.",
        "sections": [
            {
                "heading": "Clause 4.1 Scope",
                "content": "This standard IS 1239 covers mild steel tubes for water and gas.",
            }
        ],
        "metadata": {
            "filename": "is_1239.html",
            "source_url": "https://www.bis.gov.in/",
        },
    }

    chunks = StructureChunker.chunk_document(parsed_doc)
    assert len(chunks) >= 1
    c = chunks[0]
    assert c["metadata"]["standard_no"] == "IS 1239"
    assert "Clause 4.1" in c["metadata"]["clause"]
    assert c["metadata"]["source_name"] == "is_1239.html"
