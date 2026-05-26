"""
services/knowledge_base.py
──────────────────────────
Reads all JSON-based .txt files from the datasets/processed/ directory and
builds a structured knowledge base of leaders, their countries, and tweets.

Also reads the Global Geopolitical Intelligence summary for context.

This is the single source of truth for the Political Statements panel.
"""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Leader metadata ───────────────────────────────────────────────────────────
# Maps Twitter username (lowercase) → leader info
LEADER_META = {
    # United States
    "narendramodi": {
        "name": "Narendra Modi",
        "title": "Prime Minister of India",
        "country": "India",
        "country_code": "IN",
    },
    # Ukraine
    "zelenskyyua": {
        "name": "Volodymyr Zelenskyy",
        "title": "President of Ukraine",
        "country": "Ukraine",
        "country_code": "UA",
    },
    # United States
    "realdonald trump": {
        "name": "Donald Trump",
        "title": "President of the United States",
        "country": "United States",
        "country_code": "US",
    },
    "realdonaldtrump": {
        "name": "Donald Trump",
        "title": "President of the United States",
        "country": "United States",
        "country_code": "US",
    },
    # United Kingdom
    "keir_starmer": {
        "name": "Keir Starmer",
        "title": "Prime Minister of the United Kingdom",
        "country": "United Kingdom",
        "country_code": "GB",
    },
    # Israel
    "netanyahu": {
        "name": "Benjamin Netanyahu",
        "title": "Prime Minister of Israel",
        "country": "Israel",
        "country_code": "IL",
    },
    # Russia - Add Putin if available
    "kremlinrussia_e": {
        "name": "Vladimir Putin",
        "title": "President of Russia",
        "country": "Russia",
        "country_code": "RU",
    },
    # China - Add Xi Jinping if available
    "chinascio": {
        "name": "Xi Jinping",
        "title": "President of China",
        "country": "China",
        "country_code": "CN",
    },
    # Other leaders (lower priority)
    "jmeili": {
        "name": "Javier Milei",
        "title": "President of Argentina",
        "country": "Argentina",
        "country_code": "AR",
    },
    "rterdogan": {
        "name": "Recep Tayyip Erdoğan",
        "title": "President of Turkey",
        "country": "Turkey",
        "country_code": "TR",
    },
    "justintrudeau": {
        "name": "Justin Trudeau",
        "title": "Former Prime Minister of Canada",
        "country": "Canada",
        "country_code": "CA",
    },
    "lula_official": {
        "name": "Luiz Inácio Lula da Silva",
        "title": "President of Brazil",
        "country": "Brazil",
        "country_code": "BR",
    },
    "nayibbukele": {
        "name": "Nayib Bukele",
        "title": "President of El Salvador",
        "country": "El Salvador",
        "country_code": "SV",
    },
    "claudiashein": {
        "name": "Claudia Sheinbaum",
        "title": "President of Mexico",
        "country": "Mexico",
        "country_code": "MX",
    },
    "mr_obama": {
        "name": "Barack Obama",
        "title": "Former President of the United States",
        "country": "United States",
        "country_code": "US",
    },
}

# Country keyword → ISO code mapping for affected country detection
COUNTRY_KEYWORDS = {
    "US": ["united states", "usa", "america", "american", "washington", "white house", "pentagon", "u.s."],
    "CN": ["china", "chinese", "beijing", "xi jinping", "prc"],
    "RU": ["russia", "russian", "moscow", "kremlin", "putin"],
    "IN": ["india", "indian", "new delhi", "modi"],
    "PK": ["pakistan", "pakistani", "islamabad"],
    "GB": ["britain", "british", "uk", "united kingdom", "london", "england"],
    "DE": ["germany", "german", "berlin"],
    "FR": ["france", "french", "paris", "macron"],
    "JP": ["japan", "japanese", "tokyo"],
    "KR": ["south korea", "korean", "seoul"],
    "KP": ["north korea", "dprk", "pyongyang", "kim jong"],
    "IR": ["iran", "iranian", "tehran", "khamenei", "irgc"],
    "IL": ["israel", "israeli", "tel aviv", "jerusalem", "idf", "netanyahu", "hamas", "gaza"],
    "SA": ["saudi arabia", "saudi", "riyadh"],
    "TR": ["turkey", "turkish", "ankara", "erdogan"],
    "UA": ["ukraine", "ukrainian", "kyiv", "zelensky", "zelenskyy"],
    "BR": ["brazil", "brazilian", "brasilia", "lula"],
    "CA": ["canada", "canadian", "ottawa", "trudeau"],
    "MX": ["mexico", "mexican"],
    "AR": ["argentina", "argentine", "milei"],
    "SV": ["el salvador", "bukele"],
}

COUNTRY_NAMES = {
    "US": "United States", "CN": "China", "RU": "Russia", "IN": "India",
    "PK": "Pakistan", "GB": "United Kingdom", "DE": "Germany", "FR": "France",
    "JP": "Japan", "KR": "South Korea", "KP": "North Korea", "IR": "Iran",
    "IL": "Israel", "SA": "Saudi Arabia", "TR": "Turkey", "UA": "Ukraine",
    "BR": "Brazil", "CA": "Canada", "MX": "Mexico", "AR": "Argentina", "SV": "El Salvador",
}


