"""SQL Tool: Standard lookup by IS number, product name, or category."""

import logging
import re
from typing import Dict, Any, List, Optional

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.database import async_session
from backend.app.db.models import ProductCategory, Standard, Scheme

logger = logging.getLogger("parakh.tools.standards")


async def lookup_by_standard_no(standard_no: str) -> Optional[Dict[str, Any]]:
    """Lookup standard details by IS number (e.g., 'IS 1239', 'IS 4151')."""
    # Clean up standard number
    std_clean = standard_no.upper().strip()
    if not std_clean.startswith("IS"):
        std_clean = f"IS {std_clean}"

    async with async_session() as session:
        # Check product_categories first (has mandatory status)
        result = await session.execute(
            select(ProductCategory).where(ProductCategory.applicable_standard.ilike(f"%{std_clean}%"))
        )
        product = result.scalars().first()

        if product:
            return {
                "product_name": product.product_name,
                "applicable_standard": product.applicable_standard,
                "scheme_code": product.scheme_code,
                "mandatory": product.mandatory,
                "qco_order": product.qco_order,
                "source_url": product.source_url,
                "is_demo": product.is_demo,
            }

        # Check standards table
        result = await session.execute(
            select(Standard).where(Standard.standard_no.ilike(f"%{std_clean}%"))
        )
        std = result.scalars().first()

        if std:
            return {
                "standard_no": std.standard_no,
                "title": std.title,
                "scope": std.scope,
                "status": std.status,
                "year": std.year,
                "source_url": std.source_url,
            }

    return None


def _extract_keywords(text: str) -> List[str]:
    """Extract search keywords from query."""
    stopwords = {
        "what", "which", "is", "for", "the", "a", "an", "and", "or", "to", "in", "of",
        "applies", "covers", "standard", "mandatory", "where", "can", "how", "do", "i",
        "find", "list", "get", "explain", "about", "with", "from", "goods", "items",
    }
    tokens = re.findall(r"\b\w+\b", text.lower())
    return [t for t in tokens if t not in stopwords and len(t) > 2]


async def search_standards_by_product(product_query: str) -> List[Dict[str, Any]]:
    """Search for standards by product name or keywords."""
    keywords = _extract_keywords(product_query)

    async with async_session() as session:
        filters = [
            ProductCategory.product_name.ilike(f"%{product_query}%"),
            ProductCategory.category.ilike(f"%{product_query}%"),
        ]

        for kw in keywords:
            filters.append(ProductCategory.product_name.ilike(f"%{kw}%"))
            filters.append(ProductCategory.category.ilike(f"%{kw}%"))

        result = await session.execute(
            select(ProductCategory).where(or_(*filters))
        )
        products = result.scalars().all()

        # Deduplicate while preserving order
        seen = set()
        unique_products = []
        for p in products:
            if p.id not in seen:
                seen.add(p.id)
                unique_products.append(p)

        return [
            {
                "product_name": p.product_name,
                "category": p.category,
                "applicable_standard": p.applicable_standard,
                "scheme_code": p.scheme_code,
                "mandatory": p.mandatory,
                "qco_order": p.qco_order,
                "source_url": p.source_url,
                "is_demo": p.is_demo,
            }
            for p in unique_products
        ]
