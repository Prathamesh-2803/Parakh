"""Unit tests for the product compliance recommendation engine."""

import pytest
from backend.app.tools.recommend import recommend_compliance


@pytest.mark.asyncio
async def test_recommend_led_bulbs():
    """Test LED bulb recommendation."""
    product_desc = "I manufacture LED bulbs and lamps for home lighting"
    candidates, is_ambiguous, clarifying_q = await recommend_compliance(product_desc, top_k=3)

    assert len(candidates) > 0
    assert candidates[0]["product_name"] == "LED Lamps & Bulbs (Self-ballasted)"
    assert candidates[0]["applicable_standard"] == "IS 16102 (Part 1)"
    assert candidates[0]["scheme_code"] == "ISI"
    assert candidates[0]["mandatory"] is True
    assert candidates[0]["confidence"] > 0.7
    assert is_ambiguous is False


@pytest.mark.asyncio
async def test_recommend_mobile_charger():
    """Test mobile phone charger recommendation."""
    product_desc = "We produce mobile phone power adapters and USB wall chargers"
    candidates, is_ambiguous, clarifying_q = await recommend_compliance(product_desc, top_k=3)

    assert len(candidates) > 0
    assert candidates[0]["product_name"] == "Mobile Phone Power Adapters & Chargers"
    assert candidates[0]["scheme_code"] == "CRS"
    assert candidates[0]["mandatory"] is True


@pytest.mark.asyncio
async def test_recommend_gold_jewellery():
    """Test gold jewellery recommendation."""
    product_desc = "We craft 22k gold jewellery, bangles and rings"
    candidates, is_ambiguous, clarifying_q = await recommend_compliance(product_desc, top_k=3)

    assert len(candidates) > 0
    assert candidates[0]["product_name"] == "Gold Jewellery and Artefacts"
    assert candidates[0]["scheme_code"] == "HALLMARK"
    assert candidates[0]["mandatory"] is True


@pytest.mark.asyncio
async def test_ambiguous_input():
    """Test that ambiguous input triggers clarification."""
    product_desc = "Steel bars and steel tubes for building and plumbing"
    candidates, is_ambiguous, clarifying_q = await recommend_compliance(product_desc, top_k=3)

    assert is_ambiguous is True
    assert clarifying_q is not None
    assert "specify your exact product type" in clarifying_q
    assert len(candidates) >= 2


@pytest.mark.asyncio
async def test_empty_description():
    """Test empty or very short description."""
    product_desc = "XYZ obscure non-existent product 12345"
    candidates, is_ambiguous, clarifying_q = await recommend_compliance(product_desc, top_k=3)

    # All low confidence candidates should be filtered
    assert isinstance(candidates, list)
    assert is_ambiguous is False
    assert clarifying_q is None
