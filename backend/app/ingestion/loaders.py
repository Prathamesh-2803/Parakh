"""Data loaders: insert structured facts into SQLite and chunks into ChromaDB."""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.database import async_session, init_db
from backend.app.db.models import (
    Standard,
    Scheme,
    ProductCategory,
    Lab,
    HallmarkingCentre,
    Fee,
    MaterialCode,
)
from backend.app.db.vector import add_chunks

logger = logging.getLogger("parakh.loaders")


class DataLoader:
    """Load structured data into SQLite and vector chunks into ChromaDB."""

    @staticmethod
    async def load_seed_data(seed_file: Path) -> None:
        """Load seed JSON data into SQLite."""
        if not seed_file.exists():
            logger.warning(f"Seed file not found: {seed_file}")
            return

        logger.info(f"Loading seed data from {seed_file}")
        data = json.loads(seed_file.read_text(encoding="utf-8"))

        async with async_session() as session:
            if isinstance(data, list):
                # Direct list of material codes
                for item in data:
                    if "category" in item and "code" in item:
                        await DataLoader._upsert_material_code(session, item)
            elif isinstance(data, dict):
                # Load schemes
                for item in data.get("schemes", []):
                    await DataLoader._upsert_scheme(session, item)

                # Load products
                for item in data.get("products", []):
                    await DataLoader._upsert_product(session, item)

                # Load labs
                for item in data.get("labs", []):
                    await DataLoader._upsert_lab(session, item)

                # Load hallmarking centres
                for item in data.get("hallmarking_centres", []):
                    await DataLoader._upsert_hallmarking_centre(session, item)

                # Load fees
                for item in data.get("fees", []):
                    await DataLoader._upsert_fee(session, item)

                # Load material codes if in dict
                for item in data.get("material_codes", []):
                    await DataLoader._upsert_material_code(session, item)

            await session.commit()

        logger.info(f"Seed data loaded from {seed_file}")

    @staticmethod
    def _parse_item(data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert ISO date strings to datetime objects for SQLite."""
        cleaned = dict(data)
        if "fetched_at" in cleaned and isinstance(cleaned["fetched_at"], str):
            cleaned["fetched_at"] = datetime.fromisoformat(cleaned["fetched_at"].replace("Z", "+00:00"))
        return cleaned

    @staticmethod
    async def _upsert_scheme(session: AsyncSession, data: Dict[str, Any]) -> None:
        """Insert or update a scheme."""
        data = DataLoader._parse_item(data)
        result = await session.execute(
            select(Scheme).where(Scheme.scheme_code == data["scheme_code"])
        )
        existing = result.scalars().first()

        if existing:
            for key, val in data.items():
                setattr(existing, key, val)
        else:
            session.add(Scheme(**data))

    @staticmethod
    async def _upsert_product(session: AsyncSession, data: Dict[str, Any]) -> None:
        """Insert or update a product category."""
        data = DataLoader._parse_item(data)
        result = await session.execute(
            select(ProductCategory).where(
                ProductCategory.product_name == data["product_name"]
            )
        )
        existing = result.scalars().first()

        if existing:
            for key, val in data.items():
                setattr(existing, key, val)
        else:
            session.add(ProductCategory(**data))

    @staticmethod
    async def _upsert_lab(session: AsyncSession, data: Dict[str, Any]) -> None:
        """Insert or update a lab."""
        data = DataLoader._parse_item(data)
        if data.get("lab_code"):
            result = await session.execute(
                select(Lab).where(Lab.lab_code == data["lab_code"])
            )
            existing = result.scalars().first()
        else:
            existing = None

        if existing:
            for key, val in data.items():
                setattr(existing, key, val)
        else:
            session.add(Lab(**data))

    @staticmethod
    async def _upsert_hallmarking_centre(session: AsyncSession, data: Dict[str, Any]) -> None:
        """Insert or update a hallmarking centre."""
        data = DataLoader._parse_item(data)
        if data.get("centre_code"):
            result = await session.execute(
                select(HallmarkingCentre).where(
                    HallmarkingCentre.centre_code == data["centre_code"]
                )
            )
            existing = result.scalars().first()
        else:
            existing = None

        if existing:
            for key, val in data.items():
                setattr(existing, key, val)
        else:
            session.add(HallmarkingCentre(**data))

    @staticmethod
    async def _upsert_fee(session: AsyncSession, data: Dict[str, Any]) -> None:
        """Insert or update a fee entry."""
        data = DataLoader._parse_item(data)
        session.add(Fee(**data))

    @staticmethod
    async def _upsert_material_code(session: AsyncSession, data: Dict[str, Any]) -> None:
        """Insert or update a material code entry."""
        data = DataLoader._parse_item(data)
        # Ensure applicable_standards is stored as a JSON string if list
        if "applicable_standards" in data and isinstance(data["applicable_standards"], list):
            data["applicable_standards"] = json.dumps(data["applicable_standards"])

        result = await session.execute(
            select(MaterialCode).where(
                MaterialCode.category == data["category"],
                MaterialCode.code == data["code"]
            )
        )
        existing = result.scalars().first()

        if existing:
            for key, val in data.items():
                setattr(existing, key, val)
        else:
            session.add(MaterialCode(**data))

    @staticmethod
    def load_chunks_to_vector(chunks: List[Dict[str, Any]]) -> None:
        """Load chunks into ChromaDB vector store."""
        if not chunks:
            logger.info("No chunks to load into vector store")
            return

        logger.info(f"Loading {len(chunks)} chunks into ChromaDB...")
        add_chunks(chunks)
        logger.info(f"Successfully loaded {len(chunks)} chunks into ChromaDB")
