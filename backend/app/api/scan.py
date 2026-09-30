"""Image-based product scan endpoint."""

import hashlib
import logging
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from backend.app.schemas.scan import ScanResponse, ScanResult, MarkVerificationResult
from backend.app.tools.recommend import recommend_compliance
from backend.app.tools.scan import identify_product_from_image, _hash_image

logger = logging.getLogger("parakh.scan")

router = APIRouter(tags=["scan"])

# In-memory cache for scan results: {image_hash: ScanResponse}
_scan_cache: dict[str, ScanResponse] = {}

# Constants
MAX_IMAGE_SIZE = 8 * 1024 * 1024  # 8 MB
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("/scan", response_model=ScanResponse)
async def scan_image(
    file: UploadFile = File(...),
    language: Optional[str] = None,
) -> ScanResponse:
    """
    POST /scan: Upload an image of a product to get compliance recommendations.
    - Validates file type and size (<=8MB)
    - Computes SHA-256 hash for caching
    - Uses OCR-first pipeline with Gemini Vision fallback to extract product description and detected text
    - If license/HUID detected, runs verification
    - Feeds product description into existing recommend_compliance function
    - Returns structured compliance roadmap plus verification (if applicable)
    """
    # 1. Validate file type
    if file.content_type not in ALLOWED_MIME_TYPES:
        logger.warning(f"Invalid file type: {file.content_type}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(sorted(ALLOWED_MIME_TYPES))}",
        )

    # 2. Read file and validate size
    image_bytes = await file.read()
    if len(image_bytes) > MAX_IMAGE_SIZE:
        logger.warning(f"Image too large: {len(image_bytes)} bytes")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image size exceeds limit of {MAX_IMAGE_SIZE // (1024*1024)} MB",
        )

    # 3. Compute hash for caching
    image_hash = _hash_image(image_bytes)
    logger.info(f"Processing image with hash: {image_hash}")

    # 4. Check cache
    if image_hash in _scan_cache:
        logger.info(f"Returning cached result for hash: {image_hash}")
        cached = _scan_cache[image_hash]
        return ScanResponse(**cached.model_dump())

    # 5. Identify product from image
    try:
        scan_result, mark_verification = await identify_product_from_image(
            image_bytes=image_bytes,
            mime_type=file.content_type,
            language=language or "en",
        )
    except Exception as exc:
        logger.error(f"Vision processing failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to process image. Please try again later.",
        ) from exc

    # 6. Check if manual selection is required or confidence is low
    # Allow visual_classifier with lower confidence (0.15) since it's trained on limited data
    min_confidence = 0.15 if scan_result.identification_method == "visual_classifier" else 0.3
    if scan_result.confidence < min_confidence or scan_result.identification_method == "manual_required":
        logger.info(
            f"Low confidence ({scan_result.confidence}) or manual selection required: "
            f"method={scan_result.identification_method}, reason={scan_result.failure_reason}"
        )
        manual_options = await _get_manual_options()
        recommend_result = {
            "candidates": [],
            "is_ambiguous": False,
            "clarifying_question": None,
        }

        # Friendly user-facing guidance
        message_map = {
            "no_text_detected": "No markings or codes detected in the image. Please select a category below or type a description.",
            "text_detected_no_match": "Text was detected but could not be matched to an Indian Standard or code. Please select a category below.",
            "ocr_unavailable": "OCR service is currently unavailable. Please select a product category manually.",
            "vision_unavailable": "AI vision could not identify this product. Please select a category below or type a description.",
        }
        friendly_msg = message_map.get(
            scan_result.failure_reason or "",
            "Please select the product type manually or provide a text description."
        )

        response = ScanResponse(
            product_description=scan_result.product_description,
            confidence=scan_result.confidence,
            identification_method="manual_required",
            matched_code=scan_result.matched_code,
            material_info=scan_result.material_info,
            manual_options=manual_options,
            failure_reason=scan_result.failure_reason,
            recommend_result=recommend_result,
            mark_verification=mark_verification,
            message=friendly_msg,
        )
        _scan_cache[image_hash] = response
        return response

    # 7. Confidence is sufficient: run compliance recommendation
    logger.info(
        f"Product identified: '{scan_result.product_description}' "
        f"(confidence={scan_result.confidence}, method={scan_result.identification_method})"
    )
    try:
        candidates, is_ambiguous, clarifying_question = await recommend_compliance(
            product_description=scan_result.product_description
        )
    except Exception as exc:
        logger.error(f"Recommendation failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate compliance recommendation.",
        ) from exc

    recommend_result = {
        "candidates": candidates,
        "is_ambiguous": is_ambiguous,
        "clarifying_question": clarifying_question,
    }

    # 8. Build and return final response
    response = ScanResponse(
        product_description=scan_result.product_description,
        confidence=scan_result.confidence,
        identification_method=scan_result.identification_method,
        matched_code=scan_result.matched_code,
        material_info=scan_result.material_info,
        manual_options=None,
        failure_reason=scan_result.failure_reason,
        recommend_result=recommend_result,
        mark_verification=mark_verification,
        message=None,
    )

    # 9. Cache the response
    _scan_cache[image_hash] = response
    logger.info(f"Scan completed and cached for hash: {image_hash}")

    return response


async def _get_manual_options() -> list[dict[str, Any]]:
    """Get manual options for frontend category picker."""
    return [
        {
            "value": "plastic_resin_code",
            "label": "Plastic Resin Codes",
            "description": "PET (1), HDPE (2), PVC (3), LDPE (4), PP (5), PS (6), Other/PC (7)",
        },
        {
            "value": "gold_hallmark",
            "label": "Gold Hallmark & Jewellery",
            "description": "24K (999), 22K (916), 21K (875), 18K (750), 14K (585), 9K (375)",
        },
        {
            "value": "silver_hallmark",
            "label": "Silver Hallmark",
            "description": "Fine Silver (999), Sterling Silver (925), Coin Silver (900), 800",
        },
        {
            "value": "pressure_cooker",
            "label": "Domestic Pressure Cookers",
            "description": "IS 2347 - Domestic Pressure Cookers (Mandatory ISI)",
        },
        {
            "value": "helmet",
            "label": "Two-Wheeler Helmets",
            "description": "IS 4151 - Protective Helmets for Two Wheeler Riders",
        },
        {
            "value": "packaged_water",
            "label": "Packaged Drinking Water",
            "description": "IS 14543 / IS 13428 - Packaged Natural Mineral & Drinking Water",
        },
        {
            "value": "led_lighting",
            "label": "LED & Electronics Lighting",
            "description": "IS 16102 (Part 1/2) - Self-ballasted LED Lamps",
        },
        {
            "value": "metal_grade",
            "label": "Steel & Metal Grades",
            "description": "SS304, SS316, Fe 500 TMT Steel Bars",
        },
    ]
