"""
processors/entity_extractor.py
Extracts country mentions and person names from cleaned text.
Uses:
  - Regex/keyword matching for countries (fast, reliable)
  - spaCy NER for person extraction (en_core_web_sm)
"""
import re
import json
import os
import logging
from typing import List, Dict
from functools import lru_cache

logger = logging.getLogger(__name__)

# ── Country Keywords Map ──────────────────────────────────────────────────────
# Maps country codes to a list of name variants to search for
COUNTRY_KEYWORDS: Dict[str, List[str]] = {
    "US": ["united states", "usa", "america", "american", "washington", "white house", "pentagon", "u.s.", "u.s"],
    "CN": ["china", "chinese", "beijing", "xi jinping", "prc", "people's republic"],
    "RU": ["russia", "russian", "moscow", "kremlin", "putin", "soviet"],
    "IN": ["india", "indian", "new delhi", "modi", "bjp", "new delhi"],
    "PK": ["pakistan", "pakistani", "islamabad", "lahore", "karachi"],
    "GB": ["britain", "british", "uk", "united kingdom", "london", "england", "sunak", "downing street"],
    "DE": ["germany", "german", "berlin", "scholz", "bundeswehr"],
    "FR": ["france", "french", "paris", "macron", "elysee"],
    "JP": ["japan", "japanese", "tokyo", "japanese government"],
    "KR": ["south korea", "korean", "seoul", "republic of korea"],
    "KP": ["north korea", "dprk", "pyongyang", "kim jong"],
    "IR": ["iran", "iranian", "tehran", "khamenei", "irgc"],
    "IL": ["israel", "israeli", "tel aviv", "jerusalem", "idf", "netanyahu"],
    "SA": ["saudi arabia", "saudi", "riyadh", "mbs", "aramco"],
    "TR": ["turkey", "turkish", "ankara", "erdogan"],
    "UA": ["ukraine", "ukrainian", "kyiv", "zelensky", "zelenskyy"],
    "BR": ["brazil", "brazilian", "brasilia", "lula"],
    "AU": ["australia", "australian", "canberra", "sydney"],
    "CA": ["canada", "canadian", "ottawa", "trudeau"],
    "MX": ["mexico", "mexican", "mexico city"],
}


# ── spaCy Loader ──────────────────────────────────────────────────────────────
@lru_cache(maxsize=1)
def _load_spacy():
    """Lazy-load spaCy model (cached after first call)."""
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        logger.info("spaCy en_core_web_sm loaded.")
        return nlp
    except ModuleNotFoundError:
        logger.warning(
            "spaCy is not installed. Person extraction will be skipped. "
            "Install with: pip install spacy && python -m spacy download en_core_web_sm"
        )
        return None
    except OSError:
        logger.warning(
            "spaCy model not found. Run: python -m spacy download en_core_web_sm\n"
            "Person extraction will be skipped."
        )
        return None


class EntityExtractor:
    def __init__(self):
        self._spacy = None   # Lazy loaded

    def _get_spacy(self):
        if self._spacy is None:
            self._spacy = _load_spacy()
        return self._spacy

    def extract_countries(self, text: str) -> List[str]:
        """
        Returns list of ISO country codes mentioned in the text.
        Uses fast case-insensitive keyword matching.
        """
        text_lower = text.lower()
        found = []
        for code, keywords in COUNTRY_KEYWORDS.items():
            for kw in keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                    if code not in found:
                        found.append(code)
                    break   # One match per country is enough
        return found

    def extract_persons(self, text: str) -> List[str]:
        """
        Returns list of person names mentioned in the text.
        Uses spaCy NER (PERSON entity type).
        Falls back to empty list if spaCy unavailable.
        """
        nlp = self._get_spacy()
        if nlp is None:
            return []
        try:
            doc = nlp(text[:512])   # Cap at 512 chars for speed
            persons = [
                ent.text.strip()
                for ent in doc.ents
                if ent.label_ == "PERSON" and len(ent.text.strip()) > 2
            ]
            # Deduplicate
            return list(dict.fromkeys(persons))
        except Exception as e:
            logger.warning(f"spaCy NER failed: {e}")
            return []

    def extract_all(self, text: str) -> Dict[str, List[str]]:
        """
        Full entity extraction.
        Returns: {"countries": [...], "persons": [...]}
        """
        return {
            "countries": self.extract_countries(text),
            "persons": self.extract_persons(text),
        }

