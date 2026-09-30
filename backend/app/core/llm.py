"""LLM gateway — one Gemini call per question, Groq fallback, mock mode."""

import asyncio
import json
import logging
import re
import time
from typing import Any
import base64

import httpx

from backend.app.config import settings

logger = logging.getLogger("parakh.llm")


# ---------------------------------------------------------------------------
# Mock provider enhancements — contextual follow-up Q&A for demo mode
# ---------------------------------------------------------------------------

# Knowledge base for common follow-up questions in mock mode
FOLLOW_UP_KNOWLEDGE_BASE = {
    # Helmets (Two-Wheeler)
    "helmet": {
        "IS 4151": {
            "Which testing labs test helmets in India?": "BIS-recognized labs for helmet testing include: Northern Regional Testing Centre (Chandigarh), Southern Regional Testing Centre (Bengaluru), Western Regional Testing Centre (Mumbai), and Eastern Regional Testing Centre (Kolkata). All labs must have NABL accreditation for IS 4151 testing.",
            "What is the validity period of helmet certification?": "ISI certification for helmets under IS 4151 is valid for 1 year, after which renewal requires factory audit and sample testing.",
            "Are helmets mandatory for all two-wheeler riders?": "Yes, as per Central Motor Vehicles Rule 138(4)(f) and IS 4151, wearing BIS-certified helmets is mandatory for all two-wheeler riders in India.",
            "What are the key tests performed on helmets?": "Key tests include: impact absorption, penetration resistance, retention system strength, field of vision, and chin strap effectiveness as per IS 4151:2015.",
            "How can I verify if a helmet has genuine ISI mark?": "Check for 7-digit CM/L number beneath ISI mark, verify on BIS website (www.bis.gov.in) using license number, and look for IS 4151:2015 certification details."
        }
    },
    # LED Lamps
    "led_lamp": {
        "IS 16102": {
            "What testing labs certify LED lamps in India?": "BIS-recognized labs for LED lamp testing include: ERTL (East), ERTL (North), ERTL (West), ERTL (South), and CPRI units. Labs must have NABL accreditation for photometric and safety testing per IS 16102.",
            "Are LED lamps mandatory for all applications?": "LED lamps for general lighting services are mandatory under IS 16102 (Part 1) as per Quality Control Order for LED Lamps 2017. Special purpose LEDs may be exempt.",
            "What is the energy efficiency requirement for LED lamps?": "LED lamps must meet minimum efficacy standards (lumens/watt) as per IS 16102:2012, with specific values depending on color temperature and wattage rating.",
            "How does BIS ensure LED lamp quality and safety?": "BIS certification involves factory audit, sample testing for photometric performance, safety (temperature rise, protection against electric shock), and endurance testing before granting ISI mark.",
            "Can LED lamps be used in enclosed fixtures?": "Only LED lamps specifically rated for enclosed fixtures (as per manufacturer's instructions and IS 16102) should be used in enclosed spaces to prevent overheating and premature failure."
        }
    },
    # Pressure Cookers
    "pressure_cooker": {
        "IS 2347": {
            "Which labs test pressure cookers in India?": "BIS-recognized labs for pressure cooker testing include: Regional Testing Centres (Chennai, Mumbai, Kolkata, New Delhi), and approved private labs with NABL accreditation for mechanical and thermal testing per IS 2347.",
            "What safety features are mandatory in pressure cookers?": "Mandatory safety features include: pressure release valve, locking indicator, gasket release system, and minimum two independent safety mechanisms as per IS 2347:2009.",
            "Is ISI mark mandatory for all pressure cookers sold in India?": "Yes, as per Domestic Pressure Cooker Order 2020, it is mandatory for all domestic pressure cookers to bear ISI mark under IS 2347 before being sold or distributed in India.",
            "What tests are conducted on pressure cookers for certification?": "Tests include: hydraulic pressure test, blow-off valve testing, gasket permeability test, handle strength test, and thermal shock resistance as per IS 2347:2009.",
            "How often should pressure cooker safety valves be replaced?": "Safety valves should be inspected annually and replaced every 2-3 years or immediately if damaged, corroded, or not functioning properly as per manufacturer guidelines."
        }
    },
    # Gold Jewelry
    "gold_jewelry": {
        "IS 1417": {
            "Where can I get gold jewelry hallmarked in India?": "Hallmarking is done at BIS-recognized Assaying and Hallmarking Centres (AHCs). There are over 900 AHCs across India, locatable via the BIS website's 'Find AHC' tool.",
            "What does the 6-digit HUID on gold jewelry mean?": "HUID (Hallmark Unique Identification) is a 6-digit alphanumeric code uniquely identifying each hallmarked jewelry item, enabling traceability to the AHC and batch details via BIS portal as per IS 1417.",
            "Is hallmarking mandatory for all gold jewelry in India?": "Yes, as per Hallmarking Order 2020 under IS 1417, hallmarking is mandatory for all gold jewelry and items above 2 grams weight.",
            "What purity standards are recognized for gold jewelry?": "Recognized purity standards under IS 1417:2016 include: 24K (999), 23K (958), 22K (916), 21K (875), 20K (833), 18K (750), 14K (585).",
            "How can I verify the authenticity of a hallmarked gold item?": "Verify using the HUID on BIS website (www.bis.gov.in) or mKavach app, which shows AHC details, purity, weight, and hallmarking date."
        }
    },
    # Packaged Drinking Water
    "packaged_water": {
        "IS 14543": {
            "Which labs test packaged drinking water in India?": "BIS-recognized labs for water testing include: Regional Food & Water Testing Centres (Chandigarh, Kolkata, Chennai, Mumbai), and NABL-accredited labs specializing in chemical and microbiological analysis per IS 14543.",
            "Is ISI mark mandatory for all packaged drinking water?": "Yes, as per FSSAI/BIS Mandatory Certification for Drinking Water, all packaged drinking water (except mineral water) must bear ISI mark under IS 14543 before sale in India.",
            "What tests are conducted on packaged drinking water for certification?": "Tests include: microbiological (E. coli, coliforms), chemical (heavy metals, pesticides, nitrate), physical (turbidity, color, odor), and radiological parameters as per IS 14543:2004.",
            "What is the difference between packaged drinking water and mineral water?": "Packaged drinking water (IS 14543) is treated potable water, while natural mineral water (IS 13428) is sourced from protected underground reserves with stable mineral composition and minimal treatment.",
            "How often must packaged water plants be inspected for BIS certification?": "BIS certification requires factory audit every year and sample testing every 6 months for continued validity of ISI license under IS 14543."
        }
    }
}


