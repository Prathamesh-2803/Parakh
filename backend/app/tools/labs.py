"""SQL Tool: Lab and AHC finder by product, location, or pincode."""

import logging
from typing import Dict, Any, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.database import async_session
from backend.app.db.models import Lab, HallmarkingCentre

logger = logging.getLogger("parakh.tools.labs")


async def find_labs_by_location(
    state: Optional[str] = None,
    city: Optional[str] = None,
    scope_keyword: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Find testing labs by state, city, or product scope."""
    async with async_session() as session:
        query = select(Lab)

        if state:
            query = query.where(Lab.state.ilike(f"%{state}%"))
        if city:
            query = query.where(Lab.city.ilike(f"%{city}%"))
        if scope_keyword:
            query = query.where(Lab.accreditation_scope.ilike(f"%{scope_keyword}%"))

        result = await session.execute(query)
        labs = result.scalars().all()

        return [
            {
                "lab_name": l.lab_name,
                "lab_code": l.lab_code,
                "address": l.address,
                "state": l.state,
                "city": l.city,
                "accreditation_scope": l.accreditation_scope,
                "contact": l.contact,
                "source_url": l.source_url,
                "is_demo": l.is_demo,
            }
            for l in labs
        ]


async def find_ahc_by_location(
    state: Optional[str] = None,
    city: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Find Assaying & Hallmarking Centres by state or city."""
    async with async_session() as session:
        query = select(HallmarkingCentre)

        if state:
            query = query.where(HallmarkingCentre.state.ilike(f"%{state}%"))
        if city:
            query = query.where(HallmarkingCentre.city.ilike(f"%{city}%"))

        result = await session.execute(query)
        centres = result.scalars().all()

        return [
            {
                "centre_name": c.centre_name,
                "centre_code": c.centre_code,
                "address": c.address,
                "state": c.state,
                "city": c.city,
                "contact": c.contact,
                "source_url": c.source_url,
                "is_demo": c.is_demo,
            }
            for c in centres
        ]
