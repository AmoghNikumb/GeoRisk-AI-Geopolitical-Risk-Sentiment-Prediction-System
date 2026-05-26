"""
sentiment/scorer.py
Batch-scores processed posts using the local RoBERTa pipeline (primary)
or HuggingFace Inference API (fallback when HUGGINGFACE_API_KEY is set).
Handles both English (RoBERTa) and multilingual (XLM-RoBERTa) texts.
Runs every hour via APScheduler (after preprocessing).
"""
import logging
import math
from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from config import settings
from database import get_db_session
from models.processed_post import ProcessedPost
from models.raw_post import RawPost
from models.politician import Politician
from processors.text_cleaner import clean_text, is_meaningful
from processors.language_detector import detect_language, is_supported_language, get_model_for_language
from processors.entity_extractor import EntityExtractor
from sentiment.hf_client import HuggingFaceClient, normalize_to_float, ROBERTA_LABEL_MAP, FINBERT_LABEL_MAP

logger = logging.getLogger(__name__)

BATCH_SIZE = 20        # HF API rate limit safe batch size
MAX_TEXT_LENGTH = 512  # Token cap

# Lazy-loaded clients
_english_client     = None
_multilingual_client = None


def _get_english_client() -> HuggingFaceClient:
    global _english_client
    if _english_client is None:
        _english_client = HuggingFaceClient(
            settings.sentiment_model, label_map=ROBERTA_LABEL_MAP
        )
    return _english_client


def _get_multilingual_client() -> HuggingFaceClient:
    global _multilingual_client
    if _multilingual_client is None:
        _multilingual_client = HuggingFaceClient(
            settings.multilingual_model, label_map=ROBERTA_LABEL_MAP
        )
    return _multilingual_client


def _score_texts_local(texts: List[str]) -> List[dict]:
    """Score texts using the local RoBERTa pipeline (no API key needed)."""
    from services.nlp_inference import get_nlp_service
    svc = get_nlp_service()
    if not svc.is_ready():
        logger.warning("Local RoBERTa not ready — returning neutral defaults")
        return [{"label": "NEUTRAL", "score": 0.5}] * len(texts)

    results = svc.score_texts(texts)
    # Convert NLPInferenceService format → HuggingFaceClient format
    mapped = []
    for r in results:
        label = r.get("label_name", "NEUTRAL")
        # Use the winning probability as confidence
        if label == "NEGATIVE":
            conf = r.get("p_negative", 0.5)
        elif label == "POSITIVE":
            conf = r.get("p_positive", 0.5)
        else:
            conf = r.get("p_neutral", 0.5)
        mapped.append({"label": label, "score": conf})
    return mapped


def _compute_engagement_score(upvotes: int, retweets: int) -> float:
    """
    Normalize raw engagement to a 0–1 score using log scaling.
    Prevents viral posts from totally dominating the average.
    """
    total = max(upvotes + retweets, 0)
    if total == 0:
        return 0.1
    return round(min(math.log1p(total) / 10.0, 1.0), 4)


def _floor_to_hour(dt: datetime) -> datetime:
    return dt.replace(minute=0, second=0, microsecond=0) if dt else datetime.utcnow().replace(minute=0, second=0, microsecond=0)


