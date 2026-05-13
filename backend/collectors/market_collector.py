"""
collectors/market_collector.py
Fetches real-time financial market data using yfinance.
Runs every 15 minutes via APScheduler.
Captures: VIX, S&P500, Oil, Gold, USD Index, country indices.
"""
import logging
from datetime import datetime
from typing import Optional

import yfinance as yf

from database import get_db_session
from models.market_snapshot import MarketSnapshot

logger = logging.getLogger(__name__)

# ── Ticker Configuration ──────────────────────────────────────────────────────
GLOBAL_TICKERS = {
    "vix":       "^VIX",
    "sp500":     "^GSPC",
    "nasdaq":    "^IXIC",
    "dow":       "^DJI",
    "crude_oil": "CL=F",
    "gold":      "GC=F",
    "dxy":       "DX-Y.NYB",
    "btc":       "BTC-USD",
}

COUNTRY_TICKERS = {
    "india_nifty":   "^NSEI",
    "india_sensex":  "^BSESN",
    "china_sse":     "000001.SS",
    "russia_moex":   "IMOEX.ME",
    "germany_dax":   "^GDAXI",
    "uk_ftse":       "^FTSE",
    "japan_nikkei":  "^N225",
    "pakistan_kse":  "^KSE100",
}

ALL_TICKERS = {**GLOBAL_TICKERS, **COUNTRY_TICKERS}


def _fetch_price(ticker_symbol: str) -> Optional[float]:
    """Fetch the latest price for a ticker. Returns None on failure."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        data = ticker.history(period="1d", interval="1m")
        if not data.empty:
            return float(data["Close"].iloc[-1])
        # Fallback: use fast_info
        info = ticker.fast_info
        return float(info.get("last_price") or info.get("regularMarketPrice") or 0)
    except Exception as e:
        logger.warning(f"Failed to fetch {ticker_symbol}: {e}")
        return None


def _pct_change(ticker_symbol: str) -> Optional[float]:
    """Fetch today's % change for a ticker."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        data = ticker.history(period="2d")
        if len(data) >= 2:
            prev = data["Close"].iloc[-2]
            curr = data["Close"].iloc[-1]
            return round((curr - prev) / prev * 100, 3)
        return None
    except Exception:
        return None


def _compute_market_stress(vix: Optional[float], sp500_chg: Optional[float],
                           oil: Optional[float]) -> float:
    """
    Compute a 0–1 market stress score from raw values.
    High VIX + falling S&P + rising oil = high stress.
    """
    score = 0.0
    count = 0

    if vix is not None:
        # VIX: 0–15=calm, 15–25=moderate, 25–35=high, >35=extreme
        vix_score = min(vix / 40.0, 1.0)
        score += vix_score
        count += 1

    if sp500_chg is not None:
        # Falling S&P adds stress. -3% = high stress
        sp_stress = max(-sp500_chg / 3.0, 0.0)
        score += min(sp_stress, 1.0)
        count += 1

    if oil is not None and oil > 0:
        # Very high oil prices (>100) add geopolitical stress
        oil_score = min((oil - 50) / 80.0, 1.0) if oil > 50 else 0.0
        score += oil_score
        count += 1

    return round(score / count, 3) if count > 0 else 0.0


class MarketCollector:
    def __init__(self):
        logger.info("MarketCollector initialized.")

    def collect(self) -> Optional[MarketSnapshot]:
        """Fetch all market data and return a MarketSnapshot (not yet saved)."""
        logger.info("Fetching market data...")

        prices = {}
        for field, ticker in ALL_TICKERS.items():
            prices[field] = _fetch_price(ticker)
            logger.debug(f"  {field} ({ticker}): {prices[field]}")

        sp500_chg = _pct_change("^GSPC")

        stress = _compute_market_stress(
            vix=prices.get("vix"),
            sp500_chg=sp500_chg,
            oil=prices.get("crude_oil"),
        )

        snapshot = MarketSnapshot(
            captured_at=datetime.utcnow(),
            vix=prices.get("vix"),
            sp500=prices.get("sp500"),
            sp500_change_pct=sp500_chg,
            crude_oil=prices.get("crude_oil"),
            gold=prices.get("gold"),
            dxy=prices.get("dxy"),
            india_nifty=prices.get("india_nifty"),
            china_sse=prices.get("china_sse"),
            russia_moex=prices.get("russia_moex"),
            germany_dax=prices.get("germany_dax"),
            uk_ftse=prices.get("uk_ftse"),
            japan_nikkei=prices.get("japan_nikkei"),
            pakistan_kse=prices.get("pakistan_kse"),
            market_stress_score=stress,
        )
        return snapshot

    def run(self) -> bool:
        """Main entry point — called by scheduler every 15 mins."""
        try:
            snapshot = self.collect()
            with get_db_session() as db:
                db.add(snapshot)
            logger.info(
                f"Market snapshot saved: VIX={snapshot.vix}, "
                f"S&P={snapshot.sp500}, Stress={snapshot.market_stress_score}"
            )
            return True
        except Exception as e:
            logger.error(f"MarketCollector.run() failed: {e}")
            return False

