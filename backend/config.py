"""
config.py — Centralized settings using pydantic-settings.
All environment variables are loaded from .env automatically.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────
    database_url: str = "sqlite:///./georisk.db"

    # ── Redis (optional) ──────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Apify ─────────────────────────────────────────────
    apify_api_key: str = ""
    # Actor to use for live Twitter scraping.
    # Default: apidojo/tweet-scraper (well-maintained, rich field set)
    apify_twitter_actor: str = "apidojo/tweet-scraper"
    # Max tweets to fetch per scheduled run (controls Apify compute cost)
    apify_max_tweets: int = 100

    # ── Reddit ────────────────────────────────────────────
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "GeoRiskAI/1.0"

    # ── HuggingFace ───────────────────────────────────────
    huggingface_api_key: str = ""

    # ── LLM ───────────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # ── App ───────────────────────────────────────────────
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # ── Feature Flags ─────────────────────────────────────
    enable_scheduler: bool = True
    enable_reddit: bool = False      # stub until credentials provided
    enable_twitter: bool = False     # stub until credentials provided
    enable_gdelt: bool = True
    enable_markets: bool = True
    seed_demo_data: bool = True      # Seed realistic demo data on startup

    # ── Model Backend ─────────────────────────────────────
    # "pickle" → load georisk_lr.pkl + georisk_lr_scaler.pkl (default)
    #            LogisticRegression trained on GDELT 1979-2013 (59 features)
    #            Output: P(High Risk) * 100 → 0-100 risk score
    #            Accuracy: 92.8%  F1-macro: 0.907
    # "dummy"  → rule-based placeholder (debug/fallback only)
    model_backend: str = "pickle"
    model_path: str = "models/georisk_lr.pkl"
    scaler_path: str = "models/georisk_lr_scaler.pkl"

    # ── NLP Inference Pipeline ────────────────────────────
    # RoBERTa model for text → sentiment scoring
    # Pipeline: text → RoBERTa → per-post risk → LR aggregate
    nlp_roberta_model: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"

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
    alert_score_jump: float = 15.0
    alert_vix_spike: float = 20.0

    # ── LLM Brief Cache ───────────────────────────────────
    brief_cache_hours: int = 6

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
