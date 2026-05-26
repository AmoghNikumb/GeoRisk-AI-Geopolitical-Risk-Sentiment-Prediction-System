"""
collectors/apify_collector.py
─────────────────────────────
Live Twitter/X data collection via the Apify platform.

Calls the configured Apify actor (default: apidojo/tweet-scraper), waits for
the run to finish, fetches the dataset items, normalises them into the Apify
tweet format expected by ApifyIngester.map_tweet(), and persists them to the
raw_posts table.

Requires:
    pip install apify-client==1.*

Configuration (via .env):
    APIFY_API_KEY          — your Apify API token
    APIFY_TWITTER_ACTOR    — actor id (default: apidojo/tweet-scraper)
    APIFY_MAX_TWEETS       — max tweets per run (default: 100)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from config import settings
from collectors.apify_ingester import ApifyIngester, IngestionSummary
from database import get_db_session
from models.politician import Politician
from models.raw_post import RawPost
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Geopolitical search queries sent to the actor on each scheduled run.
# These mirror the keyword list in twitter_collector.py so both collectors
# cover the same topic space.
# ---------------------------------------------------------------------------
GEOPOLITICAL_QUERIES = [
    "war sanctions",
    "military strike",
    "nuclear ceasefire",
    "conflict invasion",
    "airstrike diplomacy",
    "trade war missile",
    "coup geopolitical",
    "NATO Russia China",
    "Middle East conflict",
    "Ukraine war",
]


class ApifyCollector:
    """Fetches live tweets from Apify and ingests them into raw_posts."""

    def __init__(self) -> None:
        if not settings.apify_api_key:
            raise RuntimeError(
                "APIFY_API_KEY is not set. Add it to your .env file."
            )
        # Import here so the module loads even if apify-client isn't installed
        # (the ImportError surfaces only when the collector is actually used).
        try:
            from apify_client import ApifyClient
        except ImportError as exc:
            raise ImportError(
                "apify-client is not installed. Run: pip install apify-client"
            ) from exc

        self._client = ApifyClient(settings.apify_api_key)
        self._ingester = ApifyIngester()
        logger.info(
            "ApifyCollector initialised (actor=%s, max_tweets=%d)",
            settings.apify_twitter_actor,
            settings.apify_max_tweets,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> int:
        """Fetch tweets from Apify and persist them.  Returns inserted count."""
        logger.info("ApifyCollector starting live scrape run…")

        raw_items = self._fetch_from_apify()
        if not raw_items:
            logger.info("ApifyCollector: no items returned from actor run.")
            return 0

        logger.info("ApifyCollector: %d items fetched, normalising…", len(raw_items))
        normalised = [self._normalise(item) for item in raw_items]
        normalised = [t for t in normalised if t is not None]

        inserted = self._persist(normalised)
        logger.info(
            "ApifyCollector done — %d/%d tweets inserted.",
            inserted,
            len(normalised),
        )
        return inserted

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fetch_from_apify(self) -> list[dict]:
        """Run the Apify actor and return the dataset items."""
        actor_input = self._build_actor_input()
        logger.debug("Running actor %s with input: %s", settings.apify_twitter_actor, actor_input)

        try:
            run = self._client.actor(settings.apify_twitter_actor).call(
                run_input=actor_input,
                # wait_secs=None means block until the run finishes (up to
                # Apify's default timeout of ~3600 s).
            )
        except Exception as exc:
            logger.error("Apify actor run failed: %s", exc)
            return []

        if run is None:
            logger.error("Apify actor returned None — run may have failed.")
            return []

        dataset_id = run.get("defaultDatasetId")
        if not dataset_id:
            logger.error("Apify run has no defaultDatasetId: %s", run)
            return []

        try:
            result = self._client.dataset(dataset_id).list_items()
            return result.items if result else []
        except Exception as exc:
            logger.error("Failed to fetch Apify dataset %s: %s", dataset_id, exc)
            return []

    def _build_actor_input(self) -> dict:
        """Build the input payload for the apidojo/tweet-scraper actor.

        The actor accepts ``searchTerms`` (list of query strings) and
        ``maxItems`` to cap the result set.  Other actors may use different
        field names — adjust here if you switch actors.
        """
        return {
            "searchTerms": GEOPOLITICAL_QUERIES,
            "maxItems": settings.apify_max_tweets,
            "queryType": "Latest",          # "Latest" | "Top" | "People" | …
            "lang": "en",
        }

    def _normalise(self, item: dict) -> dict | None:
        """Convert an apidojo/tweet-scraper item to the ApifyIngester tweet format.

        The apidojo actor returns a slightly different field layout than the
        Apify dataset files produced by other actors.  This method bridges the
        gap so we can reuse ApifyIngester.map_tweet() unchanged.

        Returns None if the item is missing required fields.
        """
        try:
            # apidojo/tweet-scraper field names
            tweet_id = str(item.get("id") or item.get("tweet_id") or "")
            text = item.get("text") or item.get("full_text") or ""
            if not tweet_id or not text:
                return None

            # Author block — apidojo nests this under "author" or "user"
            raw_author = item.get("author") or item.get("user") or {}
            author = {
                "username": raw_author.get("userName") or raw_author.get("username") or raw_author.get("screen_name") or "unknown",
                "name": raw_author.get("name") or raw_author.get("displayName") or "Unknown",
                "verified": bool(raw_author.get("isVerified") or raw_author.get("verified") or False),
                "location": raw_author.get("location") or "",
            }

            # Timestamps — apidojo uses ISO-8601; convert to the Twitter
            # createdAt format that ApifyIngester.map_tweet() expects.
            created_raw = item.get("createdAt") or item.get("created_at") or ""
            created_at = self._to_twitter_date(created_raw)

            return {
                "id": tweet_id,
                "text": text,
                "createdAt": created_at,
                "author": author,
                "likeCount": int(item.get("likeCount") or item.get("favorite_count") or 0),
                "retweetCount": int(item.get("retweetCount") or item.get("retweet_count") or 0),
                "replyCount": int(item.get("replyCount") or item.get("reply_count") or 0),
                "url": item.get("url") or item.get("twitterUrl") or f"https://twitter.com/i/web/status/{tweet_id}",
                "lang": item.get("lang") or "en",
                # Preserve quoted tweet if present
                "quoted_tweet": item.get("quoted_tweet") or item.get("quotedTweet"),
            }
        except Exception as exc:
            logger.warning("Failed to normalise Apify item: %s — %s", item.get("id"), exc)
            return None

    @staticmethod
    def _to_twitter_date(raw: str) -> str:
        """Convert an ISO-8601 timestamp to Twitter's createdAt format.

        ApifyIngester.map_tweet() parses: ``"%a %b %d %H:%M:%S +0000 %Y"``
        e.g. ``"Mon Jan 01 12:00:00 +0000 2024"``

        If conversion fails, returns the raw string (map_tweet will fall back
        to utcnow()).
        """
        if not raw:
            return ""
        # Try ISO-8601 variants: "2024-01-15T12:30:00.000Z" or "2024-01-15T12:30:00Z"
        for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S+00:00"):
            try:
                dt = datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
                return dt.strftime("%a %b %d %H:%M:%S +0000 %Y")
            except ValueError:
                continue
        # Already in Twitter format or unrecognised — return as-is
        return raw

    def _persist(self, tweets: list[dict]) -> int:
        """Persist normalised tweet dicts via ApifyIngester's per-tweet logic.

        Reuses map_tweet + register_politician + deduplication from the
        existing ingester rather than duplicating that logic here.
        """
        inserted = 0
        for tweet in tweets:
            mapped = self._ingester.map_tweet(tweet)
            if mapped is None:
                continue
            try:
                with get_db_session() as db:
                    politician_id = self._ingester.register_politician(tweet["author"], db)
                    mapped["politician_id"] = politician_id
                    try:
                        db.add(RawPost(**mapped))
                        db.flush()
                        inserted += 1
                    except IntegrityError:
                        db.rollback()
                        logger.debug("Duplicate tweet %s — skipping", tweet.get("id"))
            except Exception as exc:
                logger.error("Error persisting tweet %s: %s", tweet.get("id"), exc)
        return inserted
