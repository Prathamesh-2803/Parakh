"""Verification API endpoints for license and HUID verification."""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from backend.app.tools.verify import verify_license, verify_huid

router = APIRouter(tags=["verification"])
logger = logging.getLogger("parakh.verify")


class VerifyLicenseRequest(BaseModel):
    license_no: str = Field(..., min_length=1, json_schema_extra={"example": "CM/L-1234567"})


class VerifyLicenseResponse(BaseModel):
    license_no: str
    status: str
    message: str
    details: Optional[dict] = None


class VerifyHuidRequest(BaseModel):
    huid: str = Field(..., min_length=1, json_schema_extra={"example": "12345678901234"})


class VerifyHuidResponse(BaseModel):
    huid: str
    status: str
    message: str
    details: Optional[dict] = None


@router.post("/verify/license", response_model=VerifyLicenseResponse)
async def license_verification(body: VerifyLicenseRequest) -> VerifyLicenseResponse:
    """
    POST /verify/license: Verify a BIS license number (CM/L).
    """
    logger.info(f"License verification request for: {body.license_no}")
    try:
        result = await verify_license(body.license_no)
        return VerifyLicenseResponse(
            license_no=result["license_no"],
            status=result["status"],
            message=result["message"],
            details=result.get("details")
        )
    except Exception as e:
        logger.error(f"License verification failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify/huid", response_model=VerifyHuidResponse)
async def huid_verification(body: VerifyHuidRequest) -> VerifyHuidResponse:
    """
    POST /verify/huid: Verify a Hallmark Unique ID (HUID).
    """
    logger.info(f"HUID verification request for: {body.huid}")
    try:
        result = await verify_huid(body.huid)
        return VerifyHuidResponse(
            huid=result["huid"],
            status=result["status"],
            message=result["message"],
            details=result.get("details")
        )
    except Exception as e:
        logger.error(f"HUID verification failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
