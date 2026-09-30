"""Strict grounding prompts for the RAG pipeline."""

# ---------------------------------------------------------------------------
# System prompt: strict grounding rules & multilingual citation rules
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are Parakh, an authoritative AI assistant for Indian Standards (IS) and BIS (Bureau of Indian Standards) services.

CRITICAL RULES:
1. Answer ONLY from the provided context. If the context does not contain the answer, say so explicitly.
2. NEVER fabricate IS numbers, clause references, fees, dates, or URLs.
3. Every factual claim MUST be cited with source, section/clause, and URL from the context.
4. Keep all Indian Standard IDs (e.g., IS 1239, IS 4151, IS 16102), Scheme Codes (ISI, CRS, FMCS, HUID, AHC), and URLs UNTRANSLATED and in Latin script, even when responding in Hindi, Marathi, Tamil, or other Indian languages.
5. Citations in the "citations" array MUST remain in standard English/canonical format matching the retrieved chunks.
6. If you are uncertain or the context is incomplete, say: "Based on available information, [partial answer]. For complete details, please visit the official BIS portal at https://www.bis.gov.in/"
7. Output ONLY valid JSON in the exact schema requested.

OUTPUT SCHEMA:
{
  "answer": "The answer in the requested language (English/Hindi/Marathi/Tamil) with untranslated IS standard numbers",
  "citations": [
    {"source": "IS 1239", "section": "Clause 4.1", "url": "https://www.bis.gov.in/..."}
  ],
  "confidence": 0.85,  // 0.0 to 1.0
  "follow_up_suggestions": ["Follow-up question 1 in user's language", "Follow-up question 2 in user's language"]
}
"""

# ---------------------------------------------------------------------------
# Query template for grounded answers
# ---------------------------------------------------------------------------

def build_grounded_query(
    question: str,
    context: str,
    language: str = "en",
    conversation_history: str = "",
) -> str:
    """Build the final prompt with context, strict grounding, and multilingual instructions."""

    lang_instructions = {
        "hi": (
            "\n\nLANGUAGE INSTRUCTION: Respond in fluent, natural Hindi (Devanagari script). "
            "Keep all standard numbers (e.g. IS 4151, IS 1239), scheme codes (ISI, CRS, FMCS, HUID), "
            "and portal URLs untranslated in Latin letters."
        ),
        "mr": (
            "\n\nLANGUAGE INSTRUCTION: Respond in fluent, natural Marathi (Devanagari script). "
            "Keep all standard numbers (e.g. IS 4151, IS 1239), scheme codes (ISI, CRS, FMCS, HUID), "
            "and portal URLs untranslated in Latin letters."
        ),
        "ta": (
            "\n\nLANGUAGE INSTRUCTION: Respond in fluent, natural Tamil (Tamil script). "
            "Keep all standard numbers (e.g. IS 4151, IS 1239), scheme codes (ISI, CRS, FMCS, HUID), "
            "and portal URLs untranslated in Latin letters."
        ),
        "en": "\n\nLANGUAGE INSTRUCTION: Respond in English.",
    }

    lang_instruction = lang_instructions.get(
        language,
        f"\n\nLANGUAGE INSTRUCTION: Respond in {language} if possible, otherwise English. Keep IS numbers untranslated."
    )

    history_section = ""
    if conversation_history:
        history_section = f"\n\nPREVIOUS CONVERSATION:\n{conversation_history}\n"

    return f"""{SYSTEM_PROMPT}

CONTEXT (Retrieved from BIS knowledge base):
{context}
{history_section}
USER QUESTION:
{question}
{lang_instruction}

OUTPUT (valid JSON only, no other text):
"""


# ---------------------------------------------------------------------------
# Safe fallback responses (low confidence / no context) in supported languages
# ---------------------------------------------------------------------------

SAFE_FALLBACK_EN = {
    "answer": (
        "I don't have enough information in my knowledge base to answer this question accurately. "
        "For the most current and authoritative information, please visit the official BIS portal: "
        "https://www.bis.gov.in/ or call the BIS helpline at 1800-11-2417."
    ),
    "citations": [
        {
            "source": "BIS Official Portal",
            "section": None,
            "url": "https://www.bis.gov.in/",
        }
    ],
    "confidence": 0.0,
    "follow_up_suggestions": [
        "How do I contact BIS?",
        "What products need BIS certification?",
    ],
    "language": "en",
}

SAFE_FALLBACK_HI = {
    "answer": (
        "मेरे पास इस प्रश्न का सटीक उत्तर देने के लिए आधिकारिक ज्ञानकोश में पर्याप्त जानकारी नहीं है। "
        "नवीनतम और आधिकारिक जानकारी के लिए, कृपया आधिकारिक BIS पोर्टल पर जाएं: "
        "https://www.bis.gov.in/ या BIS हेल्पलाइन 1800-11-2417 पर संपर्क करें।"
    ),
    "citations": [
        {
            "source": "BIS Official Portal",
            "section": None,
            "url": "https://www.bis.gov.in/",
        }
    ],
    "confidence": 0.0,
    "follow_up_suggestions": [
        "मैं BIS से कैसे संपर्क करूं?",
        "किन उत्पादों के लिए BIS प्रमाणन अनिवार्य है?",
    ],
    "language": "hi",
}

SAFE_FALLBACK_MR = {
    "answer": (
        "माझ्याकडे या प्रश्नाचे अचूक उत्तर देण्यासाठी पुरेशी अधिकृत माहिती उपलब्ध नाही. "
        "अद्ययावत आणि अधिकृत माहितीसाठी, कृपया अधिकृत BIS पोर्टलला भेट द्या: "
        "https://www.bis.gov.in/ किंवा BIS हेल्पलाईन 1800-11-2417 वर संपर्क साधा."
    ),
    "citations": [
        {
            "source": "BIS Official Portal",
            "section": None,
            "url": "https://www.bis.gov.in/",
        }
    ],
    "confidence": 0.0,
    "follow_up_suggestions": [
        "मी BIS शी कसा संपर्क साधू शकतो?",
        "कोणत्या उत्पादनांसाठी BIS प्रमाणपत्र अनिवार्य आहे?",
    ],
    "language": "mr",
}

SAFE_FALLBACK_TA = {
    "answer": (
        "இந்தக் கேள்விக்கு துல்லியமாக பதிலளிக்க போதுமான அதிகாரப்பூர்வ தகவல் கிடைக்கவில்லை. "
        "சமீபத்திய மற்றும் அதிகாரப்பூர்வ தகவல்களுக்கு, அதிகாரப்பூர்வ BIS இணையதளத்தைப் பார்வையிடவும்: "
        "https://www.bis.gov.in/ அல்லது BIS உதவி எண் 1800-11-2417 ஐ தொடர்பு கொள்ளவும்."
    ),
    "citations": [
        {
            "source": "BIS Official Portal",
            "section": None,
            "url": "https://www.bis.gov.in/",
        }
    ],
    "confidence": 0.0,
    "follow_up_suggestions": [
        "BIS-ஐ எவ்வாறு தொடர்பு கொள்வது?",
        "எந்த பொருட்களுக்கு BIS சான்றிதழ் கட்டாயமாகும்?",
    ],
    "language": "ta",
}


def get_safe_fallback(language: str = "en") -> dict:
    """Return a safe fallback response in the user's language when confidence is too low."""
    if language == "hi":
        return SAFE_FALLBACK_HI
    elif language == "mr":
        return SAFE_FALLBACK_MR
    elif language == "ta":
        return SAFE_FALLBACK_TA
    return SAFE_FALLBACK_EN
