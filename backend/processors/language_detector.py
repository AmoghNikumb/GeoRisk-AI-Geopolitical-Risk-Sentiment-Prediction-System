"""
processors/language_detector.py
Detects language of text using langdetect.
Supports filtering to only geopolitically relevant languages.
"""
import logging
from typing import Optional
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

logger = logging.getLogger(__name__)

# Fix random seed for reproducibility
DetectorFactory.seed = 42

# Languages we can process with our NLP models
SUPPORTED_LANGUAGES = {
    "en",   # English       — cardiffnlp/twitter-roberta
    "ar",   # Arabic        — XLM-RoBERTa
    "hi",   # Hindi         — XLM-RoBERTa
    "ru",   # Russian       — XLM-RoBERTa
    "zh-cn", "zh-tw", "zh", # Chinese — XLM-RoBERTa
    "fr",   # French        — XLM-RoBERTa
    "de",   # German        — XLM-RoBERTa
    "es",   # Spanish       — XLM-RoBERTa
    "ur",   # Urdu          — XLM-RoBERTa (close to Hindi)
    "fa",   # Persian/Farsi — XLM-RoBERTa
    "tr",   # Turkish       — XLM-RoBERTa
    "ko",   # Korean        — XLM-RoBERTa
    "ja",   # Japanese      — XLM-RoBERTa
}

# Normalize langdetect output to canonical codes
_NORMALIZE = {
    "zh-cn": "zh",
    "zh-tw": "zh",
}


def detect_language(text: str) -> Optional[str]:
    """
    Detect language of text.
    Returns ISO 639-1 language code or None if detection fails.
    """
    if not text or len(text) < 20:
        return None
    try:
        lang = detect(text)
        return _NORMALIZE.get(lang, lang)
    except LangDetectException:
        return None
    except Exception as e:
        logger.warning(f"Language detection error: {e}")
        return None


def is_supported_language(lang: Optional[str]) -> bool:
    """Returns True if we have an NLP model that can process this language."""
    if not lang:
        return False
    return lang in SUPPORTED_LANGUAGES or lang.split("-")[0] in SUPPORTED_LANGUAGES


def get_model_for_language(lang: Optional[str]) -> str:
    """
    Returns the HuggingFace model name to use for a given language.
    English → domain-adapted RoBERTa
    Others  → multilingual XLM-RoBERTa
    """
    if lang == "en":
        return "cardiffnlp/twitter-roberta-base-sentiment"
    return "cardiffnlp/twitter-xlm-roberta-base-sentiment"