# ---------------------------------------------------------------------------
# Mock provider (MOCK_LLM=true) — zero cost, always works
# ---------------------------------------------------------------------------

async def _mock_generate(prompt: str, context: str = "") -> dict[str, Any]:
    """Return structured JSON mock response — used for testing and dev."""
    logger.info("mock_generate called (MOCK_LLM=true)")

    # Handle language-specific responses first
    if "Respond in fluent, natural Hindi" in prompt or "Respond in Hindi" in prompt:
        mock_json = json.dumps({
            "answer": "यह एक मॉक उत्तर है (MOCK_LLM=true)। भारत में लागू मानक IS 4151 और IS 1239 हैं।",
            "citations": [{"source": "IS 4151", "section": "Clause 1", "url": "https://www.bis.gov.in/"}],
            "confidence": 0.9,
            "follow_up_suggestions": ["आवेदन प्रक्रिया क्या है?", "फीस कितनी है?"]
        }, ensure_ascii=False)
    elif "Respond in fluent, natural Marathi" in prompt or "Respond in Marathi" in prompt:
        mock_json = json.dumps({
            "answer": "हे एक मॉक उत्तर आहे (MOCK_LLM=true). लागू मानक IS 4151 आणि IS 1239 आहे.",
            "citations": [{"source": "IS 4151", "section": "Clause 1", "url": "https://www.bis.gov.in/"}],
            "confidence": 0.9,
            "follow_up_suggestions": ["अर्ज कसा करावा?", "शुल्क किती आहे?"]
        }, ensure_ascii=False)
    elif "Respond in fluent, natural Tamil" in prompt or "Respond in Tamil" in prompt:
        mock_json = json.dumps({
            "answer": "இது ஒரு மாதிரி பதில் (MOCK_LLM=true). பொருந்தக்கூடிய தரநிலைகள் IS 4151 மற்றும் IS 1239.",
            "citations": [{"source": "IS 4151", "section": "Clause 1", "url": "https://www.bis.gov.in/"}],
            "confidence": 0.9,
            "follow_up_suggestions": ["விண்ணப்பிப்பது எப்படி?", "கட்டணம் எவ்வளவு?"]
        }, ensure_ascii=False)
    else:
        # Check for contextual follow-up in English
        follow_up_answer = _find_contextual_follow_up(prompt, context)
        logger.debug(f"mock LLM: follow_up_answer={follow_up_answer[:50] if follow_up_answer else None}")

        if follow_up_answer:
            mock_json = json.dumps({
                "answer": follow_up_answer,
                "citations": [{"source": "IS 4151", "section": "Clause 1", "url": "https://www.bis.gov.in/"}],
                "confidence": 0.9,
                "follow_up_suggestions": ["What other standards exist?", "How do I apply for ISI?"]
            })
        else:
            # Generate response from context for first-time questions
            # Extract key info from context to build a grounded answer
            logger.debug("mock LLM: calling _generate_contextual_answer")
            context_answer = _generate_contextual_answer(prompt, context)
            logger.debug(f"mock LLM: context_answer={context_answer[:100] if context_answer else None}")
            if context_answer:
                mock_json = json.dumps({
                    "answer": context_answer,
                    "citations": [{"source": "SQL Database", "section": "Product Category", "url": "https://www.bis.gov.in/"}],
                    "confidence": 0.85,
                    "follow_up_suggestions": ["Which testing labs test helmets in India?", "How do I apply for ISI license?", "How to verify ISI mark?"]
                })
            else:
                # Default mock response for new queries
                mock_json = json.dumps({
                    "answer": "This is a mock LLM response (MOCK_LLM=true). In production this would be a grounded answer from Gemini.",
                    "citations": [{"source": "IS 4151", "section": "Clause 1", "url": "https://www.bis.gov.in/"}],
                    "confidence": 0.9,
                    "follow_up_suggestions": ["What other standards exist?", "How do I apply for ISI?"]
                })

    return {
        "text": mock_json,
        "provider": "mock",
        "model": "mock",
        "usage": {"prompt_tokens": 0, "completion_tokens": 0},
    }