def _datasets_dir() -> Path:
    """Return the project-root datasets/processed/ directory."""
    backend_dir = Path(__file__).parent.parent
    return backend_dir.parent / "datasets" / "processed"


def _get_leader_meta(username: str, author: dict) -> dict:
    """Resolve leader metadata from username or author dict."""
    key = username.lower().lstrip("@")
    if key in LEADER_META:
        return LEADER_META[key]
    # Fallback: build from author data
    return {
        "name": author.get("name", username),
        "title": author.get("description", "")[:80] if author.get("description") else "",
        "country": "",
        "country_code": "",
    }


def _detect_affected_countries(text: str, leader_country_code: str) -> list[str]:
    """Detect country codes mentioned in the tweet text."""
    text_lower = text.lower()
    found = []
    for code, keywords in COUNTRY_KEYWORDS.items():
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                if code not in found:
                    found.append(code)
                break
    # Always include the leader's own country if not already there
    if leader_country_code and leader_country_code not in found:
        found.insert(0, leader_country_code)
    return found[:5]  # cap at 5


def _parse_tweet_date(created_at: str) -> Optional[datetime]:
    """Parse Twitter createdAt format."""
    for fmt in ("%a %b %d %H:%M:%S +0000 %Y", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(created_at, fmt)
        except (ValueError, TypeError):
            continue
    return None


def load_knowledge_base(limit_per_leader: int = 20) -> dict:
    """
    Load all leader tweet files and return a structured knowledge base.

    Returns:
        {
          "leaders": [
            {
              "username": str,
              "name": str,
              "title": str,
              "country": str,
              "country_code": str,
              "profile_picture": str,
              "tweets": [
                {
                  "id": str,
                  "text": str,
                  "created_at": str,   # ISO format
                  "url": str,
                  "like_count": int,
                  "retweet_count": int,
                  "view_count": int,
                  "affected_countries": [str],  # ISO codes
                }
              ]
            }
          ],
          "geopolitical_summary": str,
          "loaded_at": str,
        }
    """
    datasets_dir = _datasets_dir()
    leaders = []
    geopolitical_summary = ""

    if not datasets_dir.exists():
        logger.warning(f"Datasets directory not found: {datasets_dir}")
        return {"leaders": [], "geopolitical_summary": "", "loaded_at": datetime.utcnow().isoformat()}

    for f in sorted(datasets_dir.iterdir()):
        if not f.suffix == ".txt":
            continue

        # Global intelligence summary — not a tweet file
        if f.name.startswith("#"):
            try:
                geopolitical_summary = f.read_text(encoding="utf-8")
            except Exception as e:
                logger.warning(f"Could not read geopolitical summary: {e}")
            continue

        # Try to parse as JSON tweet array
        try:
            content = f.read_text(encoding="utf-8").strip()
            if not content.startswith("["):
                continue
            tweets_raw = json.loads(content)
        except Exception as e:
            logger.debug(f"Skipping {f.name}: {e}")
            continue

        if not tweets_raw or not isinstance(tweets_raw, list):
            continue

        # Extract author from first tweet
        first = tweets_raw[0]
        author = first.get("author", {})
        username = author.get("username", f.stem)
        profile_picture = author.get("profilePicture", "")

        meta = _get_leader_meta(username, author)

        # Parse tweets
        tweets = []
        for raw in tweets_raw:
            text = raw.get("text", "").strip()
            if len(text) < 20:
                continue
            # Skip pure reply stubs
            if raw.get("isReply") and len(text) < 40:
                continue

            created_at_raw = raw.get("createdAt", "")
            dt = _parse_tweet_date(created_at_raw)
            created_at_iso = dt.isoformat() if dt else created_at_raw

            affected = _detect_affected_countries(text, meta.get("country_code", ""))

            tweets.append({
                "id": str(raw.get("id", "")),
                "text": text,
                "created_at": created_at_iso,
                "url": raw.get("url", ""),
                "like_count": int(raw.get("likeCount", 0)),
                "retweet_count": int(raw.get("retweetCount", 0)),
                "view_count": int(raw.get("viewCount", 0)),
                "affected_countries": affected,
            })

            if len(tweets) >= limit_per_leader:
                break

        if not tweets:
            continue

        leaders.append({
            "username": username,
            "name": meta["name"],
            "title": meta["title"],
            "country": meta["country"],
            "country_code": meta["country_code"],
            "profile_picture": profile_picture,
            "tweets": tweets,
        })

    logger.info(f"Knowledge base loaded: {len(leaders)} leaders, {sum(len(l['tweets']) for l in leaders)} tweets")

    return {
        "leaders": leaders,
        "geopolitical_summary": geopolitical_summary,
        "loaded_at": datetime.utcnow().isoformat(),
    }


# Module-level cache — reloaded on each server restart
_kb_cache: dict | None = None


def get_knowledge_base(force_reload: bool = False) -> dict:
    """Return cached knowledge base, loading if needed."""
    global _kb_cache
    if _kb_cache is None or force_reload:
        _kb_cache = load_knowledge_base()
    return _kb_cache
