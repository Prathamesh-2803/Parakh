"""Feedback API endpoint: records user ratings and suggestions."""

import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.schemas.feedback import FeedbackRequest, FeedbackResponse
from backend.app.db.database import get_session, init_db
from backend.app.db.models import Feedback

router = APIRouter(tags=["feedback"])
logger = logging.getLogger("parakh.feedback")


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    body: FeedbackRequest,
    session: AsyncSession = Depends(get_session),
) -> FeedbackResponse:
    """
    POST /feedback: Record user ratings (thumbs up/down) and comments on answers.
    """
    try:
        await init_db()

        feedback_entry = Feedback(
            request_id=body.request_id,
            session_id=body.session_id,
            question=body.question,
            answer=body.answer,
            rating=body.rating,
            comment=body.comment,
            language=body.language or "en",
        )
        session.add(feedback_entry)
        await session.commit()
        await session.refresh(feedback_entry)

        logger.info(f"Feedback recorded: ID={feedback_entry.id}, rating={body.rating}, req_id={body.request_id}")
        return FeedbackResponse(
            status="ok",
            feedback_id=feedback_entry.id,
            message="Feedback recorded successfully",
        )
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to record feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