def _find_contextual_follow_up(prompt: str, context: str) -> str | None:
    """
    Find a contextual follow-up answer based on prompt and conversation history.
    Returns answer string if match found, None otherwise.
    """
    # Extract clean question if prompt contains system wrapping
    clean_q = prompt
    if "USER QUESTION:" in prompt:
        parts = prompt.split("USER QUESTION:")[1]
        clean_q = parts.split("LANGUAGE INSTRUCTION:")[0].split("OUTPUT")[0].strip()

    # Extract potential topic from context AND prompt (which contains conversation history)
    topic_key = _extract_topic_from_context(context)
    if not topic_key:
        topic_key = _extract_topic_from_context(prompt)
    if not topic_key:
        return None

    # Check if we have knowledge base for this topic
    if topic_key not in FOLLOW_UP_KNOWLEDGE_BASE:
        return None

    topic_kb = FOLLOW_UP_KNOWLEDGE_BASE[topic_key]

    # Try to extract standard from context or prompt
    standard_match = _extract_standard_from_context(context)
    if not standard_match:
        standard_match = _extract_standard_from_context(prompt)

    # We'll try to match against the specific standard if found, otherwise try all standards in the topic
    standards_to_try = []
    if standard_match and standard_match in topic_kb:
        standards_to_try.append(standard_match)
    else:
        # If no standard found or not in KB, try all standards for this topic
        standards_to_try.extend(topic_kb.keys())

    # Try matching against clean_q first, then prompt
    for q_candidate in [clean_q, prompt]:
        q_lower = q_candidate.lower().strip()
        for standard in standards_to_try:
            standard_kb = topic_kb[standard]

            # Look for exact question match
            for question, answer in standard_kb.items():
                if _questions_match(q_lower, question.lower()):
                    return answer

            # If no exact match, check for partial matches
            for question, answer in standard_kb.items():
                if _partial_question_match(q_lower, question.lower()):
                    return answer

    return None

    # Normalize prompt for matching
    prompt_lower = prompt.lower().strip()

    # Check if we have knowledge base for this topic
    if topic_key not in FOLLOW_UP_KNOWLEDGE_BASE:
        return None

    topic_kb = FOLLOW_UP_KNOWLEDGE_BASE[topic_key]

    # Try to extract standard from context
    standard_match = _extract_standard_from_context(context)

    # We'll try to match against the specific standard if found, otherwise try all standards in the topic
    standards_to_try = []
    if standard_match and standard_match in topic_kb:
        standards_to_try.append(standard_match)
    else:
        # If no standard found or not in KB, try all standards for this topic
        standards_to_try.extend(topic_kb.keys())

    # Now try each standard's knowledge base
    for standard in standards_to_try:
        standard_kb = topic_kb[standard]

        # Look for exact question match
        for question, answer in standard_kb.items():
            if _questions_match(prompt_lower, question.lower()):
                return answer

        # If no exact match, check for partial matches
        for question, answer in standard_kb.items():
            if _partial_question_match(prompt_lower, question.lower()):
                return answer

    return None


