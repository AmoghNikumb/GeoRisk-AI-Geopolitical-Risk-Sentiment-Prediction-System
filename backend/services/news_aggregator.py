"""
services/news_aggregator.py — Geopolitical News RSS Aggregator
──────────────────────────────────────────────────────────────
Fetches public RSS/Atom feeds from geopolitical sources, normalises
every item into a single schema, de-duplicates, classifies region/topic
via rule-based tagging, and caches the result in-process.

Adding a new source:
    Append an entry to NEWS_SOURCES with a unique id, label, url, and
    optional default_region. The rest is automatic.
"""
import hashlib
import logging
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Optional
from email.utils import parsedate_to_datetime

import requests

try:
    from lxml import etree as lxml_etree
    _LXML_AVAILABLE = True
except ImportError:
    _LXML_AVAILABLE = False

logger = logging.getLogger(__name__)

# ── Cache ─────────────────────────────────────────────────────────────────────
_cache: dict = {"items": [], "fetched_at": None}
CACHE_TTL_SECONDS = 20 * 60   # 20 minutes


# ── Feed Registry ─────────────────────────────────────────────────────────────
# All URLs verified live. Add new sources here — no other code changes needed.
NEWS_SOURCES = [
    # ── Geopolitical / Strategic ──────────────────────────────────────────────
    {
        "id": "war_on_rocks",
        "label": "War on the Rocks",
        "url": "https://warontherocks.com/feed/",
        "default_region": "Global",
    },
    {
        "id": "foreign_affairs",
        "label": "Foreign Affairs",
        "url": "https://www.foreignaffairs.com/rss.xml",
        "default_region": "Global",
    },
    {
        "id": "crisisgroup",
        "label": "International Crisis Group",
        "url": "https://www.crisisgroup.org/rss.xml",
        "default_region": "Global",
    },
    {
        "id": "stimson",
        "label": "Stimson Center",
        "url": "https://www.stimson.org/feed/",
        "default_region": "Global",
    },
    {
        "id": "bellingcat",
        "label": "Bellingcat",
        "url": "https://www.bellingcat.com/feed/",
        "default_region": "Global",
    },
    # ── News Wires / Broadcasters ─────────────────────────────────────────────
    {
        "id": "aljazeera_world",
        "label": "Al Jazeera — World",
        "url": "https://www.aljazeera.com/xml/rss/all.xml",
        "default_region": "Global",
    },
    {
        "id": "rferl",
        "label": "Radio Free Europe / Radio Liberty",
        "url": "https://www.rferl.org/api/epiqq",
        "default_region": "Europe",
    },
    {
        "id": "dw_world",
        "label": "Deutsche Welle — World",
        "url": "https://rss.dw.com/xml/rss-en-world",
        "default_region": "Global",
    },
    {
        "id": "guardian_world",
        "label": "The Guardian — World",
        "url": "https://www.theguardian.com/world/rss",
        "default_region": "Global",
    },
    {
        "id": "nyt_world",
        "label": "New York Times — World",
        "url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "default_region": "Global",
    },
    # ── Policy / Europe ───────────────────────────────────────────────────────
    {
        "id": "euractiv",
        "label": "Euractiv",
        "url": "https://www.euractiv.com/feed/",
        "default_region": "Europe",
    },
    {
        "id": "politico_eu",
        "label": "Politico Europe",
        "url": "https://www.politico.eu/feed/",
        "default_region": "Europe",
    },
    # ── International Organisations ───────────────────────────────────────────
    {
        "id": "un_news",
        "label": "UN News",
        "url": "https://news.un.org/feed/subscribe/en/news/all/rss.xml",
        "default_region": "Global",
    },
    {
        "id": "reliefweb",
        "label": "ReliefWeb",
        "url": "https://reliefweb.int/updates/rss.xml",
        "default_region": "Global",
    },
]

