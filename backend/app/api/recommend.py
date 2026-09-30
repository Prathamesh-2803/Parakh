"""POST /recommend endpoint: product compliance recommendation."""

import logging

from fastapi import APIRouter, Request

from backend.app.schemas.recommend import RecommendRequest, RecommendResponse, CandidateMatch
from backend.app.tools.recommend import recommend_compliance
from backend.app.core.lang import detect_language

router = APIRouter(tags=["recommend"])
logger = logging.getLogger("parakh.api.recommend")


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(body: RecommendRequest, request: Request) -> RecommendResponse:
    """
    POST /recommend: Given a free-text product description, return top 1-3
    compliance matches with applicable standards, schemes, requirements, and next steps.
    """
    request_id: str = getattr(request.state, "request_id", "unknown")
    language = body.language or detect_language(body.product_description)
    logger.info(f"POST /recommend [rid={request_id}]: '{body.product_description[:80]}'")

    # Run recommendation engine
    candidates, is_ambiguous, clarifying_question = await recommend_compliance(
        body.product_description,
        top_k=3,
    )

    # Convert to response schema
    candidate_models = [CandidateMatch(**c) for c in candidates]

    return RecommendResponse(
        candidates=candidate_models,
        is_ambiguous=is_ambiguous,
        clarifying_question=clarifying_question,
        language=language,
        request_id=request_id,
    )
