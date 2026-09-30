"""Safety and security module for Parakh.

Includes:
- Prompt injection detection
- Input sanitization
- PII masking (Aadhaar, PAN, phone numbers, email)
"""

import re
from typing import Tuple

# Common prompt injection / jailbreak patterns
INJECTION_PATTERNS = [
    r"(?i)\bignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules|commands)\b",
    r"(?i)\bdisregard\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)\b",
    r"(?i)\byou\s+are\s+now\s+(in\s+)?(dan|developer|jailbreak|unrestricted)\s+mode\b",
    r"(?i)\breveal\s+(your\s+)?(system\s+prompt|instructions|secret\s+key|api\s+key)\b",
    r"(?i)\boutput\s+(the\s+)?(system\s+prompt|initial\s+prompt|developer\s+instructions)\b",
    r"(?i)\bbypass\s+(all\s+)?(filters|safety|guardrails|constraints)\b",
    r"(?i)\bact\s+as\s+an\s+unfiltered\b",
    r"(?i)\bdo\s+anything\s+now\b",
    r"(?i)\bpretend\s+you\s+have\s+no\s+(rules|restrictions|limits)\b",
]

# PII Regex patterns for Indian context
AADHAAR_REGEX = r"\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b"
PAN_REGEX = r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b"
EMAIL_REGEX = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
PHONE_REGEX = r"(\+91[\-\s]?)?[6-9]\d{9}\b"


def sanitize_input(text: str, max_length: int = 2000) -> str:
    """
    Sanitize user input:
    - Strip null bytes and non-printable control characters (preserve newlines/tabs)
    - Remove HTML / script tags
    - Truncate to maximum allowed length
    - Normalize excessive whitespace
    """
    if not text:
        return ""

    # Remove null bytes and non-printable control characters
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)

    # Strip HTML tags
    text = re.sub(r"<[^>]*>", "", text)

    # Normalize excessive whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Cap length
    if len(text) > max_length:
        text = text[:max_length]

    return text


def is_prompt_injection(text: str) -> Tuple[bool, str]:
    """
    Check if the input text contains known prompt injection attempts.
    Returns (is_injection, matched_pattern_reason).
    """
    if not text:
        return False, ""

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text):
            return True, f"Matched injection pattern: {pattern}"

    return False, ""


def mask_pii(text: str) -> str:
    """
    Redact personally identifiable information (PII) from strings:
    - Aadhaar numbers -> [REDACTED-AADHAAR]
    - PAN card numbers -> [REDACTED-PAN]
    - Indian Mobile Numbers -> [REDACTED-PHONE]
    - Emails -> [REDACTED-EMAIL]
    """
    if not text:
        return ""

    masked = text
    masked = re.sub(EMAIL_REGEX, "[REDACTED-EMAIL]", masked)
    masked = re.sub(AADHAAR_REGEX, "[REDACTED-AADHAAR]", masked)
    masked = re.sub(PAN_REGEX, "[REDACTED-PAN]", masked)
    masked = re.sub(PHONE_REGEX, "[REDACTED-PHONE]", masked)

    return masked