# ── Region Classification Rules ───────────────────────────────────────────────
REGION_RULES: list[tuple[str, list[str]]] = [
    ("Europe", [
        "russia", "ukraine", "nato", "eu ", "european union", "germany", "france",
        "poland", "balkans", "moldova", "belarus", "finland", "sweden", "baltic",
        "hungary", "serbia", "kosovo", "turkey", "erdogan", "zelensky", "kremlin",
        "brussels", "macron", "scholz", "uk ", "britain", "london",
    ]),
    ("Middle East", [
        "iran", "israel", "gaza", "hamas", "hezbollah", "saudi", "yemen", "houthi",
        "iraq", "syria", "lebanon", "jordan", "qatar", "uae", "gulf", "persian",
        "netanyahu", "tehran", "riyadh", "idf", "irgc", "west bank",
    ]),
    ("Indo-Pacific", [
        "china", "taiwan", "south china sea", "japan", "korea", "north korea",
        "india", "pakistan", "myanmar", "philippines", "asean", "quad",
        "beijing", "xi jinping", "modi", "indo-pacific", "pla", "dprk",
        "australia", "new zealand", "aukus",
    ]),
    ("Americas", [
        "united states", "us ", "u.s.", "washington", "biden", "trump", "congress",
        "canada", "mexico", "venezuela", "colombia", "brazil", "latin america",
        "caribbean", "cuba", "nicaragua", "pentagon", "cia", "state department",
    ]),
    ("Africa", [
        "africa", "sahel", "sudan", "ethiopia", "somalia", "mali", "niger",
        "nigeria", "kenya", "congo", "drc", "mozambique", "zimbabwe",
        "south africa", "wagner", "ecowas",
    ]),
]

# ── Topic Classification Rules ────────────────────────────────────────────────
TOPIC_RULES: list[tuple[str, list[str]]] = [
    ("conflict", [
        "war", "attack", "strike", "missile", "drone", "troops", "military",
        "offensive", "ceasefire", "battle", "combat", "airstrike", "shelling",
        "casualties", "killed", "wounded", "siege", "invasion",
    ]),
    ("diplomacy", [
        "talks", "summit", "treaty", "agreement", "diplomatic", "ambassador",
        "negotiations", "bilateral", "multilateral", "un ", "united nations",
        "foreign minister", "secretary of state", "envoy", "sanctions lifted",
    ]),
    ("sanctions", [
        "sanctions", "embargo", "export controls", "blacklist", "ofac",
        "asset freeze", "travel ban", "restricted", "penalised",
    ]),
    ("defence", [
        "defence", "defense", "military aid", "weapons", "arms", "nato",
        "deterrence", "nuclear", "hypersonic", "f-35", "carrier", "submarine",
        "intelligence", "espionage", "cyber attack",
    ]),
    ("trade", [
        "trade", "tariff", "import", "export", "wto", "supply chain",
        "economic", "gdp", "investment", "currency", "dollar", "yuan",
    ]),
    ("energy", [
        "oil", "gas", "lng", "pipeline", "opec", "energy", "nuclear power",
        "renewables", "fuel", "petroleum", "nord stream",
    ]),
    ("elections", [
        "election", "vote", "ballot", "referendum", "poll", "campaign",
        "president", "prime minister", "parliament", "democracy",
    ]),
    ("cyber", [
        "cyber", "hack", "ransomware", "malware", "disinformation",
        "information warfare", "espionage", "data breach", "infrastructure attack",
    ]),
]

