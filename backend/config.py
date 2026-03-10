"""
config.py — Centralized settings using pydantic-settings.
All environment variables are loaded from .env automatically.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────
    database_url: str = "postgresql://postgres:password@localhost:5432/georisk_db"

    # ── Redis ─────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Reddit ────────────────────────────────────────────
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "GeoRiskAI/1.0"

    # ── HuggingFace ───────────────────────────────────────
    huggingface_api_key: str = ""

    # ── Anthropic ─────────────────────────────────────────
    anthropic_api_key: str = ""

    # ── App ───────────────────────────────────────────────
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    # ── Scheduler Intervals (seconds) ─────────────────────
    reddit_interval: int = 1800
    twitter_interval: int = 1800
    market_interval: int = 900
    gdelt_interval: int = 900
    process_interval: int = 3600
    brief_interval: int = 21600
    alert_interval: int = 900

    # ── Sentiment Models ──────────────────────────────────
    sentiment_model: str = "cardiffnlp/twitter-roberta-base-sentiment"
    finbert_model: str = "ProsusAI/finbert"
    multilingual_model: str = "cardiffnlp/twitter-xlm-roberta-base-sentiment"

    # ── Risk Scoring Weights ──────────────────────────────
    weight_negative_sentiment: float = 0.25
    weight_sentiment_deterioration: float = 0.20
    weight_politician_hostility: float = 0.15
    weight_gdelt_conflict: float = 0.20
    weight_vix_spike: float = 0.10
    weight_market_stress: float = 0.10

    # ── Alert Thresholds ──────────────────────────────────
    alert_score_jump: float = 15.0       # points in 6hrs
    alert_vix_spike: float = 20.0        # VIX absolute level

    # ── LLM Brief Cache ───────────────────────────────────
    brief_cache_hours: int = 6

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance — call this everywhere."""
    return Settings()


# Convenience alias
settings = get_settings()

