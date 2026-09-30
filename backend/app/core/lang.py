"""Language detection and multilingual utilities for Indian languages."""

import logging
import re
from typing import Optional

try:
    from langdetect import detect
except ImportError:
    def detect(text: str) -> str:
        return "en"

from backend.app.config import settings

logger = logging.getLogger("parakh.lang")

# Common Marathi markers to distinguish Devanagari Marathi from Hindi
MARATHI_MARKERS = [
    "आहे", "आहेत", "नाही", "नाहीत", "करावे", "साठी", "यांची", "झाले", "झाली",
    "होते", "होती", "करणे", "येथे", "कसे", "कोणते", "प्रमाणपत्र", "परवाना",
    "तक्रार", "मिळेल", "लागेल", "करावी", "असावे", "दिले", "माहिती", "दुचाकी",
    "चालकांसाठी", "बनवतो", "आम्ही", "कशी", "काय", "मधील", "च्या", "चे", "तयार",
    "हेल्मेट", "हॉलमार्किंग"
]

# Common Hindi markers
HINDI_MARKERS = [
    "है", "हैं", "नहीं", "करना", "के लिए", "होगा", "होगी", "कहाँ", "कैसे",
    "कौन", "कौन सा", "कौन सी", "प्राप्त", "लाइसेंस", "प्रमाणन", "शिकायत", "मिलेगा",
    "चाहिए", "दीजिये", "बताइए", "जानकारी", "दोपहिया", "बनाता", "हम", "मैं",
    "बनाते", "हेलमेट", "हॉलमार्क"
]


def _detect_by_script(text: str) -> Optional[str]:
    """Fast detection based on Unicode script blocks and characteristic vocabulary."""
    devanagari_count = len(re.findall(r"[ऀ-ॿ]", text))
    tamil_count = len(re.findall(r"[஀-௿]", text))
    telugu_count = len(re.findall(r"[ఀ-౿]", text))
    bengali_count = len(re.findall(r"[ঀ-৿]", text))

    total_chars = len(text.strip())
    if total_chars == 0:
        return settings.DEFAULT_LANGUAGE

    # Tamil script
    if tamil_count > 1 or (tamil_count / max(total_chars, 1) > 0.1):
        return "ta"

    # Telugu script
    if telugu_count > 1 or (telugu_count / max(total_chars, 1) > 0.1):
        return "te"

    # Bengali script
    if bengali_count > 1 or (bengali_count / max(total_chars, 1) > 0.1):
        return "bn"

    # Devanagari script (Hindi vs Marathi)
    if devanagari_count > 2 or (devanagari_count / max(total_chars, 1) > 0.1):
        # Character 'ळ' (U+0933) is unique to Marathi in Devanagari
        if "ळ" in text:
            return "mr"

        # Count exclusive markers to break ties
        marathi_only = sum(1 for marker in MARATHI_MARKERS if marker in text and marker not in HINDI_MARKERS)
        hindi_only = sum(1 for marker in HINDI_MARKERS if marker in text and marker not in MARATHI_MARKERS)

        if marathi_only > hindi_only:
            return "mr"
        if hindi_only > marathi_only:
            return "hi"

        # Fallback to total hits (including shared markers)
        marathi_hits = sum(1 for marker in MARATHI_MARKERS if marker in text)
        hindi_hits = sum(1 for marker in HINDI_MARKERS if marker in text)

        if marathi_hits > hindi_hits:
            return "mr"
        return "hi"

    return None


def detect_language(text: str, default: Optional[str] = None) -> str:
    """
    Detect language of input text with priority for Indian languages.
    Returns ISO 639-1 code (e.g. 'en', 'hi', 'mr', 'ta').
    """
    if not text or not text.strip():
        return default or settings.DEFAULT_LANGUAGE

    # 1. Fast script heuristic
    script_lang = _detect_by_script(text)
    if script_lang:
        logger.debug(f"Language detected by script: {script_lang}")
        return script_lang

    # 2. langdetect fallback
    try:
        detected = detect(text)
        if detected in settings.SUPPORTED_LANGUAGES:
            logger.debug(f"Language detected by langdetect: {detected}")
            return detected
        elif detected == "mr":
            return "mr"
        elif detected in ["hi", "ne"]:  # Nepali often shares Devanagari patterns
            return "hi"
    except Exception as e:
        logger.debug(f"langdetect failed or threw error: {e}")

    # 3. Default fallback
    return default or settings.DEFAULT_LANGUAGE


def get_language_name(lang_code: str) -> str:
    """Return human readable language name."""
    names = {
        "en": "English",
        "hi": "Hindi (हिन्दी)",
        "mr": "Marathi (मराठी)",
        "ta": "Tamil (தமிழ்)",
        "te": "Telugu (తెలుగు)",
        "bn": "Bengali (বাংলা)",
    }
    return names.get(lang_code, "English")