# ── Country → Flag emoji map (ISO 3166-1 alpha-2) ────────────────────────────
COUNTRY_FLAGS: dict[str, str] = {
    "russia": "🇷🇺", "ukraine": "🇺🇦", "china": "🇨🇳", "taiwan": "🇹🇼",
    "united states": "🇺🇸", "us ": "🇺🇸", "u.s.": "🇺🇸",
    "iran": "🇮🇷", "israel": "🇮🇱", "india": "🇮🇳", "pakistan": "🇵🇰",
    "north korea": "🇰🇵", "south korea": "🇰🇷", "japan": "🇯🇵",
    "saudi": "🇸🇦", "turkey": "🇹🇷", "germany": "🇩🇪", "france": "🇫🇷",
    "uk ": "🇬🇧", "britain": "🇬🇧", "brazil": "🇧🇷", "venezuela": "🇻🇪",
    "ethiopia": "🇪🇹", "sudan": "🇸🇩", "nigeria": "🇳🇬",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_id(url: str, title: str) -> str:
    return hashlib.md5(f"{url}|{title}".encode()).hexdigest()


def _clean_html(raw: str) -> str:
    """Strip HTML tags and collapse whitespace."""
    text = re.sub(r"<[^>]+>", " ", raw or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:500]


def _parse_date(raw: str) -> Optional[str]:
    """Parse RFC 2822 or ISO 8601 date strings → ISO 8601 UTC string."""
    if not raw:
        return None
    raw = raw.strip()
    # Try RFC 2822 (RSS)
    try:
        dt = parsedate_to_datetime(raw)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        pass
    # Try ISO 8601 variants
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(raw[:19], fmt[:len(raw[:19])])
            return dt.replace(tzinfo=timezone.utc).isoformat()
        except Exception:
            pass
    return None


def _classify_region(text: str, default: str) -> str:
    lower = text.lower()
    for region, keywords in REGION_RULES:
        if any(kw in lower for kw in keywords):
            return region
    return default


def _classify_topics(text: str) -> list[str]:
    lower = text.lower()
    return [topic for topic, keywords in TOPIC_RULES if any(kw in lower for kw in keywords)]


def _extract_countries(text: str) -> list[str]:
    lower = text.lower()
    found = []
    for country in COUNTRY_FLAGS:
        if country in lower and country not in found:
            found.append(country.strip())
    return found[:4]


def _extract_flags(countries: list[str]) -> list[str]:
    return [COUNTRY_FLAGS[c] for c in countries if c in COUNTRY_FLAGS]


def _extract_image(item_el: ET.Element, ns: dict) -> Optional[str]:
    """Try to find an image URL from media:content, enclosure, or og tags."""
    # media:content
    media_ns = "http://search.yahoo.com/mrss/"
    media_content = item_el.find(f"{{{media_ns}}}content")
    if media_content is not None:
        url = media_content.get("url")
        if url and url.startswith("http"):
            return url

    # enclosure
    enclosure = item_el.find("enclosure")
    if enclosure is not None:
        url = enclosure.get("url", "")
        if url.startswith("http") and any(ext in url for ext in [".jpg", ".jpeg", ".png", ".webp"]):
            return url

    # media:thumbnail
    media_thumb = item_el.find(f"{{{media_ns}}}thumbnail")
    if media_thumb is not None:
        url = media_thumb.get("url")
        if url and url.startswith("http"):
            return url

    return None


# ── Feed Fetcher ──────────────────────────────────────────────────────────────

def _parse_xml(content: bytes) -> ET.Element:
    """Parse XML with stdlib first, fall back to lxml for malformed feeds."""
    try:
        return ET.fromstring(content)
    except ET.ParseError:
        if _LXML_AVAILABLE:
            # lxml recovers from most malformed XML / HTML entities
            lxml_root = lxml_etree.fromstring(content, parser=lxml_etree.XMLParser(recover=True))
            # Convert back to stdlib Element via serialisation
            return ET.fromstring(lxml_etree.tostring(lxml_root))
        raise


def _get_text(el: ET.Element, tag: str, ns: dict) -> str:
    """Get text from a direct child tag, with Atom namespace fallback."""
    node = el.find(tag)
    if node is None:
        node = el.find(f"atom:{tag}", ns)
    if node is None:
        return ""
    return (node.text or "").strip()


def _fetch_feed(source: dict) -> list[dict]:
    """Fetch one RSS/Atom feed and return normalised items."""
    items = []
    try:
        resp = requests.get(
            source["url"],
            timeout=12,
            headers={"User-Agent": "GeoRiskIntelligence/2.0 (news aggregator)"},
        )
        resp.raise_for_status()
        # Reject HTML responses (Cloudflare / login walls)
        ct = resp.headers.get("content-type", "")
        first = resp.content[:300]
        if "html" in ct and b"<rss" not in first and b"<feed" not in first and b"<?xml" not in first:
            logger.warning(f"[news] Feed [{source['id']}] returned HTML — skipping")
            return []
        root = _parse_xml(resp.content)
    except Exception as e:
        logger.warning(f"[news] Feed fetch failed [{source['id']}]: {e}")
        return []

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    item_els = root.findall(".//item") or root.findall(".//atom:entry", ns)

    for el in item_els[:30]:   # cap per source
        title = _get_text(el, "title", ns)
        if not title:
            continue

        link = _get_text(el, "link", ns)
        # Atom <link href="..."> element (no text content)
        if not link:
            link_el = el.find("atom:link", ns)
            if link_el is not None:
                link = link_el.get("href", "")
        if not link:
            link_el = el.find("link")
            if link_el is not None:
                link = link_el.get("href", link_el.text or "")

        pub_raw = (
            _get_text(el, "pubDate", ns)
            or _get_text(el, "published", ns)
            or _get_text(el, "updated", ns)
            or _get_text(el, "dc:date", ns)
        )
        summary_raw = (
            _get_text(el, "description", ns)
            or _get_text(el, "summary", ns)
            or _get_text(el, "content", ns)
        )

        summary = _clean_html(summary_raw)
        combined = f"{title} {summary}"

        region = _classify_region(combined, source.get("default_region", "Global"))
        topics = _classify_topics(combined)
        countries = _extract_countries(combined)
        flags = _extract_flags(countries)
        image = _extract_image(el, ns)

        items.append({
            "id": _make_id(link, title),
            "title": title,
            "summary": summary,
            "url": link,
            "source": source["label"],
            "source_id": source["id"],
            "publishedAt": _parse_date(pub_raw),
            "image": image,
            "region": region,
            "topics": topics,
            "countries": countries,
            "flags": flags,
            "featured": False,
        })

    logger.info(f"[news] {source['id']}: {len(items)} items fetched")
    return items


# ── Aggregator ────────────────────────────────────────────────────────────────

def _deduplicate(items: list[dict]) -> list[dict]:
    seen_ids: set[str] = set()
    seen_titles: set[str] = set()
    out = []
    for item in items:
        title_key = re.sub(r"\W+", "", item["title"].lower())[:60]
        if item["id"] in seen_ids or title_key in seen_titles:
            continue
        seen_ids.add(item["id"])
        seen_titles.add(title_key)
        out.append(item)
    return out


def _sort_by_date(items: list[dict]) -> list[dict]:
    def _key(item):
        ts = item.get("publishedAt")
        if ts:
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                pass
        return datetime.min.replace(tzinfo=timezone.utc)
    return sorted(items, key=_key, reverse=True)


def _mark_featured(items: list[dict]) -> list[dict]:
    """Mark the single most recent item as featured (top story)."""
    if items:
        items[0]["featured"] = True
    return items


def fetch_news(force: bool = False) -> dict:
    """
    Public entry point.  Returns cached result unless stale or force=True.
    Thread-safe for read-heavy workloads (single writer, multiple readers).
    """
    global _cache

    now = time.time()
    if (
        not force
        and _cache["fetched_at"] is not None
        and (now - _cache["fetched_at"]) < CACHE_TTL_SECONDS
        and _cache["items"]
    ):
        return {
            "items": _cache["items"],
            "fetched_at": datetime.utcfromtimestamp(_cache["fetched_at"]).isoformat() + "Z",
            "total": len(_cache["items"]),
            "sources": [s["label"] for s in NEWS_SOURCES],
            "cached": True,
        }

    all_items: list[dict] = []
    for source in NEWS_SOURCES:
        all_items.extend(_fetch_feed(source))

    all_items = _deduplicate(all_items)
    all_items = _sort_by_date(all_items)
    all_items = _mark_featured(all_items)

    _cache["items"] = all_items
    _cache["fetched_at"] = now

    logger.info(f"[news] Aggregation complete: {len(all_items)} unique items from {len(NEWS_SOURCES)} sources")

    return {
        "items": all_items,
        "fetched_at": datetime.utcfromtimestamp(now).isoformat() + "Z",
        "total": len(all_items),
        "sources": [s["label"] for s in NEWS_SOURCES],
        "cached": False,
    }