def _extract_topic_from_context(context: str) -> str | None:
    """Extract likely product topic from conversation context."""
    if not context:
        return None

    context_lower = context.lower()

    # Map context keywords to topic keys
    topic_indicators = {
        "helmet": ["helmet", "headgear", "two wheeler", "bike", "motorcycle", "is 4151"],
        "led_lamp": ["led", "lamp", "bulb", "lighting", "is 16102"],
        "pressure_cooker": ["pressure cooker", "cooker", "is 2347"],
        "gold_jewelry": ["gold", "jewelry", "jewellery", "ornament", "is 1417"],
        "packaged_water": ["water", "drinking water", "packaged water", "is 14543"]
    }

    for topic, indicators in topic_indicators.items():
        if any(indicator in context_lower for indicator in indicators):
            return topic

    return None


def _extract_standard_from_context(context: str) -> str | None:
    """Extract IS standard number from context if present."""
    if not context:
        return None

    # Look for patterns like IS 4151, IS:16102, IS 2347:2009, etc.
    is_pattern = r'IS\s*[\d:]+\s*[\d]*'
    matches = re.findall(is_pattern, context, re.IGNORECASE)

    if matches:
        # Clean up the match (remove extra spaces, colons) and keep the full IS format
        standard = re.sub(r'[:\s]+', ' ', matches[0]).strip()
        return standard

    return None


def _questions_match(prompt: str, question: str) -> bool:
    """Check if prompt matches question exactly (after normalization)."""
    # Remove punctuation, convert to lowercase, and extra spaces for comparison
    prompt_clean = re.sub(r'[^\w\s]', '', prompt).lower().strip()
    question_clean = re.sub(r'[^\w\s]', '', question).lower().strip()
    return prompt_clean == question_clean


def _partial_question_match(prompt: str, question: str) -> bool:
    """Check if prompt contains key terms from question."""
    # Extract key nouns/verbs (simplified)
    prompt_words = set(re.findall(r'\b\w+\b', prompt.lower()))
    question_words = set(re.findall(r'\b\w+\b', question.lower()))

    # Remove common stop words
    stop_words = {"what", "is", "the", "are", "can", "how", "do", "which", "where", "when", "why", "a", "an", "of", "in", "on", "at", "to", "for"}
    prompt_words -= stop_words
    question_words -= stop_words

    # Check if at least 50% of question words are in prompt
    if not question_words:
        return False
    match_ratio = len(prompt_words & question_words) / len(question_words)
    return match_ratio >= 0.5


