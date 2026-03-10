"""
models/market_snapshot.py — VIX, S&P, Oil, Gold, indices per timestamp.
Collected every 15 minutes by market_collector.py
"""
from sqlalchemy import Column, Integer, Float, DateTime, String
from datetime import datetime
from database import Base


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    captured_at     = Column(DateTime, default=datetime.utcnow, index=True)

    # Global Fear/Stress Indicators
    vix             = Column(Float)          # CBOE Volatility Index (fear gauge)
    sp500           = Column(Float)          # S&P 500
    sp500_change_pct = Column(Float)         # % change from prev close
    crude_oil       = Column(Float)          # WTI Crude Oil futures (CL=F)
    gold            = Column(Float)          # Gold futures (GC=F)
    dxy             = Column(Float)          # US Dollar Index (DX-Y.NYB)

    # Country-specific indices (can be NULL if not available)
    india_nifty     = Column(Float)          # NSEI
    china_sse       = Column(Float)          # 000001.SS
    russia_moex     = Column(Float)          # IMOEX.ME
    germany_dax     = Column(Float)          # ^GDAXI
    uk_ftse         = Column(Float)          # ^FTSE
    japan_nikkei    = Column(Float)          # ^N225
    pakistan_kse    = Column(Float)          # ^KSE100

    # Derived stress signal (computed post-fetch)
    # High VIX + falling indices + rising oil = elevated stress
    market_stress_score = Column(Float)      # 0.0 – 1.0

    def __repr__(self):
        return f"<MarketSnapshot {self.captured_at} VIX={self.vix}>"

