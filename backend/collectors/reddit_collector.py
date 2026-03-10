"""
collectors/reddit_collector.py
Scrapes top posts from geopolitical subreddits using PRAW.
Runs every 30 minutes via APScheduler.
"""
import logging
from datetime import datetime
from typing import List, Optional

import praw
from praw.models import Submission

from config import settings
from database import get_db_session
from models.raw_post import RawPost

logger = logging.getLogger(__name__)

# Subreddits to monitor
TARGET_SUBREDDITS = [
    "worldnews",
    "geopolitics",
    "news",
    "europe",
    "MiddleEast",
    "china",
    "russia",
    "india",
    "pakistan",
    "UkraineWarVideoReport",
    "ukraine",
    "IsraelPalestine",
    "iran",
    "NorthKorea",
    "geopoliticsmasters",
]

# Keywords to search across Reddit
KEYWORD_SEARCHES = [
    "war sanctions",
    "military conflict",
    "nuclear threat",
    "ceasefire negotiations",
    "border tension",
    "trade war",
    "diplomatic crisis",
]

POSTS_PER_SUB = 50       # Top N posts per subreddit per run
KEYWORD_POSTS = 20       # Posts per keyword search


class RedditCollector:
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            user_agent=settings.reddit_user_agent,
            read_only=True,
        )
        logger.info("RedditCollector initialized.")

    def _submission_to_raw(self, sub: Submission, source_tag: str = "subreddit") -> Optional[dict]:
        """Convert a PRAW Submission into a dict ready for RawPost."""
        try:
            body = (sub.selftext or "").strip()
            if not body:
                body = sub.title   # Use title if no body text

            if len(body) < 20:     # Skip very short posts
                return None

            return {
                "source": "reddit",
                "post_id": f"reddit_{sub.id}",
                "url": f"https://reddit.com{sub.permalink}",
                "title": sub.title,
                "body": f"{sub.title}. {body}".strip(),
                "author": f"u/{sub.author.name}" if sub.author else "u/[deleted]",
                "author_verified": False,
                "upvotes": max(sub.score, 0),
                "retweet_count": sub.num_comments,
                "subreddit": sub.subreddit.display_name,
                "posted_at": datetime.utcfromtimestamp(sub.created_utc),
            }
        except Exception as e:
            logger.warning(f"Error parsing submission {sub.id}: {e}")
            return None

    def _save_posts(self, posts: List[dict]) -> int:
        """Insert new posts to DB, skip duplicates. Returns count of new rows."""
        saved = 0
        with get_db_session() as db:
            for post_data in posts:
                exists = db.query(RawPost).filter_by(post_id=post_data["post_id"]).first()
                if exists:
                    continue
                row = RawPost(**post_data)
                db.add(row)
                saved += 1
        logger.info(f"Reddit: saved {saved} new posts (skipped {len(posts) - saved} duplicates).")
        return saved

    def scrape_subreddits(self) -> List[dict]:
        """Scrape top posts from all target subreddits."""
        posts = []
        for sub_name in TARGET_SUBREDDITS:
            try:
                subreddit = self.reddit.subreddit(sub_name)
                for submission in subreddit.new(limit=POSTS_PER_SUB):
                    post = self._submission_to_raw(submission)
                    if post:
                        posts.append(post)
                logger.debug(f"Scraped r/{sub_name}")
            except Exception as e:
                logger.error(f"Failed to scrape r/{sub_name}: {e}")
        return posts

    def scrape_keywords(self) -> List[dict]:
        """Search Reddit for geopolitical keywords."""
        posts = []
        for query in KEYWORD_SEARCHES:
            try:
                for submission in self.reddit.subreddit("all").search(
                    query, sort="new", time_filter="day", limit=KEYWORD_POSTS
                ):
                    post = self._submission_to_raw(submission, source_tag="keyword")
                    if post:
                        posts.append(post)
                logger.debug(f"Keyword search '{query}' done.")
            except Exception as e:
                logger.error(f"Keyword search '{query}' failed: {e}")
        return posts

    def run(self) -> int:
        """Main entry point — called by scheduler every 30 mins."""
        logger.info("Reddit collector starting...")
        all_posts = []
        all_posts.extend(self.scrape_subreddits())
        all_posts.extend(self.scrape_keywords())

        # Deduplicate in-memory by post_id before hitting DB
        seen = set()
        unique = []
        for p in all_posts:
            if p["post_id"] not in seen:
                seen.add(p["post_id"])
                unique.append(p)

        saved = self._save_posts(unique)
        logger.info(f"Reddit collector done. {saved} new posts saved.")
        return saved

