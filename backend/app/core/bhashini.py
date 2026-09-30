"""Bhashini (National Language Translation Mission) adapter behind feature flag."""

import logging
from typing import Dict, Any, Optional
import httpx

from backend.app.config import settings

logger = logging.getLogger("parakh.bhashini")


class BhashiniClient:
    """
    Client for Bhashini (NLTM / Dhruva) API for Indian language translation and speech.
    Operates behind ENABLE_BHASHINI feature flag with graceful fallback.
    """

    def __init__(self):
        self.enabled = settings.ENABLE_BHASHINI
        self.user_id = settings.BHASHINI_USER_ID
        self.api_key = settings.BHASHINI_API_KEY
        self.pipeline_id = settings.BHASHINI_PIPELINE_ID
        self.inference_url = settings.BHASHINI_INFERENCE_URL

    def is_configured(self) -> bool:
        """Check if Bhashini credentials and feature flag are active."""
        return bool(self.enabled and self.api_key and self.user_id)

    async def translate_text(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> str:
        """
        Translate text from source_lang to target_lang using Bhashini NMT.
        Falls back to original text if Bhashini is disabled or request fails.
        """
        if not self.is_configured() or source_lang == target_lang:
            return text

        logger.info(f"Translating via Bhashini from {source_lang} to {target_lang}")
        try:
            payload = {
                "pipelineTasks": [
                    {
                        "taskType": "translation",
                        "config": {
                            "language": {
                                "sourceLanguage": source_lang,
                                "targetLanguage": target_lang,
                            }
                        },
                    }
                ],
                "inputData": {
                    "input": [{"source": text}]
                },
            }

            headers = {
                "Content-Type": "application/json",
                "userID": self.user_id,
                "ulcaApiKey": self.api_key,
                "Authorization": self.api_key,
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.inference_url,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

                translated = (
                    data.get("pipelineResponse", [{}])[0]
                    .get("output", [{}])[0]
                    .get("target")
                )
                if translated:
                    return translated

        except Exception as e:
            logger.warning(f"Bhashini translation failed: {e}. Falling back to original text.")

        return text


# Global instance
bhashini_client = BhashiniClient()
