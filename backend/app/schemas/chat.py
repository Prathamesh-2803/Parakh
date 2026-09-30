"""Request / response schemas for the /chat endpoint."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming chat question from any channel."""

    question: str = Field(..., min_length=1, max_length=2000, description="User's question in any language")
    language: str | None = Field(None, description="ISO 639-1 code if known (e.g. 'hi', 'en')")
    session_id: str | None = Field(None, description="Optional session/conversation ID")


class Citation(BaseModel):
    """A single source citation attached to an answer."""

    source: str = Field(..., description="e.g. IS 1239, BIS Portal")
    section: str | None = Field(None, description="Clause or section reference")
    url: str | None = Field(None, description="Direct URL to the source")


class LLMResponse(BaseModel):
    """Structured LLM response from Gemini/Groq."""

    answer: str = Field(..., description="The answer in plain language")
    citations: list[Citation] = Field(default_factory=list, description="Source citations")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    follow_up_suggestions: list[str] = Field(default_factory=list, description="Suggested follow-up questions")


class ChatResponse(BaseModel):
    """Response returned to any channel."""

    answer: str
    citations: list[Citation] = []
    confidence: float | None = None
    follow_up_suggestions: list[str] = []
    language: str = "en"
    session_id: str | None = None
    request_id: str | None = None
    from_cache: bool = False