def _generate_contextual_answer(prompt: str, context: str) -> str | None:
    """
    Generate a grounded answer from the provided context for first-time questions.
    Extracts key information from SQL tool results in the context (last occurrence).
    """
    if not context or not context.strip():
        return None
    
    # Extract product info from context (SQL tool results - take LAST occurrence)
    import re
    
    # Find all occurrences and take the last one (SQL tool results are appended at the end)
    product_matches = list(re.finditer(r'Product:\s*([^\n]+)', context))
    standard_matches = list(re.finditer(r'Standard:\s*([^\n]+)', context))
    scheme_matches = list(re.finditer(r'Scheme:\s*([^\n]+)', context))
    mandatory_matches = list(re.finditer(r'Mandatory:\s*([^\n]+)', context))
    qco_matches = list(re.finditer(r'QCO Order:\s*([^\n]+)', context))
    
    if not product_matches:
        return None

    # Take the last match (SQL tool result is appended last)
    product = product_matches[-1].group(1).strip()
    standard = standard_matches[-1].group(1).strip() if standard_matches else "Not specified"
    scheme = scheme_matches[-1].group(1).strip() if scheme_matches else "Not specified"
    mandatory = mandatory_matches[-1].group(1).strip() if mandatory_matches else "Unknown"
    qco = qco_matches[-1].group(1).strip() if qco_matches else "Not specified"
    
    # Build answer based on product type
    if "helmet" in product.lower():
        return (
            f"In India, {product} are governed by **{standard}** "
            f"('Protective Helmets for Two-Wheeler Riders'). "
            f"Under the {qco}, BIS certification under **{scheme}** "
            f"is **mandatory**. Helmets must undergo rigorous tests "
            f"including shock absorption, penetration resistance, "
            f"retention system strength, and peripheral vision compliance before sale."
        )
    elif "led" in product.lower() or "lamp" in product.lower() or "bulb" in product.lower():
        return (
            f"{product} in India are governed by **{standard}**. "
            f"Under the {qco}, BIS certification under **{scheme}** "
            f"is **mandatory**. Products must meet safety and photometric "
            f"performance requirements as per the standard."
        )
    elif "pressure cooker" in product.lower() or "cooker" in product.lower():
        return (
            f"{product} in India are governed by **{standard}**. "
            f"Under the {qco}, BIS certification under **{scheme}** "
            f"is **mandatory**. Cookers must pass hydraulic pressure test, "
            f"blow-off valve testing, and thermal shock resistance."
        )
    elif "gold" in product.lower() or "jewellery" in product.lower() or "jewelry" in product.lower():
        return (
            f"{product} in India are governed by **{standard}**. "
            f"Under the {qco}, hallmarking under **{scheme}** "
            f"is **mandatory**. Each article must bear a 6-digit HUID "
            f"for traceability and purity verification."
        )
    elif "water" in product.lower():
        return (
            f"{product} in India are governed by **{standard}**. "
            f"Under the {qco}, BIS certification under **{scheme}** "
            f"is **mandatory**. Water must meet microbiological, chemical, "
            f"and physical quality parameters."
        )
    else:
        # Generic template
        mandatory_text = "mandatory" if "true" in mandatory.lower() else "voluntary"
        return (
            f"{product} in India are governed by **{standard}**. "
            f"Under the {qco}, BIS certification under **{scheme}** "
            f"is **{mandatory_text}**."
        )


# ---------------------------------------------------------------------------
# Gemini provider (primary)
# ---------------------------------------------------------------------------

async def _gemini_generate(prompt: str, context: str = "") -> dict[str, Any]:
    """Call Google Gemini via the REST API (keeps dependencies light)."""
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    model = settings.GEMINI_MODEL
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
        f":generateContent?key={api_key}"
    )

    # Build the request body — single user turn with optional context
    parts: list[dict] = []
    if context:
        parts.append({"text": f"Context:\n{context}\n\n"})
    parts.append({"text": prompt})

    body = {"contents": [{"parts": parts}]}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=body)
        if resp.status_code != 200:
            logger.error("Gemini API error %d: %s", resp.status_code, resp.text)
        resp.raise_for_status()
        data = resp.json()

    # Extract generated text
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        logger.error("Unexpected Gemini response structure: %s", data)
        raise RuntimeError("Failed to parse Gemini response") from exc

    usage = data.get("usageMetadata", {})
    return {
        "text": text,
        "provider": "gemini",
        "model": model,
        "usage": {
            "prompt_tokens": usage.get("promptTokenCount", 0),
            "completion_tokens": usage.get("candidatesTokenCount", 0),
        },
    }


