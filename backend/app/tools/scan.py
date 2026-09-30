"""Product identification from image using OCR-first pipeline with Custom Classifier + Gemini Vision fallback."""

import hashlib
import logging
import os
import re
from typing import Tuple, Optional

from backend.app.config import settings
from backend.app.core.llm import generate_vision
from backend.app.schemas.scan import ScanResult, MarkVerificationResult, MaterialCodeMatch
from backend.app.tools.ocr_identify import extract_text_from_image, match_material_code, LICENSE_PATTERN, HUID_PATTERN
from backend.app.tools.verify import verify_license, verify_huid
from backend.app.tools.product_classifier import classify_product_image, ProductClassifierInference

logger = logging.getLogger("parakh.scan")


def is_mock_mode() -> bool:
    """Check if mock LLM mode is active."""
    return os.getenv("MOCK_LLM", str(settings.MOCK_LLM)).lower() in ("true", "1", "yes")


def _hash_image(image_bytes: bytes) -> str:
    """Compute SHA-256 hash of image bytes."""
    return hashlib.sha256(image_bytes).hexdigest()


async def identify_product_from_image(
    image_bytes: bytes,
    mime_type: str,
    language: str = "en",
) -> Tuple[ScanResult, MarkVerificationResult | None]:
    """
    Identify product from image using OCR-first pipeline with Gemini Vision fallback.
    If detected text contains license/HUID patterns, runs verification.

    Args:
        image_bytes: Raw image bytes
        mime_type: MIME type of image (e.g., 'image/jpeg')
        language: Language code for product description (default: 'en')

    Returns:
        Tuple of (ScanResult, MarkVerificationResult | None)
    """
    logger.info(
        f"identify_product_from_image called with {len(image_bytes)} bytes, mime_type={mime_type}"
    )

    # Step 1: Multi-pass OCR extraction & material code / standard matching
    full_text = extract_text_from_image(image_bytes)
    match = match_material_code(full_text)

    logger.debug(f"OCR extracted text: {full_text!r}")
    logger.debug(f"OCR match result: {match}")

    if match:
        # Build ScanResult from OCR match
        product_description = match.material_name
        detected_text = full_text
        confidence = match.confidence
        scan_result = ScanResult(
            product_description=product_description,
            detected_text=detected_text,
            confidence=confidence,
            identification_method="ocr_code_match",
            matched_code=match.code,
            material_info=match.model_dump(),
            failure_reason=None,
        )

        # Run verification on any detected license/HUID from the match
        mark_verification = None
        license_valid = None
        huid_valid = None
        if match.detected_license:
            lic_res = await verify_license(license_no=match.detected_license)
            license_valid = lic_res.get("is_valid", False)
            logger.debug(f"License verification result: {lic_res}")
        if match.detected_huid:
            hid_res = await verify_huid(huid=match.detected_huid)
            huid_valid = hid_res.get("is_valid", False)
            logger.debug(f"HUID verification result: {hid_res}")

        if license_valid is not None or huid_valid is not None:
            mark_verification = MarkVerificationResult(
                license=match.detected_license if license_valid is not None else None,
                license_valid=license_valid,
                huid=match.detected_huid if huid_valid is not None else None,
                huid_valid=huid_valid,
            )

        logger.info(f"OCR identification successful: {product_description} (confidence: {confidence})")
        return scan_result, mark_verification

    # Determine failure reason for OCR
    if not full_text or not full_text.strip():
        ocr_failure_reason = "no_text_detected"
        desc = "No printed markings or standard codes were detected. Manual selection required."
    else:
        ocr_failure_reason = "text_detected_no_match"
        desc = "Text detected but no matching BIS standard or material code found. Manual selection required."

    # Step 2: No OCR match - try Custom Visual Classifier
    logger.info("Trying custom visual classifier for product identification")
    try:
        cls_result = classify_product_image(image_bytes)
        cls_conf = cls_result.get("confidence", 0.0)
        cls_class = cls_result.get("class", "other")
        
        if cls_conf >= 0.15 and cls_class != "other":
            # Good visual classification result
            scan_result = ScanResult(
                product_description=f"{cls_result['description']} (Visual AI: {cls_result['standard']})",
                detected_text=full_text,
                confidence=cls_conf,
                identification_method="visual_classifier",
                failure_reason=None,
            )
            logger.info(f"Visual classifier: {cls_result['description']} (confidence: {cls_conf:.2f})")
            
            # Verify any license/HUID from OCR text even if classifier succeeded
            mark_verification = None
            detected_text_upper = full_text.upper()
            license_match = LICENSE_PATTERN.search(detected_text_upper)
            if license_match:
                lic_digits = license_match.group(1)
                license_formatted = f"CM/L-{lic_digits}"
                lic_res = await verify_license(license_no=license_formatted)
                mark_verification = MarkVerificationResult(
                    license=license_formatted,
                    license_valid=lic_res.get("is_valid", False),
                )
            huid_match = HUID_PATTERN.search(detected_text_upper)
            if huid_match:
                huid_6char = huid_match.group(1)
                huid_formatted = f"HUID-{huid_6char[:2]}-{huid_6char[2:]}"
                huid_res = await verify_huid(huid=huid_6char)
                if mark_verification is None:
                    mark_verification = MarkVerificationResult()
                mark_verification.huid = huid_formatted
                mark_verification.huid_valid = huid_res.get("is_valid", False)
            
            return scan_result, mark_verification
        else:
            logger.info(f"Visual classifier low confidence ({cls_conf:.2f}) or 'other' class, continuing...")
    except Exception as exc:
        logger.warning(f"Visual classifier error ({exc}), continuing to next step...")

    # Step 3: Check if we are in mock mode
    if is_mock_mode():
        scan_result = ScanResult(
            product_description=desc,
            detected_text=full_text,
            confidence=0.0,
            identification_method="manual_required",
            failure_reason=ocr_failure_reason,
        )
        logger.info(f"Mock mode active & OCR/classifier found no match: {ocr_failure_reason}")
        return scan_result, None

    # Step 4: Fall back to Gemini Vision
    logger.info("Falling back to Gemini Vision for product identification")
    prompt = """
    Analyze this image of a product, its packaging, or label.
    Return a JSON object with exactly these fields:
    - product_description: a short plain description of what the product is (e.g., "LED bulb", "steel helmet", "cement bag")
    - detected_text: any readable text/marks on the image (brand name, ISI mark, license number, HUID, CRS registration, batch/model number). If no text is visible, return an empty string.
    - confidence: a float between 0.0 and 1.0 indicating how confident you are that this is a product image and the description is correct. If the image is unclear, not a product, or you cannot confidently identify the product, set confidence below 0.3.

    Be concise and accurate. Do not add extra fields.
    """.strip()

    try:
        llm_result = await generate_vision(prompt=prompt, image_bytes=image_bytes, mime_type=mime_type)
        llm_text = llm_result.get("text", "")
        logger.debug(f"Gemini Vision raw response: {llm_text!r}")

        # Parse JSON from LLM output
        import json
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", llm_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = llm_text

        data = json.loads(json_str)
        conf = float(data.get("confidence", 0.0))
        scan_result = ScanResult(
            product_description=data.get("product_description", "Unable to identify product"),
            detected_text=data.get("detected_text", ""),
            confidence=conf,
            identification_method="ai_vision" if conf >= 0.3 else "manual_required",
            failure_reason=None if conf >= 0.3 else ocr_failure_reason,
        )
        logger.info(f"Gemini Vision identification: {scan_result.product_description} (confidence: {conf})")
    except Exception as exc:
        logger.warning(f"Gemini Vision processing failed/unavailable ({exc}), degrading gracefully to manual fallback")
        scan_result = ScanResult(
            product_description="Unable to identify product from image. Manual selection required.",
            detected_text=full_text,
            confidence=0.0,
            identification_method="manual_required",
            failure_reason="vision_unavailable" if ocr_failure_reason == "no_text_detected" else ocr_failure_reason,
        )

    # Extract license/HUID from detected_text and verify if found
    mark_verification = None
    detected_text_upper = scan_result.detected_text.upper()

    license_match = LICENSE_PATTERN.search(detected_text_upper)
    if license_match:
        lic_digits = license_match.group(1)
        license_formatted = f"CM/L-{lic_digits}"
        logger.info(f"Detected license-like text: {license_formatted}")
        license_res = await verify_license(license_no=license_formatted)
        mark_verification = MarkVerificationResult(
            license=license_formatted,
            license_valid=license_res.get("is_valid", False),
        )

    huid_match = HUID_PATTERN.search(detected_text_upper)
    if huid_match:
        huid_6char = huid_match.group(1)
        huid_formatted = f"HUID-{huid_6char[:2]}-{huid_6char[2:]}"
        logger.info(f"Detected HUID-like text: {huid_formatted}")
        huid_res = await verify_huid(huid=huid_6char)
        if mark_verification is None:
            mark_verification = MarkVerificationResult()
        mark_verification.huid = huid_formatted
        mark_verification.huid_valid = huid_res.get("is_valid", False)

    return scan_result, mark_verification
