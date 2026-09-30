"""Multilingual support tests for language detection, intent routing, and response generation."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from backend.app.main import app
from backend.app.core.lang import detect_language
from backend.app.core.router import classify_intent
from backend.app.core.prompts import get_safe_fallback


client = TestClient(app)


def test_detect_language_english():
    """Test language detection for English queries."""
    assert detect_language("What is the standard for helmets?") == "en"
    assert detect_language("Which IS code applies to LED bulbs?") == "en"
    assert detect_language("") == "en"  # defaults to English
    assert detect_language("   ") == "en"  # defaults to English


def test_detect_language_hindi():
    """Test language detection for Hindi queries."""
    assert detect_language("दोपहिया वाहन चालकों के लिए हेलमेट का कौन सा मानक लागू होता है?") == "hi"
    assert detect_language("एलईडी बल्ब के लिए कौन सा बीआईएस लाइसेंस चाहिए?") == "hi"
    assert detect_language("मानक") == "hi"
    assert detect_language("हेलमेट") == "hi"


def test_detect_language_marathi():
    """Test language detection for Marathi queries."""
    assert detect_language("दुचाकी चालकांसाठी हेल्मेटचे कोणते मानक लागू आहे?") == "mr"
    assert detect_language("आम्ही LED बल्ब बनवतो, काय मानक लागू?") == "mr"
    assert detect_language("कोणते मानक") == "mr"
    assert detect_language("स्टील उत्पादनांसाठी परवाना") == "mr"


def test_detect_language_tamil():
    """Test language detection for Tamil queries."""
    assert detect_language("இருசக்கர வாகன ஓட்டிகளுக்கான ஹெல்மெட் தரம் என்ன?") == "ta"
    assert detect_language("எல்இடி பல்புகளுக்கு என்ன சான்றிதழ் தேவை?") == "ta"
    assert detect_language("ஹால்மார்க்கிங்") == "ta"


def test_language_detection_fallback_to_english():
    """Test that unknown languages fallback to English (default)."""
    with patch('backend.app.core.lang.detect', side_effect=Exception()):
        assert detect_language("Some random text") == "en"


def test_classify_intent_multilingual_patterns():
    """Test that intent classification works for Hindi and Marathi patterns."""
    # Hindi patterns
    assert classify_intent("हेलमेट") == "find_standard"
    assert classify_intent("प्रक्रिया") == "explain_scheme"
    assert classify_intent("प्रयोगशाला") == "find_lab"
    assert classify_intent("हॉलमार्क") == "hallmarking"
    assert classify_intent("सत्यापन") == "verify_license"
    assert classify_intent("शिकायत") == "consumer_query"
    assert classify_intent("बीआईएस क्या है") == "general_faq"
    assert classify_intent("मैं बनाता हूँ") == "recommend_compliance"

    # Marathi patterns
    assert classify_intent("हेल्मेट") == "find_standard"
    assert classify_intent("प्रक्रिया") == "explain_scheme"
    assert classify_intent("प्रयोगशाळा") == "find_lab"
    assert classify_intent("हॉलमार्किंग") == "hallmarking"
    assert classify_intent("परवाना तपासा") == "verify_license"
    assert classify_intent("ग्राहक") == "consumer_query"
    assert classify_intent(r"बी\.आई\.एस\.") == "general_faq"
    assert classify_intent("आम्ही बनवतो") == "recommend_compliance"


def test_safe_fallback_multilingual():
    """Test that safe fallback responses are available in all supported languages."""
    en_fallback = get_safe_fallback("en")
    hi_fallback = get_safe_fallback("hi")
    mr_fallback = get_safe_fallback("mr")
    ta_fallback = get_safe_fallback("ta")

    assert "answer" in en_fallback
    assert "answer" in hi_fallback
    assert "answer" in mr_fallback
    assert "answer" in ta_fallback

    # Check that the Hindi fallback contains Devanagari characters
    assert any("ऀ" <= c <= "ॿ" for c in hi_fallback["answer"])
    # Check that the Marathi fallback contains Devanagari characters
    assert any("ऀ" <= c <= "ॿ" for c in mr_fallback["answer"])
    # Check that the Tamil fallback contains Tamil characters
    assert any("஀" <= c <= "௿" for c in ta_fallback["answer"])


@pytest.mark.asyncio
async def test_chat_endpoint_language_detection_and_response():
    """Test that the chat endpoint detects language and returns a response in that language."""
    # Mock the LLM generate function to return a structured response in the detected language
    async def mock_generate(prompt: str, context: str = ""):
        # Detect language from the prompt (simplified for test)
        if "Respond in fluent, natural Hindi" in prompt:
            lang = "hi"
            answer = "यह एक परीक्षण उत्तर है।"
        elif "Respond in fluent, natural Marathi" in prompt:
            lang = "mr"
            answer = "हे एक प्रयोगात्मक उत्तर आहे।"
        elif "Respond in fluent, natural Tamil" in prompt:
            lang = "ta"
            answer = "இது ஒரு சோதனை பதில்."
        else:
            lang = "en"
            answer = "This is a test response."

        return {
            "text": f"""{{
                "answer": "{answer}",
                "citations": [{{"source": "IS 4151", "section": "Clause 1", "url": "https://www.bis.gov.in/"}}],
                "confidence": 0.9,
                "follow_up_suggestions": ["Test follow-up"]
            }}""",
            "provider": "mock",
            "model": "mock",
            "usage": {"prompt_tokens": 0, "completion_tokens": 0},
        }

    with patch("backend.app.api.chat.generate", side_effect=mock_generate):
        # Test English query (no language specified)
            response = client.post("/chat", json={"question": "What is the standard for helmets?"})
            assert response.status_code == 200
            data = response.json()
            assert data["language"] == "en"
            assert "test response" in data["answer"].lower()

            # Test Hindi query (no language specified)
            response = client.post("/chat", json={"question": "दोपहिया वाहन चालकों के लिए हेलमेट का कौन सा मानक लागू होता है?"})
            assert response.status_code == 200
            data = response.json()
            assert data["language"] == "hi"
            # The answer should be in Hindi (we can check for Devanagari)
            assert any("ऀ" <= c <= "ॿ" for c in data["answer"])

            # Test Marathi query (no language specified)
            response = client.post("/chat", json={"question": "दुचाकी चालकांसाठी हेल्मेटचे कोणते मानक लागू आहे?"})
            assert response.status_code == 200
            data = response.json()
            assert data["language"] == "mr"
            # The answer should be in Marathi (Devanagari)
            assert any("ऀ" <= c <= "ॿ" for c in data["answer"])

            # Test Tamil query (no language specified)
            response = client.post("/chat", json={"question": "இருத Sri Lanka கStudents in Sri Lanka"})
            assert response.status_code == 200
            data = response.json()
            assert data["language"] == "ta"
            # The answer should be in Tamil (Tamil script)
            assert any("஀" <= c <= "௿" for c in data["answer"])


@pytest.mark.asyncio
async def test_recommend_endpoint_language_detection():
    """Test that the recommend endpoint detects language and returns a response in that language."""
    # Mock the recommend_compliance function to return some candidates
    async def mock_recommend_compliance(product_description: str, top_k: int = 3):
        # Detect language from the product description (simplified for test)
        if any(c in product_description for c in "दोपहिया वाहन"):
            lang = "hi"
        elif any(c in product_description for c in "दुचाकी"):
            lang = "mr"
        elif any(c in product_description for c in "இருத"):
            lang = "ta"
        else:
            lang = "en"

        # Return a candidate match in the detected language
        candidates = [{
            "product_name": "Test Product",
            "applicable_standard": "IS 4151",
            "scheme_code": "ISI",
            "mandatory": True,
            "qco_order": "QCO 123",
            "confidence": 0.95,
            "key_requirements": ["Requirement 1", "Requirement 2"],
            "next_steps": ["Step 1", "Step 2"],
            "nearest_labs": ["Lab A", "Lab B"]
        }]
        is_ambiguous = False
        clarifying_question = None
        return candidates, is_ambiguous, clarifying_question

    with patch("backend.app.tools.recommend.recommend_compliance", side_effect=mock_recommend_compliance):
        # Test English query (no language specified)
        response = client.post("/recommend", json={"product_description": "I manufacture LED bulbs for homes"})
        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "en"

        # Test Hindi query (no language specified)
        response = client.post("/recommend", json={"product_description": "दोपहिया वाहन चालकों के लिए हेलमेट"})
        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "hi"

        # Test Marathi query (no language specified)
        response = client.post("/recommend", json={"product_description": "दुचाकी चालकांसाठी हेल्मेट"})
        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "mr"

        # Test Tamil query (no language specified)
        response = client.post("/recommend", json={"product_description": "இருத Sri Lanka கStudents in Sri Lanka"})
        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "ta"


def test_bhashini_feature_flag():
    """Test that the Bhashini adapter respects the feature flag."""
    from backend.app.core.bhashini import bhashini_client

    # When disabled, it should return the original text
    assert bhashini_client.enabled == False  # Assuming ENABLE_BHASHINI is False by default
    # We can test the translate_text method directly
    import asyncio
    result = asyncio.run(bhashini_client.translate_text("Hello", "en", "hi"))
    assert result == "Hello"  # Should fall back to original text when disabled or not configured

    # When enabled but not configured, should also fall back
    bhashini_client.enabled = True
    bhashini_client.api_key = ""  # Not configured
    result = asyncio.run(bhashini_client.translate_text("Hello", "en", "hi"))
    assert result == "Hello"  # Should fall back to original text

    # Reset to default
    bhashini_client.enabled = False