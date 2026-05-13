"""
routes/markets.py
─────────────────
GET /api/markets/ticker        — structured data for the marquee bar (from DB)
GET /api/markets/ticker/live   — fresh prices fetched directly from yfinance
GET /api/markets/snapshot      — latest full market snapshot
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from database import get_db
from models.market_snapshot import MarketSnapshot

router = APIRouter()

# ── Ticker symbol registry (matches market_collector.py) ─────────────────────
LIVE_TICKERS = [
    {"symbol": "SPX",    "label": "S&P 500",      "yf": "^GSPC",      "prefix": "",  "suffix": ""},
    {"symbol": "NDX",    "label": "Nasdaq",        "yf": "^IXIC",      "prefix": "",  "suffix": ""},
    {"symbol": "DJIA",   "label": "Dow Jones",     "yf": "^DJI",       "prefix": "",  "suffix": ""},
    {"symbol": "VIX",    "label": "VIX",           "yf": "^VIX",       "prefix": "",  "suffix": ""},
    {"symbol": "GOLD",   "label": "Gold",          "yf": "GC=F",       "prefix": "$", "suffix": ""},
    {"symbol": "WTI",    "label": "WTI Crude",     "yf": "CL=F",       "prefix": "$", "suffix": ""},
    {"symbol": "DXY",    "label": "USD Index",     "yf": "DX-Y.NYB",   "prefix": "",  "suffix": ""},
    {"symbol": "NIFTY",  "label": "Nifty 50",      "yf": "^NSEI",      "prefix": "₹", "suffix": ""},
    {"symbol": "SENSEX", "label": "Sensex",        "yf": "^BSESN",     "prefix": "₹", "suffix": ""},
    {"symbol": "NIKKEI", "label": "Nikkei 225",    "yf": "^N225",      "prefix": "¥", "suffix": ""},
    {"symbol": "DAX",    "label": "DAX",           "yf": "^GDAXI",     "prefix": "€", "suffix": ""},
    {"symbol": "FTSE",   "label": "FTSE 100",      "yf": "^FTSE",      "prefix": "£", "suffix": ""},
    {"symbol": "SSE",    "label": "Shanghai",      "yf": "000001.SS",  "prefix": "¥", "suffix": ""},
    {"symbol": "KSE",    "label": "KSE 100",       "yf": "^KSE100",    "prefix": "₨", "suffix": ""},
    {"symbol": "BTC",    "label": "Bitcoin",       "yf": "BTC-USD",    "prefix": "$", "suffix": ""},
]


def _direction(change: float | None) -> str:
    if change is None:
        return "flat"
    if change > 0.05:
        return "up"
    if change < -0.05:
        return "down"
    return "flat"


def _fetch_live_price(yf_symbol: str):
    """Fetch latest price + % change via yfinance. Returns (price, pct_change)."""
    try:
        import yfinance as yf
        ticker = yf.Ticker(yf_symbol)
        data = ticker.history(period="2d", interval="1d")
        if len(data) >= 2:
            prev  = float(data["Close"].iloc[-2])
            curr  = float(data["Close"].iloc[-1])
            pct   = round((curr - prev) / prev * 100, 3) if prev else None
            return round(curr, 2), pct
        elif len(data) == 1:
            curr = float(data["Close"].iloc[-1])
            return round(curr, 2), None
        # Fallback to fast_info
        fi = ticker.fast_info
        price = fi.get("last_price") or fi.get("regularMarketPrice")
        pct   = fi.get("regularMarketChangePercent")
        return (round(float(price), 2) if price else None,
                round(float(pct) * 100, 3) if pct else None)
    except Exception:
        return None, None


def _build_ticker_item(t: dict, price: Optional[float], pct: Optional[float]) -> dict:
    return {
        "symbol":         t["symbol"],
        "label":          t["label"],
        "prefix":         t["prefix"],
        "value":          price,
        "change_percent": pct,
        "direction":      _direction(pct),
    }


# ── DB-backed ticker (fast, uses last saved snapshot) ────────────────────────
@router.get("/markets/ticker")
def get_market_ticker(db: Session = Depends(get_db)):
    market = db.query(MarketSnapshot).order_by(MarketSnapshot.captured_at.desc()).first()

    sp_chg = market.sp500_change_pct if market else None

    # Map DB fields to ticker items
    db_values = {
        "SPX":    (market.sp500,        sp_chg),
        "NDX":    (None,                None),
        "DJIA":   (None,                None),
        "VIX":    (market.vix,          None),
        "GOLD":   (market.gold,         None),
        "WTI":    (market.crude_oil,    None),
        "DXY":    (market.dxy,          None),
        "NIFTY":  (market.india_nifty,  None),
        "SENSEX": (None,                None),
        "NIKKEI": (market.japan_nikkei, None),
        "DAX":    (market.germany_dax,  None),
        "FTSE":   (market.uk_ftse,      None),
        "SSE":    (market.china_sse,    None),
        "KSE":    (market.pakistan_kse, None),
        "BTC":    (None,                None),
    } if market else {}

    ticker = []
    for t in LIVE_TICKERS:
        price, pct = db_values.get(t["symbol"], (None, None))
        ticker.append(_build_ticker_item(t, price, pct))

    return {
        "ticker":         ticker,
        "market_stress":  round(market.market_stress_score, 3) if market and market.market_stress_score else None,
        "captured_at":    market.captured_at.isoformat() if market else None,
    }


# ── Live ticker (fetches fresh prices directly, ~5-10s latency) ──────────────
@router.get("/markets/ticker/live")
def get_live_ticker():
    """
    Fetches current prices directly from yfinance for all ticker symbols.
    Use sparingly — each call hits Yahoo Finance for all symbols.
    The frontend should call this once on load, then poll /markets/ticker (DB).
    """
    ticker = []
    for t in LIVE_TICKERS:
        price, pct = _fetch_live_price(t["yf"])
        ticker.append(_build_ticker_item(t, price, pct))

    return {
        "ticker":      ticker,
        "captured_at": datetime.utcnow().isoformat(),
        "live":        True,
    }


# ── Full snapshot ─────────────────────────────────────────────────────────────
@router.get("/markets/snapshot")
def get_market_snapshot(db: Session = Depends(get_db)):
    market = db.query(MarketSnapshot).order_by(MarketSnapshot.captured_at.desc()).first()
    if not market:
        return {"snapshot": None}
    return {
        "snapshot": {
            "vix":                market.vix,
            "sp500":              market.sp500,
            "sp500_change_pct":   market.sp500_change_pct,
            "crude_oil":          market.crude_oil,
            "gold":               market.gold,
            "dxy":                market.dxy,
            "india_nifty":        market.india_nifty,
            "china_sse":          market.china_sse,
            "russia_moex":        market.russia_moex,
            "germany_dax":        market.germany_dax,
            "uk_ftse":            market.uk_ftse,
            "japan_nikkei":       market.japan_nikkei,
            "pakistan_kse":       market.pakistan_kse,
            "market_stress_score": market.market_stress_score,
            "captured_at":        market.captured_at.isoformat() if market.captured_at else None,
        }
    }
