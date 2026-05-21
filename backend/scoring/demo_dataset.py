"""
scoring/demo_dataset.py
───────────────────────
Temporary collected tweet dataset for model validation.

On each refresh call, a random sample is drawn from the full post pool
so the UI shows different posts with fresh timestamps — simulating a
live feed until real Twitter/X fetching is integrated.

DATA SOURCE:
  Manually curated from recent public news headlines and social media
  posts (May 2025). Clearly labeled as "demo_collected" — NOT live data.

ARCHITECTURE NOTE:
  Replace score_demo_posts() with a live TwitterCollector call once
  API credentials are available. The interface stays the same.
"""
from __future__ import annotations

import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# ── Validation sentences (fixed — used to verify model behavior) ──────────────
DEMO_VALIDATION_SENTENCES: List[Dict[str, str]] = [
    {
        "text": "Airstrikes near the border have increased fears of a broader regional war.",
        "expected": "NEGATIVE",
        "context": "Generic conflict escalation",
    },
    {
        "text": "Officials from both countries agreed to resume peace talks next week.",
        "expected": "POSITIVE",
        "context": "Diplomatic de-escalation",
    },
    {
        "text": "Heavy shelling displaced hundreds of civilians overnight.",
        "expected": "NEGATIVE",
        "context": "Active conflict, civilian impact",
    },
    {
        "text": "The ceasefire appears to be holding in major cities.",
        "expected": "POSITIVE",
        "context": "Ceasefire stability",
    },
    {
        "text": "Military mobilization and threats from both sides are escalating tensions.",
        "expected": "NEGATIVE",
        "context": "Bilateral escalation",
    },
]

# ── Full post pool — sampled randomly on each refresh ────────────────────────
# Each pair has 12–15 posts so each refresh shows a different 5–6 post subset.
# Timestamps are assigned fresh on each call (relative to now).

