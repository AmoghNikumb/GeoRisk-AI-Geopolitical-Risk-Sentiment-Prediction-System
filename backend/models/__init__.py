"""
models/__init__.py
Importing all models here ensures SQLAlchemy registers them
when `import models` is called in database.py → init_db().
"""
from models.country import Country
from models.politician import Politician
from models.raw_post import RawPost
from models.processed_post import ProcessedPost
from models.market_snapshot import MarketSnapshot
from models.gdelt_event import GdeltEvent
from models.sentiment_score import SentimentScore
from models.risk_score import RiskScore
from models.intel_brief import IntelBrief
from models.alert import Alert

__all__ = [
    "Country",
    "Politician",
    "RawPost",
    "ProcessedPost",
    "MarketSnapshot",
    "GdeltEvent",
    "SentimentScore",
    "RiskScore",
    "IntelBrief",
    "Alert",
]

