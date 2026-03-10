"""
sentiment/hf_client.py
Generic HuggingFace Inference API wrapper.
Used for RoBERTa, FinBERT, and XLM-RoBERTa sentiment models.
Free tier: ~1000 req/hour. Batching keeps us well under.
"""
import logging
import time
from typing import List, Dict, Optional

import requests

from config import settings

logger = logging.getLogger(__name__)

HF_API_BASE = "https://api-inference.huggingface.co/models"

# Label mappings per model
ROBERTA_LABEL_MAP = {
    "LABEL_0": "NEGATIVE",
    "LABEL_1": "NEUTRAL",
    "LABEL_2": "POSITIVE",
}

FINBERT_LABEL_MAP = {
    "negative": "NEGATIVE",
    "neutral":  "NEUTRAL",
    "positive": "POSITIVE",
}


class HuggingFaceClient:
    def __init__(self, model_name: str, label_map: Optional[Dict] = None):
        self.model_name = model_name
        self.api_url    = f"{HF_API_BASE}/{model_name}"
        self.label_map  = label_map or ROBERTA_LABEL_MAP
        self.headers    = {"Authorization": f"Bearer {settings.huggingface_api_key}"}

    def _call_api(self, texts: List[str], retry: int = 3) -> Optional[List]:
        """
        POST to HF Inference API. Handles model loading delays.
        Returns list of prediction dicts or None on failure.
        """
        payload = {"inputs": texts, "options": {"wait_for_model": True}}

        for attempt in range(retry):
            try:
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=60,
                )
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 503:
                    # Model loading — wait and retry
                    wait = 20 * (attempt + 1)
                    logger.warning(f"HF model loading, waiting {wait}s...")
                    time.sleep(wait)
                elif response.status_code == 429:
                    # Rate limited
                    logger.warning("HF rate limited, waiting 60s...")
                    time.sleep(60)
                else:
                    logger.error(f"HF API error {response.status_code}: {response.text[:200]}")
                    return None
            except requests.exceptions.Timeout:
                logger.warning(f"HF API timeout (attempt {attempt + 1})")
            except Exception as e:
                logger.error(f"HF API exception: {e}")
                return None

        return None

    def score_texts(self, texts: List[str]) -> List[Optional[Dict]]:
        """
        Score a list of texts.
        Returns list of dicts: {"label": "NEGATIVE", "score": 0.91}
        Length matches input — None entries indicate failures.
        """
        if not texts:
            return []

        results = self._call_api(texts)
        if results is None:
            logger.error(f"HF scoring failed for {len(texts)} texts.")
            return [None] * len(texts)

        parsed = []
        for item in results:
            try:
                if isinstance(item, list):
                    # List of label predictions — take highest confidence
                    best = max(item, key=lambda x: x["score"])
                    label = self.label_map.get(best["label"].upper(), best["label"].upper())
                    parsed.append({"label": label, "score": best["score"]})
                elif isinstance(item, dict):
                    label = self.label_map.get(item["label"].upper(), item["label"].upper())
                    parsed.append({"label": label, "score": item["score"]})
                else:
                    parsed.append(None)
            except Exception as e:
                logger.warning(f"Failed to parse HF result {item}: {e}")
                parsed.append(None)

        return parsed


def normalize_to_float(label: str, confidence: float) -> float:
    """
    Convert label + confidence to a single float score.
    NEGATIVE: confidence mapped to [-1, 0]
    NEUTRAL:  always 0
    POSITIVE: confidence mapped to [0, +1]
    """
    if label == "NEGATIVE":
        return -confidence
    elif label == "POSITIVE":
        return confidence
    else:
        return 0.0

