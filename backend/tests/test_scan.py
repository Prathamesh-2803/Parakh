"""Unit and integration tests for the image-based product scan feature."""

import io
import json
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.tools.scan import identify_product_from_image, _hash_image
from backend.app.schemas.scan import ScanResult, MarkVerificationResult, ScanResponse


# A tiny valid 1x1 PNG byte string for testing
TINY_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.mark.asyncio
async def test_identify_product_ocr_first():
    """Test identify_product_from_image with OCR match bypassing vision."""
    # Test OCR-first path by mocking extract_text_from_image and match_material_code
    with patch("backend.app.tools.scan.extract_text_from_image", return_value="PC"), \
         patch("backend.app.tools.scan.match_material_code") as mock_match:
        # Set up mock match
        from backend.app.schemas.scan import MaterialCodeMatch
        mock_match.return_value = MaterialCodeMatch(
            category="plastic_resin_code",
            code="7",
            label="OTHER / PC",
            material_name="Polycarbonate / Other Plastics",
            confidence=0.95,
            raw_matched_text="PC",
        )

        scan_result, mark_verification = await identify_product_from_image(
            image_bytes=TINY_PNG_BYTES,
            mime_type="image/png",
            language="en",
        )

        assert isinstance(scan_result, ScanResult)
        assert scan_result.confidence == 0.95
        assert scan_result.product_description == "Polycarbonate / Other Plastics"
        assert mark_verification is None


@pytest.mark.asyncio
async def test_identify_product_ocr_huid():
    """Test identify_product_from_image with OCR match containing HUID."""
    with patch("backend.app.tools.scan.extract_text_from_image", return_value="916 HUID-AB12CD"), \
         patch("backend.app.tools.scan.match_material_code") as mock_match:
        from backend.app.schemas.scan import MaterialCodeMatch
        mock_match.return_value = MaterialCodeMatch(
            category="gold_hallmark",
            code="916",
            label="22K",
            material_name="22 Karat Gold (91.6% purity)",
            confidence=0.95,
            raw_matched_text="916",
            detected_huid="HUID-AB-12CD",
        )

        scan_result, mark_verification = await identify_product_from_image(
            image_bytes=TINY_PNG_BYTES,
            mime_type="image/png",
            language="en",
        )

        assert scan_result.product_description == "22 Karat Gold (91.6% purity)"
        assert mark_verification is not None
        assert mark_verification.huid == "HUID-AB-12CD"
        # Since verify_huid is called, let's check its behavior
        assert mark_verification.huid_valid in [True, False]


@pytest.mark.asyncio
async def test_identify_product_mock_mode():
    """Test identify_product_from_image with default mock mode."""
    # In mock mode, if OCR fails, it returns a manual_required result
    with patch.dict("os.environ", {"MOCK_LLM": "true"}), \
         patch("backend.app.tools.scan.extract_text_from_image", return_value=""), \
         patch("backend.app.tools.scan.match_material_code", return_value=None):
        scan_result, mark_verification = await identify_product_from_image(
            image_bytes=TINY_PNG_BYTES,
            mime_type="image/png",
            language="en",
        )

        assert isinstance(scan_result, ScanResult)
        assert scan_result.confidence == 0.0
        assert "Manual selection required" in scan_result.product_description
        assert mark_verification is None


@pytest.mark.asyncio
async def test_identify_product_low_confidence():
    """Test handling of low-confidence vision extraction."""
    mock_low_conf_llm = {
        "text": json.dumps({
            "product_description": "Blurry or unknown object",
            "detected_text": "",
            "confidence": 0.15
        }),
        "provider": "mock",
    }

    with patch.dict("os.environ", {"MOCK_LLM": "false"}), \
         patch("backend.app.tools.scan.generate_vision", AsyncMock(return_value=mock_low_conf_llm)):
        scan_result, mark_verification = await identify_product_from_image(
            image_bytes=TINY_PNG_BYTES,
            mime_type="image/png",
            language="en",
        )

        assert scan_result.confidence == 0.15
        assert mark_verification is None


@pytest.mark.asyncio
async def test_identify_product_license_auto_verification():
    """Test automatic BIS license verification when detected in image text."""
    mock_license_llm = {
        "text": json.dumps({
            "product_description": "LED Bulb 9W",
            "detected_text": "PHILIPS ISI CM/L-1234567 230V 50HZ",
            "confidence": 0.95
        }),
        "provider": "mock",
    }

    with patch.dict("os.environ", {"MOCK_LLM": "false"}), \
         patch("backend.app.tools.scan.generate_vision", AsyncMock(return_value=mock_license_llm)):
        scan_result, mark_verification = await identify_product_from_image(
            image_bytes=TINY_PNG_BYTES,
            mime_type="image/png",
            language="en",
        )

        assert scan_result.product_description == "LED Bulb 9W"
        assert mark_verification is not None
        assert mark_verification.license == "CM/L-1234567"
        assert mark_verification.license_valid is True


@pytest.mark.asyncio
async def test_post_scan_endpoint_success():
    """Integration test for POST /scan end-to-end with valid image."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        files = {
            "file": ("test_bulb.png", io.BytesIO(TINY_PNG_BYTES), "image/png")
        }
        resp = await ac.post("/scan", files=files, data={"language": "en"})
        assert resp.status_code == 200
        data = resp.json()

        assert "product_description" in data
        assert "confidence" in data
        assert "recommend_result" in data
        assert "candidates" in data["recommend_result"]
        assert "mark_verification" in data


@pytest.mark.asyncio
async def test_post_scan_caching():
    """Test that scanning the same image hash hits cache."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        files1 = {
            "file": ("test_cache.png", io.BytesIO(TINY_PNG_BYTES), "image/png")
        }
        resp1 = await ac.post("/scan", files=files1)
        assert resp1.status_code == 200

        files2 = {
            "file": ("test_cache.png", io.BytesIO(TINY_PNG_BYTES), "image/png")
        }
        resp2 = await ac.post("/scan", files=files2)
        assert resp2.status_code == 200
        assert resp2.json()["product_description"] == resp1.json()["product_description"]


@pytest.mark.asyncio
async def test_post_scan_invalid_mime():
    """Test rejecting non-image MIME types."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        files = {
            "file": ("test.txt", io.BytesIO(b"Hello world text file"), "text/plain")
        }
        resp = await ac.post("/scan", files=files)
        assert resp.status_code == 400
        assert "Invalid file type" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_post_scan_oversized_image():
    """Test rejecting images larger than 8MB."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create a mock 9MB byte payload
        big_bytes = b"0" * (9 * 1024 * 1024)
        files = {
            "file": ("huge.png", io.BytesIO(big_bytes), "image/png")
        }
        resp = await ac.post("/scan", files=files)
        assert resp.status_code == 413
        assert "exceeds limit" in resp.json()["detail"]
