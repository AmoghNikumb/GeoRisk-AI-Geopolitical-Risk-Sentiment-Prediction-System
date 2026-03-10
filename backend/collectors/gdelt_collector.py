"""
collectors/gdelt_collector.py
Fetches real conflict events from the GDELT Project (free, no API key).
Filters for high-conflict events (GoldsteinScale < -5).
Runs every 15 minutes via APScheduler.
GDELT Docs: https://www.gdeltproject.org/data.html
"""
import logging
import io
import zipfile
import csv
from datetime import datetime, timedelta
from typing import List, Optional

import requests

from database import get_db_session
from models.gdelt_event import GdeltEvent

logger = logging.getLogger(__name__)

# ── GDELT API URLs ────────────────────────────────────────────────────────────
# Last 15 minutes update list
GDELT_LASTUPDATE_URL = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"

# GDELT Event column positions (GDELT 2.0 format)
# Full schema: http://data.gdeltproject.org/documentation/GDELT-Event_Codebook-V2.0.pdf
COL = {
    "GLOBALEVENTID": 0,
    "SQLDATE": 1,
    "Actor1Code": 5,
    "Actor1Name": 6,
    "Actor1CountryCode": 7,
    "Actor2Code": 15,
    "Actor2Name": 16,
    "Actor2CountryCode": 17,
    "EventCode": 26,
    "GoldsteinScale": 30,
    "NumMentions": 31,
    "NumSources": 32,
    "NumArticles": 33,
    "AvgTone": 34,
    "ActionGeo_FullName": 53,
    "ActionGeo_CountryCode": 55,
    "ActionGeo_Lat": 56,
    "ActionGeo_Long": 57,
}

# Only keep events with GoldsteinScale below this threshold
GOLDSTEIN_THRESHOLD = -5.0


def _get_latest_event_file_url() -> Optional[str]:
    """Fetch the URL of the most recent GDELT event file."""
    try:
        resp = requests.get(GDELT_LASTUPDATE_URL, timeout=15)
        resp.raise_for_status()
        for line in resp.text.strip().split("\n"):
            parts = line.strip().split(" ")
            if len(parts) >= 3 and "export.CSV.zip" in parts[2]:
                return parts[2]
        return None
    except Exception as e:
        logger.error(f"Failed to get GDELT lastupdate: {e}")
        return None


def _download_and_parse(url: str) -> List[dict]:
    """Download a GDELT .CSV.zip and parse the event rows."""
    events = []
    try:
        resp = requests.get(url, timeout=60, stream=True)
        resp.raise_for_status()

        with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
            csv_name = [n for n in z.namelist() if n.endswith(".CSV")][0]
            with z.open(csv_name) as f:
                reader = csv.reader(io.TextIOWrapper(f, encoding="utf-8"), delimiter="\t")
                for row in reader:
                    if len(row) < 58:
                        continue
                    try:
                        goldstein = float(row[COL["GoldsteinScale"]] or 0)
                    except ValueError:
                        continue

                    if goldstein >= GOLDSTEIN_THRESHOLD:
                        continue   # Skip non-conflictual events

                    actor1_country = row[COL["Actor1CountryCode"]].strip() or None
                    actor2_country = row[COL["Actor2CountryCode"]].strip() or None

                    if not actor1_country and not actor2_country:
                        continue  # Skip events with no country actors

                    date_str = row[COL["SQLDATE"]].strip()
                    try:
                        event_date = datetime.strptime(date_str, "%Y%m%d")
                    except ValueError:
                        event_date = datetime.utcnow()

                    events.append({
                        "gdelt_event_id": row[COL["GLOBALEVENTID"]].strip(),
                        "event_date": event_date,
                        "actor1_country": actor1_country,
                        "actor2_country": actor2_country,
                        "actor1_name": row[COL["Actor1Name"]].strip()[:200] or None,
                        "actor2_name": row[COL["Actor2Name"]].strip()[:200] or None,
                        "event_code": row[COL["EventCode"]].strip()[:10],
                        "goldstein_scale": goldstein,
                        "num_articles": int(row[COL["NumArticles"]] or 0),
                        "num_sources": int(row[COL["NumSources"]] or 0),
                        "avg_tone": float(row[COL["AvgTone"]] or 0),
                        "action_country": row[COL["ActionGeo_CountryCode"]].strip()[:10] or None,
                        "action_geo_name": row[COL["ActionGeo_FullName"]].strip()[:200] or None,
                        "action_lat": float(row[COL["ActionGeo_Lat"]] or 0) or None,
                        "action_long": float(row[COL["ActionGeo_Long"]] or 0) or None,
                    })
    except Exception as e:
        logger.error(f"Error parsing GDELT file {url}: {e}")

    return events


class GdeltCollector:
    def __init__(self):
        logger.info("GdeltCollector initialized.")

    def _save_events(self, events: List[dict]) -> int:
        saved = 0
        with get_db_session() as db:
            for ev in events:
                exists = db.query(GdeltEvent).filter_by(
                    gdelt_event_id=ev["gdelt_event_id"]
                ).first()
                if exists:
                    continue
                db.add(GdeltEvent(**ev))
                saved += 1
        return saved

    def run(self) -> int:
        """Main entry point — called by scheduler every 15 mins."""
        logger.info("GDELT collector starting...")
        url = _get_latest_event_file_url()
        if not url:
            logger.error("Could not get GDELT event file URL.")
            return 0

        logger.info(f"Downloading GDELT file: {url}")
        events = _download_and_parse(url)
        logger.info(f"Parsed {len(events)} conflictual events (GS < {GOLDSTEIN_THRESHOLD})")

        saved = self._save_events(events)
        logger.info(f"GDELT collector done: {saved} new events saved.")
        return saved

