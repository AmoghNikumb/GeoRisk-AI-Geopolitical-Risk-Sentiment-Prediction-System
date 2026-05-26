"""
Apify Twitter Ingestion Pipeline.

Reads pre-scraped Apify Twitter dataset files (JSON arrays) and ingests
them into the GeoRisk AI platform's raw_posts table.
"""

from __future__ import annotations

import dataclasses
import json
import logging
import time
from datetime import datetime
from pathlib import Path

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db_session
from models.country import Country
from models.politician import Politician
from models.raw_post import RawPost

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class IngestionSummary:
    """Summary of a single ingestion run for one dataset file."""

    file_path: str
    total_parsed: int
    inserted: int
    duplicates: int
    skipped: int
    elapsed_seconds: float

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


class ApifyIngester:
    """Ingests Apify Twitter dataset files into the GeoRisk AI platform."""

    def __init__(self) -> None:
        # Cached set of valid ISO-3166-1 alpha-2 country codes, lazy-loaded.
        self._known_codes: set[str] = set()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_file(self, path: Path) -> list[dict]:
        """Read an Apify dataset file and return a list of raw tweet dicts.

        Args:
            path: Path to a ``.txt`` or ``.json`` file containing a JSON array
                  of Apify tweet objects.

        Returns:
            A list of tweet dicts (may be empty).

        Raises:
            FileNotFoundError: If *path* does not exist (propagated from open).
            ValueError: If the file cannot be parsed as JSON, or if the
                        top-level JSON value is not an array.
        """
        with open(path, encoding="utf-8") as fh:
            try:
                result = json.load(fh)
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse {path}: {e}") from e

        if not isinstance(result, list):
            raise ValueError(f"{path} does not contain a JSON array")

        if len(result) == 0:
            logger.warning("File %s contains an empty JSON array", path)
            return []

        return result

    def map_tweet(self, tweet: dict) -> dict | None:
        """Map a single Apify tweet dict to a RawPost-compatible dict.

        Returns ``None`` if the tweet should be skipped (e.g. body too short).
        """
        # Extract body and skip if too short
        body = tweet["text"]
        if len(body.strip()) < 15:
            logger.debug(
                "Skipping tweet %s: body too short (%d chars)",
                tweet.get("id", "<unknown>"),
                len(body.strip()),
            )
            return None

        # Build post_id
        post_id = "twitter_" + tweet["id"]

        # Parse createdAt; fall back to utcnow() on failure
        raw_created_at = tweet.get("createdAt", "")
        try:
            posted_at = datetime.strptime(raw_created_at, "%a %b %d %H:%M:%S +0000 %Y")
        except (ValueError, TypeError):
            logger.warning(
                "Cannot parse createdAt for tweet %s: %r — falling back to utcnow()",
                tweet.get("id", "<unknown>"),
                raw_created_at,
            )
            posted_at = datetime.utcnow()

        # Map all fields per the Field Mapping table
        author = tweet["author"]
        return {
            "post_id": post_id,
            "source": "twitter",
            "body": body,
            "author": "@" + author["username"],
            "author_verified": author["verified"],
            "upvotes": tweet.get("likeCount", 0),
            "retweet_count": tweet.get("retweetCount", 0),
            "reply_count": tweet.get("replyCount", 0),
            "url": tweet["url"],
            "language": tweet["lang"],
            "posted_at": posted_at,
            "scraped_at": datetime.utcnow(),
            "processed": False,
            "sentiment_scored": False,
            "title": None,
            "subreddit": None,
        }

    def register_politician(self, author: dict, db: Session) -> int | None:
        """Look up or create a Politician row for *author*.

        Returns the politician's primary-key id, or ``None`` on failure.
        """
        handle = "@" + author["username"]

        # Fast path: politician already exists
        politician = db.query(Politician).filter_by(twitter_handle=handle).first()
        if politician is not None:
            return politician.id

        # Resolve country code from the author's location field
        country_code = self._resolve_country_code(
            author.get("location", ""),
            db,
            username=author["username"],
        )

        # Create a new Politician row
        politician = Politician(
            twitter_handle=handle,
            name=author["name"],
            title=None,
            country_code=country_code,
            influence_weight=0.5,
            is_verified=author["verified"],
            is_active=True,
        )
        db.add(politician)
        try:
            db.flush()
            return politician.id
        except IntegrityError:
            # Race condition: another process inserted the same handle
            db.rollback()
            existing = db.query(Politician).filter_by(twitter_handle=handle).first()
            return existing.id if existing is not None else None

    def _resolve_country_code(
        self, location: str, db: Session, username: str = ""
    ) -> str | None:
        """Resolve a free-text location string to an ISO-3166-1 alpha-2 code.

        Resolution is attempted in three steps:
        1. Direct two-letter code match (e.g. ``"GB"`` → ``"GB"``).
        2. Country name / full_name substring match (case-insensitive).
        3. Returns ``None`` and logs a WARNING if no match is found.

        The set of valid codes is loaded from the ``countries`` table on the
        first call and cached on the instance for subsequent calls.
        """
        # Lazy-load all country rows on first call
        if not self._known_codes:
            countries: list[Country] = db.query(Country).all()
            self._known_codes = {c.code for c in countries}
            # Store full country objects for name matching
            self._country_rows: list[Country] = countries
        else:
            # Ensure _country_rows is populated (may be missing if _known_codes
            # was pre-populated externally, e.g. in tests)
            if not hasattr(self, "_country_rows"):
                self._country_rows = db.query(Country).all()

        stripped = location.strip()

        # Step 1: direct two-letter code match
        if len(stripped) == 2:
            candidate = stripped.upper()
            if candidate in self._known_codes:
                return candidate

        # Step 2: country name / full_name substring match (case-insensitive)
        location_lower = location.lower()
        for country in self._country_rows:
            if country.name and country.name.lower() in location_lower:
                return country.code
            if country.full_name and country.full_name.lower() in location_lower:
                return country.code

        # Step 3: no match
        logger.warning(
            "Cannot resolve country code for @%s location='%s'",
            username,
            location,
        )
        return None

    def ingest(self, file_path: Path) -> IngestionSummary:
        """Orchestrate the full ingestion run for one dataset file.

        Returns an :class:`IngestionSummary` with counters for inserted,
        duplicate, and skipped tweets.
        """
        start_time = time.monotonic()

        tweets = self.load_file(file_path)
        total_tweets = len(tweets)
        logger.info("Ingesting file %s — %d tweets found", file_path, total_tweets)

        inserted = 0
        duplicates = 0
        skipped = 0
        total_parsed = 0

        def _process_tweet(tweet: dict) -> None:
            """Process a single tweet dict (top-level or quoted). Updates counters."""
            nonlocal inserted, duplicates, skipped, total_parsed

            total_parsed += 1

            mapped = self.map_tweet(tweet)
            if mapped is None:
                logger.debug(
                    "Skipping tweet %s: map_tweet returned None",
                    tweet.get("id", "<unknown>"),
                )
                skipped += 1
                return

            try:
                with get_db_session() as db:
                    politician_id = self.register_politician(tweet["author"], db)
                    mapped["politician_id"] = politician_id
                    try:
                        db.add(RawPost(**mapped))
                        db.flush()
                        inserted += 1
                    except IntegrityError:
                        db.rollback()
                        logger.debug(
                            "Duplicate tweet %s — skipping",
                            tweet.get("id", "<unknown>"),
                        )
                        duplicates += 1
            except IntegrityError:
                # IntegrityError that escaped the inner try (shouldn't normally happen)
                logger.debug(
                    "Duplicate tweet %s (outer) — skipping",
                    tweet.get("id", "<unknown>"),
                )
                duplicates += 1
            except Exception as e:
                logger.error(
                    "Error processing tweet %s: %s",
                    tweet.get("id", "<unknown>"),
                    e,
                )
                skipped += 1

        for tweet in tweets:
            _process_tweet(tweet)

            # Also process quoted tweet if present
            quoted = tweet.get("quoted_tweet")
            if quoted:
                _process_tweet(quoted)

        elapsed = time.monotonic() - start_time

        logger.info(
            "Ingestion complete for %s — inserted=%d, duplicates=%d, skipped=%d, elapsed=%.3fs",
            file_path.name,
            inserted,
            duplicates,
            skipped,
            elapsed,
        )

        return IngestionSummary(
            file_path=str(file_path),
            total_parsed=total_parsed,
            inserted=inserted,
            duplicates=duplicates,
            skipped=skipped,
            elapsed_seconds=elapsed,
        )
