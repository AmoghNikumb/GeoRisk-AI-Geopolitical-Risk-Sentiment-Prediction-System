"""
processors/aggregator.py
Aggregates processed post sentiment into per-country per-hour buckets.
Produces rows in the sentiment_scores table.
Runs every hour via APScheduler.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional

import numpy as np
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db_session
from models.processed_post import ProcessedPost
from models.sentiment_score import SentimentScore

logger = logging.getLogger(__name__)

# How many hours back to aggregate in one run
AGGREGATE_HOURS_BACK = 3


def _floor_to_hour(dt: datetime) -> datetime:
    """Truncate datetime to the hour: 14:37 → 14:00."""
    return dt.replace(minute=0, second=0, microsecond=0)


def _compute_volume_spike(post_count: int, country_code: str,
                          time_bucket: datetime, db: Session) -> float:
    """
    Compute Z-score of current post count vs 7-day hourly average.
    A Z-score > 2 means abnormally high volume → spike signal.
    """
    try:
        week_ago = time_bucket - timedelta(days=7)
        historical = db.query(SentimentScore.post_count).filter(
            SentimentScore.country_code == country_code,
            SentimentScore.time_bucket >= week_ago,
            SentimentScore.time_bucket < time_bucket,
        ).all()
        counts = [r[0] for r in historical if r[0] is not None]
        if len(counts) < 5:
            return 0.0
        mean = np.mean(counts)
        std  = np.std(counts)
        if std == 0:
            return 0.0
        z = (post_count - mean) / std
        return round(float(z), 3)
    except Exception:
        return 0.0


class SentimentAggregator:

    def aggregate_hour(self, time_bucket: datetime) -> int:
        """
        Aggregate all processed posts for a given hour bucket.
        Returns number of SentimentScore rows created/updated.
        """
        bucket_end = time_bucket + timedelta(hours=1)
        created = 0

        with get_db_session() as db:
            # Get all countries mentioned in this hour
            rows = db.query(
                ProcessedPost
            ).filter(
                ProcessedPost.time_bucket == time_bucket,
                ProcessedPost.sentiment_scored == True,  # noqa: E712
            ).all()

            if not rows:
                logger.debug(f"No scored posts in bucket {time_bucket}")
                return 0

            # Group by country
            country_posts: dict = {}
            for post in rows:
                for country in (post.mentioned_countries or []):
                    if country not in country_posts:
                        country_posts[country] = []
                    country_posts[country].append(post)

            for country_code, posts in country_posts.items():
                scores = [p.sentiment_score for p in posts if p.sentiment_score is not None]
                if not scores:
                    continue

                # Weighted sentiment (by engagement_score × influence_weight)
                weights = [
                    max((p.engagement_score or 0.1) * (p.influence_weight or 1.0), 0.01)
                    for p in posts if p.sentiment_score is not None
                ]
                weighted_avg = float(np.average(scores, weights=weights))

                # Politician vs public breakdown
                politician_scores = [p.sentiment_score for p in posts
                                     if p.source == "twitter" and p.author_verified
                                     and p.sentiment_score is not None]
                public_scores = [p.sentiment_score for p in posts
                                 if p.source == "reddit"
                                 and p.sentiment_score is not None]
                twitter_scores = [p.sentiment_score for p in posts
                                  if p.source == "twitter"
                                  and p.sentiment_score is not None]

                # Negative ratio
                negative_count = sum(1 for s in scores if s < -0.2)
                negative_ratio = negative_count / len(scores)

                # High hostility count (score < -0.7)
                high_hostility = sum(1 for s in scores if s < -0.7)

                # Previous bucket delta
                prev_bucket = time_bucket - timedelta(hours=1)
                prev_score_row = db.query(SentimentScore).filter_by(
                    country_code=country_code, time_bucket=prev_bucket
                ).first()
                prev_avg = prev_score_row.avg_sentiment if prev_score_row else None
                delta = round(float(np.mean(scores)) - prev_avg, 4) if prev_avg is not None else 0.0

                # Volume spike Z-score
                spike = _compute_volume_spike(len(posts), country_code, time_bucket, db)

                # Check if row already exists for this bucket
                existing = db.query(SentimentScore).filter_by(
                    country_code=country_code, time_bucket=time_bucket
                ).first()

                score_obj = existing or SentimentScore(
                    country_code=country_code,
                    time_bucket=time_bucket,
                )

                score_obj.avg_sentiment         = round(float(np.mean(scores)), 4)
                score_obj.weighted_sentiment     = round(weighted_avg, 4)
                score_obj.sentiment_delta        = delta
                score_obj.politician_sentiment   = round(float(np.mean(politician_scores)), 4) if politician_scores else None
                score_obj.public_sentiment       = round(float(np.mean(public_scores)), 4) if public_scores else None
                score_obj.twitter_sentiment      = round(float(np.mean(twitter_scores)), 4) if twitter_scores else None
                score_obj.reddit_sentiment       = round(float(np.mean(public_scores)), 4) if public_scores else None
                score_obj.post_count             = len(posts)
                score_obj.twitter_count          = len([p for p in posts if p.source == "twitter"])
                score_obj.reddit_count           = len([p for p in posts if p.source == "reddit"])
                score_obj.post_volume_spike      = spike
                score_obj.negative_ratio         = round(negative_ratio, 4)
                score_obj.high_hostility_count   = high_hostility
                score_obj.computed_at            = datetime.utcnow()

                if not existing:
                    db.add(score_obj)
                    created += 1

        return created

    def run(self) -> int:
        """
        Main entry point — called by scheduler every hour.
        Aggregates the last AGGREGATE_HOURS_BACK hours.
        """
        logger.info("Sentiment aggregator starting...")
        total = 0
        now = datetime.utcnow()

        for h in range(AGGREGATE_HOURS_BACK):
            bucket = _floor_to_hour(now - timedelta(hours=h))
            count = self.aggregate_hour(bucket)
            total += count
            logger.debug(f"Aggregated bucket {bucket}: {count} country scores")

        logger.info(f"Aggregator done: {total} sentiment score rows created.")
        return total

