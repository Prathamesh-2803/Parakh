"""Pydantic schemas for feedback."""

from typing import Optional
from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    question: str = Field(..., min_length=1, description="The user query or product prompt")
    answer: str = Field(..., min_length=1, description="The response provided to user")
    rating: str = Field(..., pattern="^(positive|negative)$", description="User rating: positive (thumbs up) or negative (thumbs down)")
    comment: Optional[str] = Field(None, max_length=1000, description="Optional user comment/correction")
    language: Optional[str] = Field("en", description="Language code")


class FeedbackResponse(BaseModel):
    status: str = "ok"
    feedback_id: int
    message: str = "Feedback recorded successfully"
