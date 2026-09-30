"""Intent router: rule-based + keyword intent classification."""

import logging
import re
from typing import Dict, Any, List

logger = logging.getLogger("parakh.router")

# Available intents
INTENTS = {
    "find_standard": "Find Indian Standard for a product or lookup an IS number",
    "explain_scheme": "Explain certification schemes (ISI, CRS, FMCS, Hallmarking) and fees",
    "find_lab": "Locate recognized testing laboratories",
    "hallmarking": "Questions about gold/silver hallmarking, HUID, AHC",
    "verify_license": "Verify a license number, CM/L, or HUID",
    "consumer_query": "Consumer complaints, substandard products, consumer rights",
    "general_faq": "General questions about BIS, roles, website, portal",
    "recommend_compliance": "Recommend BIS certification and standards for a product description",
}

# Rule patterns for fast intent detection (English, Hindi, Marathi)
PATTERNS = {
    "find_standard": [
        r"\bis\s*\d+",  # IS 1239, IS 4151
        r"\bstandard\b",
        r"\bwhich standard\b",
        r"\bapplicable standard\b",
        r"\bmandatory\b",
        r"\bqco\b",
        r"\bcro\b",
        r"\bcompulsory\b",
        r"\bhelmets?\b",
        r"\bcement\b",
        r"\bsteel\b",
        r"\bled\b",
        r"\bcharger\b",
        r"\blpg\b",
        # Hindi / Marathi patterns
        r"मानक",
        r"हेलमेट",
        r"हेल्मेट",
        r"सीमेंट",
        r"स्टील",
        r"एलईडी",
        r"अनिवार्य",
        r"लागू",
        r"कोणते मानक",
        r"कोणता स्टँडर्ड",
    ],
    "explain_scheme": [
        r"\bscheme\b",
        r"\bisi mark\b",
        r"\bcrs\b",
        r"\bfmcs\b",
        r"\bforeign manufacturer\b",
        r"\bfee\b",
        r"\bcost\b",
        r"\bhow to apply\b",
        r"\bprocess\b",
        r"\blicense\b",
        r"\bcertification process\b",
        # Hindi / Marathi patterns
        r"स्कीम",
        r"योजना",
        r"आईएसआई",
        r"प्रक्रिया",
        r"शुल्क",
        r"फीस",
        r"आवेदन",
        r"प्रमाणपत्र कसे मिळवावे",
    ],
    "find_lab": [
        r"\blab\b",
        r"\blaborator(y|ies)\b",
        r"\btesting\b",
        r"\btest\b",
        r"\bnabl\b",
        r"\btest report\b",
        r"\bwhere to test\b",
        r"\bwhere can i test\b",
        # Hindi / Marathi patterns
        r"प्रयोगशाला",
        r"प्रयोगशाळा",
        r"लैब",
        r"जांच",
        r"परीक्षण",
        r"तपासणी",
        r"कुठे तपासणी",
    ],
    "hallmarking": [
        r"\bhallmark(ing)?\b",
        r"\bhuid\b",
        r"\bgold\b",
        r"\bsilver\b",
        r"\bjeweller(y|s)?\b",
        r"\bcarat\b",
        r"\bahc\b",
        r"\bassaying\b",
        r"\b22k\b",
        r"\b18k\b",
        # Hindi / Marathi patterns
        r"हॉलमार्क",
        r"हॉलमार्किंग",
        r"एचयूआईडी",
        r"सोना",
        r"सोने",
        r"चांदी",
        r"आभूषण",
        r"दागिने",
        r"कॅरेट",
    ],
    "verify_license": [
        r"\bverify\b",
        r"\bcheck license\b",
        r"\bcm/l\b",
        r"\bcml\b",
        r"\bcheck huid\b",
        r"\bvalid\b",
        r"\bis this authentic\b",
        r"\bfake\b",
        # Hindi / Marathi patterns
        r"सत्यापन",
        r"सत्यापित",
        r"लाइसेंस जांच",
        r"खरा की खोटा",
        r"वैध",
        r"परवाना तपासा",
    ],
    "consumer_query": [
        r"\bcomplaint\b",
        r"\bsubstandard\b",
        r"\bcheat\b",
        r"\bconsumer\b",
        r"\bgrievance\b",
        r"\bhow to report\b",
        r"\bcare app\b",
        r"\bhelpline\b",
        # Hindi / Marathi patterns
        r"शिकायत",
        r"तक्रार",
        r"उपभोक्ता",
        r"ग्राहक",
        r"खराब माल",
        r"केयर ऐप",
        r"हेल्पलाइन",
    ],
    "general_faq": [
        r"\bwhat is bis\b",
        r"\babout bis\b",
        r"\bportal\b",
        r"\bwebsite\b",
        r"\bcontact\b",
        r"\bmanak\b",
        # Hindi / Marathi patterns
        r"बीआईएस क्या है",
        r"बी\.आई\.एस\.",
        r"मानक भवन",
        r"संपर्क",
        r"पोर्टल",
        r"वेबसाइट",
    ],
    "recommend_compliance": [
        r"\bi make\b",
        r"\bi manufacture\b",
        r"\bwe make\b",
        r"\bwe manufacture\b",
        r"\bwe produce\b",
        r"\bi produce\b",
        r"\bwe sell\b",
        r"\bi sell\b",
        r"\bmy product\b",
        r"\bour product\b",
        r"\bwhat certification do i need\b",
        r"\bwhat compliance\b",
        r"\bwhich license do i need\b",
        r"\bdo i need bis\b",
        r"\brecommend\b",
        # Hindi / Marathi patterns
        r"मैं बनाता हूँ",
        r"हम बनाते हैं",
        r"हम उत्पादन करते हैं",
        r"उत्पादन",
        r"आम्ही बनवतो",
        r"आमचे उत्पादन",
        r"कोणते प्रमाणपत्र हवे",
    ],
}


def classify_intent(query: str) -> str:
    """
    Classify query intent using rule patterns.
    Fast, deterministic, and zero cost (no LLM call).
    """
    q_lower = query.lower()

    # Check each intent's patterns
    scores = {intent: 0 for intent in INTENTS}

    for intent, patterns in PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, q_lower):
                scores[intent] += 1

    # Find highest scoring intent
    best_intent = max(scores, key=scores.get)
    max_score = scores[best_intent]

    # If no pattern matched, default to general_faq
    if max_score == 0:
        logger.info(f"No rule match for '{query[:40]}...', defaulting to general_faq")
        return "general_faq"

    logger.info(f"Classified '{query[:40]}...' as '{best_intent}' (score: {max_score})")
    return best_intent
