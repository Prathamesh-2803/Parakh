"""Pydantic schemas for the image-based product scan endpoint."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class MaterialCodeMatch(BaseModel):
    """Result of matching an OCR-extracted stamped code against reference material codes."""

    code: str = Field(..., description="Matched code, e.g. '7', '916', 'SS304'")
    label: str = Field(..., description="Label or grade, e.g. 'PC', '22K', 'Grade 304'")
    category: str = Field(..., description="Category, e.g. 'plastic_resin_code', 'gold_hallmark'")
    material_name: str = Field(..., description="Human-readable material name")
    common_uses: str | None = Field(default=None, description="Common uses of this material")
    notes: str | None = Field(default=None, description="Regulatory and safety notes")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Match confidence score")
    raw_matched_text: str = Field(..., description="The raw OCR text fragment matched")
    detected_license: str | None = Field(default=None, description="BIS license number if found in OCR text")
    detected_huid: str | None = Field(default=None, description="Gold HUID if found in OCR text")


class ScanResult(BaseModel):
    """Result from vision-based product identification."""

    product_description: str = Field(
        ..., description="Short plain description of what the product is"
    )
    detected_text: str = Field(
        ..., description="Any readable text/marks on the image (brand, license, etc.)"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in the product identification"
    )
    identification_method: str = Field(
        default="ai_vision",
        description="Method used: 'ocr_code_match', 'ai_vision', or 'manual_required'"
    )
    matched_code: str | None = Field(
        default=None,
        description="Raw or formatted stamped code if identified via OCR"
    )
    material_info: dict[str, Any] | None = Field(
        default=None,
        description="Detailed material code info if matched"
    )
    failure_reason: str | None = Field(
        default=None,
        description="Specific reason if identification failed: 'no_text_detected', 'text_detected_no_match', 'ocr_unavailable'"
    )


class MarkVerificationResult(BaseModel):
    """Result from license/HUID verification (if applicable)."""

    license: str | None = Field(
        default=None, description="License number if detected and verified"
    )
    huid: str | None = Field(
        default=None, description="HUID if detected and verified"
    )
    license_valid: bool | None = Field(
        default=None, description="Whether the license is valid (if checked)"
    )
    huid_valid: bool | None = Field(
        default=None, description="Whether the HUID is valid (if checked)"
    )


class ScanResponse(BaseModel):
    """Response from the POST /scan endpoint."""

    product_description: str = Field(
        ..., description="Product description from vision model or material code match"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in the product identification"
    )
    identification_method: str = Field(
        default="ai_vision",
        description="Method used: 'ocr_code_match', 'ai_vision', or 'manual_required'"
    )
    matched_code: str | None = Field(
        default=None,
        description="Raw or formatted stamped code if identified via OCR"
    )
    material_info: dict[str, Any] | None = Field(
        default=None,
        description="Detailed material code info if matched"
    )
    manual_options: list[dict[str, Any]] | None = Field(
        default=None,
        description="List of available material codes/categories when manual selection is required"
    )
    failure_reason: str | None = Field(
        default=None,
        description="Specific internal failure reason: 'no_text_detected', 'text_detected_no_match', 'ocr_unavailable'"
    )
    recommend_result: dict[str, Any] = Field(
        ..., description="Full compliance recommendation result"
    )
    mark_verification: MarkVerificationResult | None = Field(
        default=None, description="Verification result if license/HUID detected"
    )
    message: str | None = Field(
        default=None, description="Optional informational or guidance message"
    )