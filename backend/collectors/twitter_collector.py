"""
collectors/twitter_collector.py
Scrapes tweets from tracked politicians + keyword searches.
Uses ntscraper (no API key required).
Runs every 30 minutes via APScheduler.
"""
import logging
import json
import os
from datetime import datetime
from typing import List, Optional

from ntscraper import Nitter

from config import settings
from database import get_db_session
from models.raw_post import RawPost
from models.politician import Politician

logger = logging.getLogger(__name__)

# Geopolitical keyword searches on Twitter
KEYWORD_SEARCHES = [
    "war", "sanctions", "military strike",
    "nuclear", "ceasefire", "conflict",
    "invasion", "airstrike", "diplomacy failed",
    "trade war", "missile", "coup",
]

TWEETS_PER_POLITICIAN = 10
TWEETS_PER_KEYWORD    = 15


class TwitterCollector:
    def __init__(self):
        # ntscraper uses Nitter instances — no API key needed
        self.scraper = Nitter(log_level=1, skip_instance_check=False)
        self._load_politicians()
        logger.info("TwitterCollector initialized.")

    def _load_politicians(self):
        """Load tracked politicians from DB."""
        with get_db_session() as db:
            self.politicians = db.query(Politician).filter_by(is_active=True).all()
            # Detach from session for use outside context
            self.politician_map = {
                p.twitter_handle.lstrip("@"): {
                    "id": p.id,
                    "weight": p.influence_weight,
                    "verified": p.is_verified,
                    "country_code": p.country_code,
                }
                for p in self.politicians
            }
        logger.info(f"Loaded {len(self.politician_map)} politicians for tracking.")

    def _tweet_to_raw(self, tweet: dict, politician_meta: Optional[dict] = None) -> Optional[dict]:
        """Convert a ntscraper tweet dict into a RawPost-ready dict."""
        try:
            body = tweet.get("text", "").strip()
            if len(body) < 15:
                return None

            tweet_id = tweet.get("link", "").split("/status/")[-1].split("?")[0]
            if not tweet_id:
                return None

            post_id = f"twitter_{tweet_id}"
            author = tweet.get("user", {}).get("username", "unknown")

            # Parse date
            date_str = tweet.get("date", "")
            try:
                posted_at = datetime.strptime(date_str, "%b %d, %Y · %I:%M %p UTC")
            except Exception:
                posted_at = datetime.utcnow()

            likes = int(tweet.get("stats", {}).get("likes", 0) or 0)
            retweets = int(tweet.get("stats", {}).get("retweets", 0) or 0)
            comments = int(tweet.get("stats", {}).get("comments", 0) or 0)

            return {
                "source": "twitter",
                "post_id": post_id,
                "url": tweet.get("link", ""),
                "title": None,
                "body": body,
                "author": f"@{author}",
                "author_verified": politician_meta["verified"] if politician_meta else False,
                "upvotes": likes,
                "retweet_count": retweets,
                "reply_count": comments,
                "politician_id": politician_meta["id"] if politician_meta else None,
                "posted_at": posted_at,
            }
        except Exception as e:
            logger.warning(f"Error parsing tweet: {e}")
            return None

    def _save_posts(self, posts: List[dict]) -> int:
        saved = 0
        with get_db_session() as db:
            for post_data in posts:
                exists = db.query(RawPost).filter_by(post_id=post_data["post_id"]).first()
                if exists:
                    continue
                db.add(RawPost(**post_data))
                saved += 1
        logger.info(f"Twitter: saved {saved} new tweets.")
        return saved

    def scrape_politicians(self) -> List[dict]:
        """Scrape last N tweets from each tracked politician."""
        posts = []
        for handle, meta in self.politician_map.items():
            try:
                result = self.scraper.get_tweets(handle, mode="user", number=TWEETS_PER_POLITICIAN)
                tweets = result.get("tweets", [])
                for tweet in tweets:
                    post = self._tweet_to_raw(tweet, politician_meta=meta)
                    if post:
                        posts.append(post)
                logger.debug(f"Scraped @{handle}: {len(tweets)} tweets")
            except Exception as e:
                logger.error(f"Failed to scrape @{handle}: {e}")
        return posts

    def scrape_keywords(self) -> List[dict]:
        """Search Twitter for geopolitical keywords."""
        posts = []
        for keyword in KEYWORD_SEARCHES:
            try:
                result = self.scraper.get_tweets(
                    keyword, mode="term", number=TWEETS_PER_KEYWORD
                )
                tweets = result.get("tweets", [])
                for tweet in tweets:
                    post = self._tweet_to_raw(tweet)
                    if post:
                        posts.append(post)
                logger.debug(f"Keyword '{keyword}': {len(tweets)} tweets")
            except Exception as e:
                logger.error(f"Twitter keyword '{keyword}' failed: {e}")
        return posts

    def run(self) -> int:
        """Main entry point — called by scheduler every 30 mins."""
        logger.info("Twitter collector starting...")
        # Reload politicians in case DB changed
        self._load_politicians()

        all_posts = []
        all_posts.extend(self.scrape_politicians())
        all_posts.extend(self.scrape_keywords())

        # In-memory dedup
        seen, unique = set(), []
        for p in all_posts:
            if p["post_id"] not in seen:
                seen.add(p["post_id"])
                unique.append(p)

        saved = self._save_posts(unique)
        logger.info(f"Twitter collector done. {saved} new tweets saved.")
        return saved

