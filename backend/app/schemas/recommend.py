"""Schemas for the product compliance recommendation endpoint."""

from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    """Request for product compliance recommendation."""

    product_description: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Free-text product description (e.g., 'I manufacture LED bulbs for homes')",
    )
    language: str | None = Field(None, description="Response language (en/hi/mr/ta)")


class CandidateMatch(BaseModel):
    """A candidate product match with compliance details."""

    product_name: str = Field(..., description="Matched product category")
    applicable_standard: str | None = Field(None, description="IS number")
    scheme_code: str = Field(..., description="ISI/CRS/FMCS/HALLMARK")
    mandatory: bool = Field(..., description="Whether certification is mandatory")
    qco_order: str | None = Field(None, description="Quality Control Order reference")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Match confidence 0.0-1.0")
    key_requirements: list[str] = Field(default_factory=list, description="Key technical/process requirements")
    next_steps: list[str] = Field(default_factory=list, description="Steps to obtain certification")
    nearest_labs: list[str] = Field(default_factory=list, description="Nearby testing labs")


class RecommendResponse(BaseModel):
    """Response with top candidate matches and optional clarifying question."""

    candidates: list[CandidateMatch] = Field(default_factory=list, description="Top 1-3 matches ranked by confidence")
    is_ambiguous: bool = Field(False, description="Whether input requires clarification")
    clarifying_question: str | None = Field(None, description="Question to disambiguate if ambiguous")
    language: str = Field("en")
    request_id: str | None = None
