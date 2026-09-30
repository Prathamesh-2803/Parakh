"""Integration tests for the image-based product scan feature with sample images."""

import io
import os
import pytest
from unittest.mock import patch

from backend.app.tools.scan import identify_product_from_image
from backend.app.schemas.scan import ScanResult, MarkVerificationResult


# Helper to load test image bytes
def load_test_image(filename: str) -> bytes:
    """Load a test image from the fixtures directory."""
    test_dir = os.path.join(os.path.dirname(__file__), "fixtures", "scan_images")
    path = os.path.join(test_dir, filename)
    with open(path, "rb") as f:
        return f.read()


@pytest.mark.asyncio
async def test_bisleri_bottle_visual_classifier():
    """Test Bisleri bottle -> visual classifier identifies as bottle."""
    image_bytes = load_test_image("bisleri_bottle.jpg")

    scan_result, mark_verification = await identify_product_from_image(
        image_bytes=image_bytes,
        mime_type="image/jpeg",
        language="en",
    )

    # Visual classifier identifies as bottle (confidence > 0.15)
    assert scan_result.identification_method == "visual_classifier"
    assert "Plastic bottles" in scan_result.product_description
    assert scan_result.confidence >= 0.15
    assert mark_verification is None


@pytest.mark.asyncio
async def test_gold_ring_hallmark_visual_classifier():
    """Test gold ring -> visual classifier identifies as gold jewelry."""
    image_bytes = load_test_image("gold_ring_hallmark.jpg")

    scan_result, mark_verification = await identify_product_from_image(
        image_bytes=image_bytes,
        mime_type="image/jpeg",
        language="en",
    )

    # Visual classifier identifies as gold jewelry (confidence > 0.15)
    assert scan_result.identification_method == "visual_classifier"
    assert "Gold jewellery" in scan_result.product_description
    assert scan_result.confidence >= 0.15
    assert mark_verification is None


@pytest.mark.asyncio
async def test_prestige_cooker_ocr_match():
    """Test prestige cooker with 'IS 2347 CM/L-1234567' -> OCR match for standard and license."""
    image_bytes = load_test_image("prestige_cooker.jpg")

    scan_result, mark_verification = await identify_product_from_image(
        image_bytes=image_bytes,
        mime_type="image/jpeg",
        language="en",
    )

    # Expect OCR code match for IS standard
    assert scan_result.identification_method == "ocr_code_match"
    assert scan_result.matched_code == "IS 2347"
    assert "Domestic Pressure Cookers" in scan_result.product_description
    assert scan_result.confidence >= 0.9

    # Expect license detection and verification
    assert mark_verification is not None
    assert mark_verification.license == "CM/L-1234567"
    assert mark_verification.license_valid is True
    # No HUID expected
    assert mark_verification.huid is None


@pytest.mark.asyncio
async def test_plain_mug_visual_classifier_or_manual():
    """Test plain mug -> visual classifier may return 'other' class, falls back to manual."""
    image_bytes = load_test_image("plain_mug.jpg")

    scan_result, mark_verification = await identify_product_from_image(
        image_bytes=image_bytes,
        mime_type="image/jpeg",
        language="en",
    )

    # Plain mug is not in training classes, so classifier may return 'other' (falls to manual)
    # or low-confidence visual_classifier. Both are acceptable.
    assert scan_result.identification_method in ("visual_classifier", "manual_required")
    assert mark_verification is None


@pytest.mark.asyncio
async def test_gemini_fallback_degrades_to_visual_classifier_or_manual():
    """Test that when Gemini is unavailable, visual classifier is tried before manual fallback."""
    image_bytes = load_test_image("plain_mug.jpg")  # No text, so OCR will fail

    # Temporarily disable mock mode to force Gemini Vision fallback
    with patch.dict(os.environ, {"MOCK_LLM": "false"}):
        # Mock generate_vision to simulate failure (e.g., API key missing)
        with patch("backend.app.tools.scan.generate_vision") as mock_vision:
            # Simulate an exception from the vision API (e.g., missing API key)
            mock_vision.side_effect = Exception("Gemini API key not configured")

            scan_result, mark_verification = await identify_product_from_image(
                image_bytes=image_bytes,
                mime_type="image/jpeg",
                language="en",
            )

            # Visual classifier is attempted; may return visual_classifier or fall to manual
            assert scan_result.identification_method in ("visual_classifier", "manual_required")
            assert mark_verification is None