_POST_POOL: List[Dict[str, Any]] = [

    # ── India–Pakistan (IN-PK) ────────────────────────────────────────────────
    {"pair": "IN-PK", "country_a": "IN", "country_b": "PK",
     "query": "India Pakistan Operation Sindoor",
     "text": "India launched Operation Sindoor striking nine sites in Pakistan and Pakistan-administered Kashmir following the Pahalgam terror attack."},
    {"pair": "IN-PK", "country_a": "IN", "country_b": "PK",
     "query": "India Pakistan jets retaliation",
     "text": "Pakistan's military says it has shot down five Indian Air Force jets in retaliation for the strikes. India has not confirmed losses."},
    {"pair": "IN-PK", "country_a": "IN", "country_b": "PK",
     "query": "India Pakistan ceasefire diplomacy",
     "text": "India and Pakistan have agreed to a ceasefire after four days of intense cross-border military exchanges. Both sides claim victory."},
    {"pair": "IN-PK", "country_a": "IN", "country_b": "PK",
     "query": "India Pakistan border shelling civilians",
     "text": "Heavy artillery shelling along the Line of Control has displaced thousands of civilians in Kashmir. Hospitals overwhelmed."},
    {"pair": "IN-PK", "country_a": "IN", "country_b": "PK",
     "query": "India Pakistan nuclear threat",
     "text": "Pakistan's foreign minister warns of nuclear escalation if India continues military operations inside Pakistani territory."},
    {"pair": "IN-PK", "country_a": "IN", "country_b": "PK",
     "query": "India Pakistan US ceasefire",
     "text": "US Secretary of State confirms both India and Pakistan have agreed to a full and immediate ceasefire. Diplomatic channels reopened."},
    {"pair": "IN-PK", "country_a": "IN", "country_b": "PK",
     "query": "India Pakistan military mobilization",
     "text": "India has mobilized additional armored divisions to the Punjab border. Pakistan has placed its air force on high alert."},
    {"pair": "IN-PK", "country_a": "IN", "country_b": "PK",
     "query": "India Pakistan Pahalgam terrorism",
     "text": "The Pahalgam terror attack that killed 26 tourists was the trigger for India's military response. Pakistan denies involvement."},
    {"pair": "IN-PK", "country_a": "IN", "country_b": "PK",
     "query": "India Pakistan LoC violations",
     "text": "Indian Army reports 47 ceasefire violations along the Line of Control in the past 48 hours. Troops on high alert."},
    {"pair": "IN-PK", "country_a": "IN", "country_b": "PK",
     "query": "India Pakistan diplomatic expulsion",
     "text": "Pakistan expels Indian High Commissioner and suspends bilateral trade following the military strikes."},
    {"pair": "IN-PK", "country_a": "IN", "country_b": "PK",
     "query": "India Pakistan water treaty",
     "text": "India suspends the Indus Waters Treaty in response to the Pahalgam attack, escalating tensions further."},
    {"pair": "IN-PK", "country_a": "IN", "country_b": "PK",
     "query": "India Pakistan peace talks resumed",
     "text": "Back-channel diplomacy between India and Pakistan reportedly active. Both sides exploring conditions for sustained ceasefire."},

    # ── Russia–Ukraine (RU-UA) ────────────────────────────────────────────────
    {"pair": "RU-UA", "country_a": "RU", "country_b": "UA",
     "query": "Russia Ukraine drone strikes Kyiv",
     "text": "Russia launched a massive drone and missile barrage targeting Kyiv and Kharkiv overnight. Air defenses intercepted most but not all."},
    {"pair": "RU-UA", "country_a": "RU", "country_b": "UA",
     "query": "Ukraine Russia ceasefire Trump",
     "text": "Trump administration pushing for ceasefire talks between Russia and Ukraine. Zelensky insists on security guarantees before any deal."},
    {"pair": "RU-UA", "country_a": "RU", "country_b": "UA",
     "query": "Russia Ukraine Donetsk frontline",
     "text": "Russian forces have advanced several kilometers in Donetsk region. Ukrainian military reports intense fighting near Pokrovsk."},
    {"pair": "RU-UA", "country_a": "RU", "country_b": "UA",
     "query": "Ukraine Russia peace talks Istanbul",
     "text": "First direct peace talks between Russia and Ukraine in three years held in Istanbul. No breakthrough but dialogue continues."},
    {"pair": "RU-UA", "country_a": "RU", "country_b": "UA",
     "query": "Russia Ukraine EU sanctions energy",
     "text": "EU announces new sanctions package targeting Russian energy exports and financial institutions supporting the war effort."},
    {"pair": "RU-UA", "country_a": "RU", "country_b": "UA",
     "query": "Ukraine military aid US weapons",
     "text": "US approves additional $2 billion military aid package for Ukraine including long-range missiles and air defense systems."},
    {"pair": "RU-UA", "country_a": "RU", "country_b": "UA",
     "query": "Russia Ukraine Zaporizhzhia nuclear",
     "text": "IAEA warns of dangerous situation at Zaporizhzhia nuclear plant as shelling intensifies in surrounding area."},
    {"pair": "RU-UA", "country_a": "RU", "country_b": "UA",
     "query": "Russia Ukraine mobilization troops",
     "text": "Russia announces new wave of military mobilization targeting 150,000 additional troops for the Ukrainian front."},
    {"pair": "RU-UA", "country_a": "RU", "country_b": "UA",
     "query": "Ukraine counteroffensive Kherson",
     "text": "Ukrainian forces launch limited counteroffensive in Kherson region, recapturing several villages from Russian control."},
    {"pair": "RU-UA", "country_a": "RU", "country_b": "UA",
     "query": "Russia Ukraine grain deal Black Sea",
     "text": "Russia withdraws from Black Sea grain deal, threatening global food security and pushing wheat prices higher."},
    {"pair": "RU-UA", "country_a": "RU", "country_b": "UA",
     "query": "Ukraine NATO membership talks",
     "text": "NATO allies discuss accelerated path to membership for Ukraine as war enters third year with no end in sight."},
    {"pair": "RU-UA", "country_a": "RU", "country_b": "UA",
     "query": "Russia Ukraine civilian casualties",
     "text": "UN reports over 10,000 civilian casualties in Ukraine since the start of the conflict, calling for immediate ceasefire."},

    # ── Israel–Iran (IL-IR) ───────────────────────────────────────────────────
    {"pair": "IL-IR", "country_a": "IL", "country_b": "IR",
     "query": "Israel Iran nuclear strike threat",
     "text": "Israel warns it will strike Iranian nuclear facilities if Tehran crosses uranium enrichment red lines. Iran calls it an act of war."},
    {"pair": "IL-IR", "country_a": "IL", "country_b": "IR",
     "query": "Iran nuclear deal Oman talks",
     "text": "Iran and US resume indirect nuclear talks in Oman. Tehran demands sanctions relief before any enrichment limits."},
    {"pair": "IL-IR", "country_a": "IL", "country_b": "IR",
     "query": "Israel Hezbollah rockets Lebanon",
     "text": "Hezbollah fires 40 rockets into northern Israel. IDF responds with airstrikes on Hezbollah positions in southern Lebanon."},
    {"pair": "IL-IR", "country_a": "IL", "country_b": "IR",
     "query": "Iran Houthi missiles Israel",
     "text": "Iranian-backed Houthi forces launch ballistic missiles toward Israel. Iron Dome and Arrow systems intercept all projectiles."},
    {"pair": "IL-IR", "country_a": "IL", "country_b": "IR",
     "query": "Israel Iran Gaza ceasefire Qatar",
     "text": "Qatar mediating between Israel and Hamas for extended ceasefire in Gaza. Iran signals it would support a deal if terms are right."},
    {"pair": "IL-IR", "country_a": "IL", "country_b": "IR",
     "query": "Iran uranium enrichment IAEA",
     "text": "IAEA confirms Iran has enriched uranium to 84% purity, just below weapons-grade threshold. Israel calls it unacceptable."},
    {"pair": "IL-IR", "country_a": "IL", "country_b": "IR",
     "query": "Israel Iran shadow war assassinations",
     "text": "Senior Iranian nuclear scientist killed in targeted assassination. Tehran blames Israel and vows retaliation."},
    {"pair": "IL-IR", "country_a": "IL", "country_b": "IR",
     "query": "Iran proxy network Iraq Syria",
     "text": "Iranian proxy militias in Iraq and Syria increase attacks on US bases, raising fears of broader regional escalation."},
    {"pair": "IL-IR", "country_a": "IL", "country_b": "IR",
     "query": "Israel Iran diplomatic back channel",
     "text": "European diplomats report secret back-channel talks between Israeli and Iranian officials to prevent direct military confrontation."},
    {"pair": "IL-IR", "country_a": "IL", "country_b": "IR",
     "query": "Iran oil sanctions US pressure",
     "text": "US tightens sanctions on Iranian oil exports, cutting revenue that funds proxy militias across the Middle East."},

    # ── China–Taiwan (CN-TW) ──────────────────────────────────────────────────
    {"pair": "CN-TW", "country_a": "CN", "country_b": "TW",
     "query": "China Taiwan military exercises strait",
     "text": "China conducts large-scale military exercises around Taiwan Strait involving carrier groups and amphibious assault ships."},
    {"pair": "CN-TW", "country_a": "CN", "country_b": "TW",
     "query": "Taiwan PLA aircraft median line",
     "text": "Taiwan's defense ministry reports record number of PLA aircraft crossing the median line in the Taiwan Strait this week."},
    {"pair": "CN-TW", "country_a": "CN", "country_b": "TW",
     "query": "US Taiwan arms sale China",
     "text": "US approves $500 million arms sale to Taiwan. China summons US ambassador and warns of countermeasures."},
    {"pair": "CN-TW", "country_a": "CN", "country_b": "TW",
     "query": "Taiwan China trade economic ties",
     "text": "Taiwan and China maintain significant trade ties despite tensions. Cross-strait trade reached $180 billion last year."},
    {"pair": "CN-TW", "country_a": "CN", "country_b": "TW",
     "query": "China Taiwan invasion timeline",
     "text": "US intelligence assesses China could be ready for a Taiwan invasion by 2027. Taiwan accelerates defense spending."},
    {"pair": "CN-TW", "country_a": "CN", "country_b": "TW",
     "query": "Taiwan election China reaction",
     "text": "Taiwan elects pro-independence president. Beijing calls the result a provocation and increases military pressure."},
    {"pair": "CN-TW", "country_a": "CN", "country_b": "TW",
     "query": "China Taiwan semiconductor chips",
     "text": "Taiwan's TSMC dominates global chip production. China views this as strategic leverage in any conflict scenario."},
    {"pair": "CN-TW", "country_a": "CN", "country_b": "TW",
     "query": "US Taiwan defense commitment",
     "text": "US reaffirms commitment to Taiwan's defense under the Taiwan Relations Act. China calls it interference in internal affairs."},

    # ── China–US (CN-US) ──────────────────────────────────────────────────────
    {"pair": "CN-US", "country_a": "CN", "country_b": "US",
     "query": "China US trade war tariffs 145",
     "text": "US raises tariffs on Chinese goods to 145%. China retaliates with 125% tariffs on American imports. Trade war escalates."},
    {"pair": "CN-US", "country_a": "CN", "country_b": "US",
     "query": "China US trade truce Geneva",
     "text": "US and China reach temporary trade truce in Geneva. Both sides agree to reduce tariffs for 90 days while negotiations continue."},
    {"pair": "CN-US", "country_a": "CN", "country_b": "US",
     "query": "China US South China Sea navy",
     "text": "US Navy conducts freedom of navigation operation in South China Sea. China's PLA Navy shadows US vessels and issues warnings."},
    {"pair": "CN-US", "country_a": "CN", "country_b": "US",
     "query": "China US semiconductor export controls",
     "text": "US expands semiconductor export controls targeting Chinese AI chip development. Beijing calls it economic coercion."},
    {"pair": "CN-US", "country_a": "CN", "country_b": "US",
     "query": "China US spy balloon incident",
     "text": "US shoots down Chinese surveillance balloon over the Atlantic. China denies it was a spy balloon, calls it a weather research craft."},
    {"pair": "CN-US", "country_a": "CN", "country_b": "US",
     "query": "China US TikTok ban legislation",
     "text": "US Congress passes legislation forcing sale or ban of TikTok. China calls it an abuse of state power and threatens retaliation."},
    {"pair": "CN-US", "country_a": "CN", "country_b": "US",
     "query": "China US military hotline communication",
     "text": "US and China restore military-to-military communication hotline after months of suspension following Taiwan tensions."},
    {"pair": "CN-US", "country_a": "CN", "country_b": "US",
     "query": "China US fentanyl sanctions",
     "text": "US sanctions Chinese companies for supplying fentanyl precursors. Beijing denies responsibility and threatens countermeasures."},

    # ── North Korea–US (KP-US) ────────────────────────────────────────────────
    {"pair": "KP-US", "country_a": "KP", "country_b": "US",
     "query": "North Korea ICBM missile test Japan",
     "text": "North Korea fires intercontinental ballistic missile that flew over Japan before landing in the Pacific Ocean."},
    {"pair": "KP-US", "country_a": "KP", "country_b": "US",
     "query": "North Korea US diplomacy Kim Trump",
     "text": "Trump signals openness to meeting Kim Jong-un again. North Korea has not responded to diplomatic overtures."},
    {"pair": "KP-US", "country_a": "KP", "country_b": "US",
     "query": "North Korea Russia troops Ukraine",
     "text": "North Korea sends additional troops and ammunition to support Russian forces in Ukraine. US condemns the military cooperation."},
    {"pair": "KP-US", "country_a": "KP", "country_b": "US",
     "query": "North Korea nuclear test underground",
     "text": "Seismic activity detected near North Korea's Punggye-ri nuclear test site. US and South Korea on high alert."},
    {"pair": "KP-US", "country_a": "KP", "country_b": "US",
     "query": "North Korea sanctions violations",
     "text": "UN panel reports North Korea has evaded $3 billion in sanctions through cryptocurrency theft and ship-to-ship transfers."},
    {"pair": "KP-US", "country_a": "KP", "country_b": "US",
     "query": "North Korea South Korea border tension",
     "text": "North Korea sends balloons carrying trash and manure across the border into South Korea. Seoul suspends military agreement."},
    {"pair": "KP-US", "country_a": "KP", "country_b": "US",
     "query": "US South Korea military exercises",
     "text": "US and South Korea conduct largest joint military exercises in years. North Korea calls it rehearsal for invasion."},
]

