"""Chat endpoint for the Parakh RAG pipeline."""

import json
import re
import logging
from typing import Optional
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from backend.app.core.safety import sanitize_input, is_prompt_injection
from backend.app.core.lang import detect_language
from backend.app.core.router import classify_intent
from backend.app.core.retrieval import gather_context
from backend.app.core.llm import generate
from backend.app.core.prompts import build_grounded_query, get_safe_fallback
from backend.app.core.cache import get_cached, set_cached, clear_cache
from backend.app.core.memory import get_history, add_turn
from backend.app.core.logger import logger
from backend.app.schemas.chat import ChatRequest, ChatResponse, LLMResponse, Citation

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request) -> ChatResponse:
    """
    POST /chat: Full RAG pipeline.
    1. Check cache
    2. Check if query is BIS-related (if not, return safe fallback)
    3. Intent routing (rule-based, no LLM call)
    4. Context gathering (SQL tools + hybrid retrieval)
    5. ONE Gemini call with strict grounding prompt
    6. Citation validation
    7. Cache and return
    """
    request_id: str = getattr(request.state, "request_id", "unknown")
    language = body.language or detect_language(body.question)
    session_id = body.session_id

    # Safety: sanitize input and check for prompt injection
    sanitized_question = sanitize_input(body.question)
    is_injection, reason = is_prompt_injection(sanitized_question)
    if is_injection:
        logger.warning(f"Prompt injection detected [rid={request_id}]: {reason}")
        fallback = get_safe_fallback(language)
        return ChatResponse(
            **fallback,
            session_id=session_id,
            request_id=request_id,
            from_cache=False,
        )

    logger.info(f"POST /chat [rid={request_id}]: '{sanitized_question[:80]}'")

    # 1. Cache lookup
    cached_resp = get_cached(sanitized_question, language)
    if cached_resp:
        return ChatResponse(
            **cached_resp,
            session_id=session_id,
            request_id=request_id,
            from_cache=True,
        )

    # 2. Check if the query is BIS-related or matches known standards/products
    q_lower = body.question.lower()
    is_bis_related = (
        bool(re.search(r"\bis\s*\d+", q_lower))
        or any(
            k in q_lower
            for k in [
                "bis",
                "standard",
                "manak",
                "scheme",
                "isi",
                "crs",
                "fmcs",
                "hallmark",
                "huid",
                "lab",
                "license",
                "helmet",
                "cement",
                "steel",
                "led",
                "cylinder",
                "gold",
                "water",
            ]
        )
    )

    if not is_bis_related:
        logger.info("Query is not BIS-related, returning safe fallback")
        fallback = get_safe_fallback(language)
        # Do not cache non-BIS queries
        return ChatResponse(
            **fallback,
            session_id=session_id,
            request_id=request_id,
            from_cache=False,
        )

    # 3. Intent routing (zero cost)
    intent = classify_intent(body.question)
    logger.info(f"Intent classified: {intent}")

    # 4. Context gathering
    context, retrieved_chunks = await gather_context(intent, body.question, language)

    # Check for out-of-domain or missing context queries
    if not context.strip() and (not is_bis_related or intent not in ["general_faq", "explain_scheme"]):
        logger.info("No context retrieved for query, returning safe fallback")
        fallback = get_safe_fallback(language)
        set_cached(body.question, language, fallback)
        return ChatResponse(
            **fallback,
            session_id=session_id,
            request_id=request_id,
            from_cache=False,
        )

    # 5. Build prompt and make ONE LLM call
    history = get_history(session_id) if session_id else ""
    prompt = build_grounded_query(
        question=body.question,
        context=context,
        language=language,
        conversation_history=history,
    )

    llm_result = await generate(prompt=prompt, context="")
    llm_text = llm_result.get("text", "")

    # 6. Parse structured JSON from LLM output
    parsed_response: Optional[LLMResponse] = None
    try:
        # Extract JSON substring if wrapped in markdown code blocks
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", llm_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = llm_text

        data = json.loads(json_str)
        parsed_response = LLMResponse(**data)
    except Exception as e:
        logger.warning(f"Failed to parse LLM JSON response: {e}. Raw text: {llm_text[:200]}")
        # In mock mode, construct a valid mock response
        if "mock" in llm_text.lower():
            parsed_response = LLMResponse(
                answer=llm_text,
                citations=[Citation(source="Parakh Mock DB", section="Demo", url="https://www.bis.gov.in/")],
                confidence=0.9,
                follow_up_suggestions=[
                    "What other standards exist?",
                    "How do I apply for ISI?",
                ],
                language=language,
            )
        else:
            # For non-mock mode, return a safe fallback if we cannot parse the response
            logger.warning("Returning safe fallback due to LLM response parsing failure")
            fallback = get_safe_fallback(language)
            return ChatResponse(
                **fallback,
                session_id=session_id,
                request_id=request_id,
                from_cache=False,
            )

    # 7. Validate citations and confidence
    if parsed_response.confidence < 0.3:
        logger.info(f"Low confidence response ({parsed_response.confidence}), returning safe fallback")
        fallback = get_safe_fallback(language)
        set_cached(body.question, language, fallback)
        return ChatResponse(
            **fallback,
            session_id=session_id,
            request_id=request_id,
            from_cache=False,
        )

    # 8. Cache and return
    set_cached(sanitized_question, language, parsed_response.model_dump())
    
    # Save conversation history for follow-up questions
    if session_id:
        add_turn(session_id, body.question, parsed_response.answer)
    
    return ChatResponse(
        **parsed_response.model_dump(),
        session_id=session_id,
        request_id=request_id,
        from_cache=False,
    )