class SentimentScorer:
    def __init__(self):
        self.extractor = EntityExtractor()

    def process_unscored_raw(self, limit: int = 500) -> int:
        """
        Phase 1: Pick up unprocessed raw posts → clean → extract entities → create ProcessedPost.
        Returns number of ProcessedPosts created.
        """
        created = 0
        with get_db_session() as db:
            raw_posts = db.query(RawPost).filter_by(processed=False).limit(limit).all()
            logger.info(f"Processing {len(raw_posts)} raw posts...")

            for raw in raw_posts:
                try:
                    clean = clean_text(raw.body)
                    if not is_meaningful(clean):
                        raw.processed = True
                        continue

                    lang = detect_language(clean)
                    if not is_supported_language(lang):
                        raw.processed = True
                        continue

                    entities = self.extractor.extract_all(clean)

                    # Get politician influence weight if applicable
                    influence = 1.0
                    if raw.politician_id:
                        pol = db.query(Politician).filter_by(id=raw.politician_id).first()
                        if pol:
                            influence = pol.influence_weight

                    engagement = _compute_engagement_score(raw.upvotes or 0, raw.retweet_count or 0)

                    processed = ProcessedPost(
                        raw_post_id=raw.id,
                        clean_text=clean[:2000],
                        language=lang,
                        is_english=(lang == "en"),
                        mentioned_countries=entities["countries"],
                        mentioned_persons=entities["persons"],
                        source=raw.source,
                        author=raw.author,
                        author_verified=raw.author_verified or False,
                        influence_weight=influence,
                        engagement_score=engagement,
                        politician_id=raw.politician_id,
                        posted_at=raw.posted_at,
                        time_bucket=_floor_to_hour(raw.posted_at or datetime.utcnow()),
                    )
                    db.add(processed)
                    raw.processed = True
                    created += 1

                except Exception as e:
                    logger.error(f"Error processing raw post {raw.id}: {e}")
                    raw.processed = True   # Mark done to avoid infinite loop

        logger.info(f"ProcessedPost rows created: {created}")
        return created

    def score_batch(self, posts: List[ProcessedPost]) -> int:
        """Score a batch of ProcessedPost objects. Returns number scored."""
        if not posts:
            return 0

        use_local = not settings.huggingface_api_key

        if use_local:
            # ── Local RoBERTa pipeline (no API key needed) ────────────────
            texts = [p.clean_text[:MAX_TEXT_LENGTH] for p in posts]
            results = _score_texts_local(texts)

            scored = 0
            with get_db_session() as db:
                for post, result in zip(posts, results):
                    if result is None:
                        continue
                    try:
                        pp = db.query(ProcessedPost).filter_by(id=post.id).first()
                        if not pp:
                            continue
                        pp.sentiment_label      = result["label"]
                        pp.sentiment_confidence = round(result["score"], 4)
                        pp.sentiment_score      = normalize_to_float(
                            result["label"], result["score"]
                        )
                        pp.sentiment_model      = settings.nlp_roberta_model
                        pp.sentiment_scored     = True

                        raw = db.query(RawPost).filter_by(id=pp.raw_post_id).first()
                        if raw:
                            raw.sentiment_scored = True

                        scored += 1
                    except Exception as e:
                        logger.error(f"Error saving score for post {post.id}: {e}")
            return scored

        # ── HuggingFace API path (when key is set) ────────────────────────
        # Split by language
        english = [(i, p) for i, p in enumerate(posts) if p.is_english]
        multilingual = [(i, p) for i, p in enumerate(posts) if not p.is_english]

        scores = [None] * len(posts)

        # Score English posts
        if english:
            client = _get_english_client()
            idxs, eng_posts = zip(*english)
            texts = [p.clean_text[:MAX_TEXT_LENGTH] for p in eng_posts]
            results = client.score_texts(list(texts))
            for idx, result in zip(idxs, results):
                scores[idx] = result

        # Score multilingual posts
        if multilingual:
            client = _get_multilingual_client()
            idxs, multi_posts = zip(*multilingual)
            texts = [p.clean_text[:MAX_TEXT_LENGTH] for p in multi_posts]
            results = client.score_texts(list(texts))
            for idx, result in zip(idxs, results):
                scores[idx] = result

        # Write scores back
        scored = 0
        with get_db_session() as db:
            for post, score_result in zip(posts, scores):
                if score_result is None:
                    continue
                try:
                    pp = db.query(ProcessedPost).filter_by(id=post.id).first()
                    if not pp:
                        continue
                    pp.sentiment_label      = score_result["label"]
                    pp.sentiment_confidence = round(score_result["score"], 4)
                    pp.sentiment_score      = normalize_to_float(
                        score_result["label"], score_result["score"]
                    )
                    pp.sentiment_model      = settings.sentiment_model
                    pp.sentiment_scored     = True

                    # Also update the parent raw post
                    raw = db.query(RawPost).filter_by(id=pp.raw_post_id).first()
                    if raw:
                        raw.sentiment_scored = True

                    scored += 1
                except Exception as e:
                    logger.error(f"Error saving score for post {post.id}: {e}")

        return scored

    def run(self) -> int:
        """
        Main entry point — called by scheduler every hour.
        1. Process unscored raw posts → ProcessedPost
        2. Batch-score all unscored ProcessedPosts
        Returns total posts scored.
        """
        logger.info("Sentiment scorer starting...")

        # Step 1: preprocessing
        self.process_unscored_raw()

        # Step 2: scoring
        total_scored = 0
        with get_db_session() as db:
            unscored = db.query(ProcessedPost).filter_by(sentiment_scored=False).all()
            logger.info(f"Scoring {len(unscored)} unscored posts...")

        # Re-fetch in batches (outside session to avoid timeout)
        offset = 0
        while True:
            with get_db_session() as db:
                batch = db.query(ProcessedPost).filter_by(
                    sentiment_scored=False
                ).limit(BATCH_SIZE).offset(offset).all()
                if not batch:
                    break
                # Detach objects
                batch_data = [
                    type("P", (), {
                        "id": p.id, "clean_text": p.clean_text,
                        "is_english": p.is_english, "raw_post_id": p.raw_post_id
                    })()
                    for p in batch
                ]

            scored = self.score_batch(batch_data)
            total_scored += scored
            offset += BATCH_SIZE
            logger.debug(f"Scored batch at offset {offset}: {scored} posts")

            if len(batch) < BATCH_SIZE:
                break

        logger.info(f"Sentiment scorer done. Total scored: {total_scored}")
        return total_scored