async def _gemini_vision_generate(prompt: str, image_bytes: bytes, mime_type: str) -> dict[str, Any]:
    """Call Google Gemini Vision via the REST API with inline image data."""
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    model = settings.GEMINI_MODEL
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
        f":generateContent?key={api_key}"
    )

    # Encode image bytes to base64
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')

    # Build the request body with inline image data
    parts: list[dict] = []
    parts.append({
        "inline_data": {
            "mime_type": mime_type,
            "data": image_base64
        }
    })
    parts.append({"text": prompt})

    body = {"contents": [{"parts": parts}]}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=body)
        if resp.status_code != 200:
            logger.error("Gemini Vision API error %d: %s", resp.status_code, resp.text)
        resp.raise_for_status()
        data = resp.json()

    # Extract generated text
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        logger.error("Unexpected Gemini Vision response structure: %s", data)
        raise RuntimeError("Failed to parse Gemini Vision response") from exc

    usage = data.get("usageMetadata", {})
    return {
        "text": text,
        "provider": "gemini",
        "model": model,
        "usage": {
            "prompt_tokens": usage.get("promptTokenCount", 0),
            "completion_tokens": usage.get("candidatesTokenCount", 0),
        },
    }


# ---------------------------------------------------------------------------
# Groq provider (fallback)
# ---------------------------------------------------------------------------

async def _groq_generate(prompt: str, context: str = "") -> dict[str, Any]:
    """Call Groq chat completions API as fallback."""
    api_key = settings.GROQ_API_KEY
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set")

    model = settings.GROQ_MODEL
    url = "https://api.groq.com/openai/v1/chat/completions"

    messages: list[dict] = []
    if context:
        messages.append({"role": "system", "content": f"Context:\n{context}"})
    messages.append({"role": "user", "content": prompt})

    body = {"model": model, "messages": messages, "temperature": 0.2, "max_tokens": 1024}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            url, json=body, headers={"Authorization": f"Bearer {api_key}"}
        )
        if resp.status_code != 200:
            logger.error("Groq API error %d: %s", resp.status_code, resp.text)
        resp.raise_for_status()
        data = resp.json()

    text = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return {
        "text": text,
        "provider": "groq",
        "model": model,
        "usage": {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
        },
    }


# ---------------------------------------------------------------------------
# Public entry point with retry + fallback
# ---------------------------------------------------------------------------

async def generate(prompt: str, context: str = "") -> dict[str, Any]:
    """Generate an LLM response.  Order: mock → Gemini (with retry) → Groq."""

    # --- Mock mode (no cost) ---
    if settings.MOCK_LLM:
        return await _mock_generate(prompt, context)

    # --- Gemini with exponential backoff ---
    last_exc: Exception | None = None
    for attempt in range(1, settings.LLM_MAX_RETRIES + 1):
        try:
            return await _gemini_generate(prompt, context)
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            delay = settings.LLM_RETRY_BASE_DELAY * (2 ** (attempt - 1))
            logger.warning(
                "Gemini attempt %d/%d failed (%s) — retrying in %.1fs",
                attempt,
                settings.LLM_MAX_RETRIES,
                exc,
                delay,
            )
            await asyncio.sleep(delay)

    logger.error("Gemini exhausted retries; falling back to Groq")

    # --- Groq fallback ---
    try:
        return await _groq_generate(prompt, context)
    except Exception as exc:  # noqa: BLE001
        logger.error("Groq fallback also failed: %s", exc)
        raise RuntimeError(
            "All LLM providers failed. Please try again later."
        ) from last_exc


async def generate_vision(prompt: str, image_bytes: bytes, mime_type: str) -> dict[str, Any]:
    """Generate an LLM response from image. Order: mock → Gemini (with retry)."""
    # --- Mock mode (no cost) ---
    if settings.MOCK_LLM:
        return await _mock_vision_generate(prompt, image_bytes, mime_type)

    # --- Gemini Vision with exponential backoff ---
    last_exc: Exception | None = None
    for attempt in range(1, settings.LLM_MAX_RETRIES + 1):
        try:
            return await _gemini_vision_generate(prompt, image_bytes, mime_type)
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            delay = settings.LLM_RETRY_BASE_DELAY * (2 ** (attempt - 1))
            logger.warning(
                "Gemini Vision attempt %d/%d failed (%s) — retrying in %.1fs",
                attempt,
                settings.LLM_MAX_RETRIES,
                exc,
                delay,
            )
            await asyncio.sleep(delay)

    logger.error("Gemini Vision exhausted retries")
    raise RuntimeError(
        "Gemini Vision failed after retries. Please try again later."
    ) from last_exc
