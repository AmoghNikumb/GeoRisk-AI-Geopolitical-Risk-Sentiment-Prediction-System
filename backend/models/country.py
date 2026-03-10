"""
models/country.py — Country metadata table.
Seeded once from data/countries.json.
"""
from sqlalchemy import Column, String, Float, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Country(Base):
    __tablename__ = "countries"

    # ISO 3166-1 alpha-2 code (e.g. "US", "CN", "IN")
    code        = Column(String(2), primary_key=True)
    name        = Column(String(100), nullable=False)          # "United States"
    full_name   = Column(String(200))                          # "United States of America"
    region      = Column(String(100))                          # "North America"
    flag_emoji  = Column(String(10))                           # "🇺🇸"

    # Market ticker symbols for this country
    stock_index_ticker = Column(String(20))                    # "^GSPC", "NSEI", "000001.SS"
    currency_code      = Column(String(3))                     # "USD", "CNY"

    # Metadata
    is_tracked  = Column(Boolean, default=True)                # Include in active monitoring
    created_at  = Column(DateTime, default=datetime.utcnow)

    # Relationships
    politicians = relationship("Politician", back_populates="country")

    def __repr__(self):
        return f"<Country {self.code} — {self.name}>"

    def to_dict(self):
        return {
            "code": self.code,
            "name": self.name,
            "region": self.region,
            "flag_emoji": self.flag_emoji,
            "stock_index_ticker": self.stock_index_ticker,
        }