# How many posts to sample per pair on each refresh
_SAMPLE_SIZE_PER_PAIR = 5


def _assign_fresh_timestamps(posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Assign fresh timestamps relative to now so each refresh looks like
    recently collected data. Spreads posts over the last 6 hours.
    """
    now = datetime.utcnow()
    result = []
    for i, post in enumerate(posts):
        # Spread evenly over last 6 hours, with small random jitter
        minutes_ago = int((6 * 60 / max(len(posts), 1)) * i) + random.randint(0, 15)
        ts = now - timedelta(minutes=minutes_ago)
        result.append({
            **post,
            "posted_at": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": "demo_collected",
        })
    return result


def get_demo_posts(pair: Optional[str] = None, sample: bool = True) -> List[Dict[str, Any]]:
    """
    Return demo posts, optionally filtered by pair and randomly sampled.
    Each call returns a different random subset when sample=True.
    """
    pool = _POST_POOL if pair is None else [p for p in _POST_POOL if p["pair"] == pair]

    if not sample:
        return _assign_fresh_timestamps(pool)

    # Sample per pair so each pair always has representation
    pairs_in_pool: Dict[str, List] = {}
    for post in pool:
        pairs_in_pool.setdefault(post["pair"], []).append(post)

    sampled = []
    for pair_key, pair_posts in pairs_in_pool.items():
        n = min(_SAMPLE_SIZE_PER_PAIR, len(pair_posts))
        sampled.extend(random.sample(pair_posts, n))

    return _assign_fresh_timestamps(sampled)


def get_demo_validation_sentences() -> List[Dict[str, str]]:
    """Return the 5 fixed validation sentences."""
    return DEMO_VALIDATION_SENTENCES


def score_demo_posts(pair: Optional[str] = None) -> Dict[str, Any]:
    """
    Score a fresh random sample of demo posts through the full NLP pipeline.
    Each call returns a different subset with fresh timestamps.
    """
    from services.nlp_inference import get_nlp_service

    svc = get_nlp_service()

    # Get a fresh random sample
    posts = get_demo_posts(pair=pair, sample=True)

    if not posts:
        return {"error": f"No demo posts found for pair: {pair}"}

    # Group by pair
    pairs_grouped: Dict[str, List[Dict]] = {}
    for post in posts:
        pairs_grouped.setdefault(post["pair"], []).append(post)

    results = {}
    for pair_key, pair_posts in pairs_grouped.items():
        texts = [p["text"] for p in pair_posts]
        scored = svc.score_texts(texts)

        enriched = []
        for post, score in zip(pair_posts, scored):
            enriched.append({
                **score,
                "pair":      post["pair"],
                "country_a": post["country_a"],
                "country_b": post["country_b"],
                "source":    post["source"],
                "query":     post["query"],
                "posted_at": post["posted_at"],
            })

        aggregate = svc.aggregate_country_risk(
            scored,
            country=pair_key,
            window_label=f"demo_refresh_{datetime.utcnow().strftime('%H%M%S')}",
        )

        results[pair_key] = {
            "pair_key":  pair_key,
            "country_a": pair_posts[0]["country_a"],
            "country_b": pair_posts[0]["country_b"],
            "posts":     enriched,
            "aggregate": aggregate,
            "data_note": "⚠️ DEMO DATA — Sampled posts (refreshed). Not live social intelligence.",
        }

    return results


def score_validation_sentences() -> List[Dict[str, Any]]:
    """
    Score the 5 validation sentences. Results are deterministic
    (same text → same model output) but returned with a fresh timestamp.
    """
    from services.nlp_inference import get_nlp_service

    svc = get_nlp_service()
    sentences = get_demo_validation_sentences()
    texts = [s["text"] for s in sentences]
    scored = svc.score_texts(texts)

    results = []
    for sentence, score in zip(sentences, scored):
        results.append({
            **score,
            "expected": sentence["expected"],
            "context":  sentence["context"],
            "correct":  score["label_name"] == sentence["expected"],
        })

    return results
