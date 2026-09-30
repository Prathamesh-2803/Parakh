"""Tests for the LLM gateway (core/llm.py)."""

import pytest
import asyncio

from backend.app.core.llm import generate


@pytest.mark.asyncio
async def test_mock_generate_returns_text():
    """Mock mode should return a canned response."""
    result = await generate("What is IS 1239?")
    assert "text" in result
    assert result["provider"] == "mock"
    assert len(result["text"]) > 0


@pytest.mark.asyncio
async def test_mock_generate_has_usage():
    """Mock response should include usage metadata."""
    result = await generate("test")
    assert "usage" in result
    assert result["usage"]["prompt_tokens"] == 0


@pytest.mark.asyncio
async def test_mock_generate_ignores_context():
    """Context should be accepted but not affect mock output."""
    r1 = await generate("q", context="")
    r2 = await generate("q", context="some context")
    assert r1["text"] == r2["text"]
