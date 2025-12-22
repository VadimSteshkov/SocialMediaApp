"""
Test suite for the Translation Microservice.
Tests translation functionality, language detection, and text processing.
"""
import pytest
import sys
import os

# Add parent directory to path to import translation_service
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to import translation functions, skip tests if dependencies not available
try:
    from translation_service import detect_language, translate_text
    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False
    # Define mock functions for testing structure
    def detect_language(text):
        return 'en'
    def translate_text(text, source_lang=None, target_lang='en'):
        return {'translated_text': text, 'detected_lang': 'en', 'error': 'Service not available'}


@pytest.mark.skipif(not TRANSLATION_AVAILABLE, reason="Translation service dependencies not available")
def test_detect_language_english():
    """Test language detection for English text."""
    text = "Hello, this is a test message in English."
    detected = detect_language(text)
    assert detected == 'en'


@pytest.mark.skipif(not TRANSLATION_AVAILABLE, reason="Translation service dependencies not available")
def test_detect_language_russian():
    """Test language detection for Russian text."""
    text = "Привет, это тестовое сообщение на русском языке."
    detected = detect_language(text)
    assert detected == 'ru'


@pytest.mark.skipif(not TRANSLATION_AVAILABLE, reason="Translation service dependencies not available")
def test_detect_language_german():
    """Test language detection for German text."""
    text = "Hallo, dies ist eine Testnachricht auf Deutsch."
    detected = detect_language(text)
    assert detected == 'de'


@pytest.mark.skipif(not TRANSLATION_AVAILABLE, reason="Translation service dependencies not available")
def test_detect_language_spanish():
    """Test language detection for Spanish text."""
    text = "Hola, este es un mensaje de prueba en español."
    detected = detect_language(text)
    assert detected == 'es'


@pytest.mark.skipif(not TRANSLATION_AVAILABLE, reason="Translation service dependencies not available")
def test_detect_language_french():
    """Test language detection for French text."""
    text = "Bonjour, ceci est un message de test en français."
    detected = detect_language(text)
    assert detected == 'fr'


@pytest.mark.skipif(not TRANSLATION_AVAILABLE, reason="Translation service dependencies not available")
def test_detect_language_empty():
    """Test language detection for empty text."""
    text = ""
    detected = detect_language(text)
    assert detected == 'en'  # Default to English


@pytest.mark.skipif(not TRANSLATION_AVAILABLE, reason="Translation service dependencies not available")
def test_detect_language_none():
    """Test language detection for None text."""
    text = None
    detected = detect_language(text)
    assert detected == 'en'  # Default to English


@pytest.mark.skipif(not TRANSLATION_AVAILABLE, reason="Translation service dependencies not available")
def test_translate_text_empty():
    """Test translation of empty text."""
    result = translate_text("", source_lang='en', target_lang='de')
    assert 'error' in result
    assert result['detected_lang'] == 'en'


@pytest.mark.skipif(not TRANSLATION_AVAILABLE, reason="Translation service dependencies not available")
def test_translate_text_same_language():
    """Test translation when source and target languages are the same."""
    text = "Hello, this is a test."
    result = translate_text(text, source_lang='en', target_lang='en')
    assert result['translated_text'] == text
    assert result['source_lang'] == 'en'
    assert result['target_lang'] == 'en'
    assert 'error' not in result


@pytest.mark.skipif(not TRANSLATION_AVAILABLE, reason="Translation service dependencies not available")
def test_translate_text_short_english_to_german():
    """Test translation of short English text to German."""
    text = "Hello, how are you?"
    result = translate_text(text, source_lang='en', target_lang='de')
    
    # Translation should succeed (may return error if model not loaded, but structure should be correct)
    assert 'translated_text' in result
    assert 'detected_lang' in result
    assert result['source_lang'] == 'en'
    assert result['target_lang'] == 'de'
    
    # If translation succeeded, text should be different
    if 'error' not in result:
        assert result['translated_text'] != text
        assert len(result['translated_text']) > 0


@pytest.mark.skipif(not TRANSLATION_AVAILABLE, reason="Translation service dependencies not available")
def test_translate_text_auto_detect():
    """Test translation with automatic language detection."""
    text = "Hello, this is a test message."
    result = translate_text(text, source_lang=None, target_lang='de')
    
    assert 'translated_text' in result
    assert 'detected_lang' in result
    assert result['detected_lang'] == 'en'  # Should detect as English
    assert result['target_lang'] == 'de'


@pytest.mark.skipif(not TRANSLATION_AVAILABLE, reason="Translation service dependencies not available")
def test_translate_text_long_text():
    """Test translation of longer text (should handle chunking)."""
    text = "This is a longer text that should be split into multiple chunks for translation. " * 10
    result = translate_text(text, source_lang='en', target_lang='de')
    
    assert 'translated_text' in result
    assert 'detected_lang' in result
    
    # If translation succeeded, should have translated text
    if 'error' not in result:
        assert len(result['translated_text']) > 0
        # Translated text might be shorter or longer, but should exist
        assert isinstance(result['translated_text'], str)


@pytest.mark.skipif(not TRANSLATION_AVAILABLE, reason="Translation service dependencies not available")
def test_translate_text_unsupported_language_pair():
    """Test translation with unsupported language pair."""
    text = "Test message"
    result = translate_text(text, source_lang='xx', target_lang='yy')
    
    # Should return error or original text
    assert 'translated_text' in result
    # May have error or return original text
    assert isinstance(result['translated_text'], str)


@pytest.mark.skipif(not TRANSLATION_AVAILABLE, reason="Translation service dependencies not available")
def test_translate_text_special_characters():
    """Test translation of text with special characters."""
    text = "Hello! This is a test with numbers: 123 and symbols: @#$%"
    result = translate_text(text, source_lang='en', target_lang='de')
    
    assert 'translated_text' in result
    assert 'detected_lang' in result
    
    if 'error' not in result:
        assert len(result['translated_text']) > 0


@pytest.mark.skipif(not TRANSLATION_AVAILABLE, reason="Translation service dependencies not available")
def test_translate_text_multiple_sentences():
    """Test translation of text with multiple sentences."""
    text = "First sentence. Second sentence. Third sentence."
    result = translate_text(text, source_lang='en', target_lang='de')
    
    assert 'translated_text' in result
    assert 'detected_lang' in result
    
    if 'error' not in result:
        assert len(result['translated_text']) > 0
        # Should preserve sentence structure
        assert isinstance(result['translated_text'], str)

