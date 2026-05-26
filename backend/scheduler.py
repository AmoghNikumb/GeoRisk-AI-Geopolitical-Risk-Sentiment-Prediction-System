"""
scheduler.py — APScheduler wiring all background jobs.
Jobs run in-process (no separate worker needed).
"""
import logging
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import settings

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler = None


# ── Job Functions (wrap collector/processor .run() calls) ────────────────────

def job_reddit():
    try:
        from collectors.reddit_collector import RedditCollector
        RedditCollector().run()
    except Exception as e:
        logger.error(f"Reddit job failed: {e}")


def job_twitter():
    try:
        from collectors.twitter_collector import TwitterCollector
        TwitterCollector().run()
    except Exception as e:
        logger.error(f"Twitter job failed: {e}")


def job_market():
    try:
        from collectors.market_collector import MarketCollector
        MarketCollector().run()
    except Exception as e:
        logger.error(f"Market job failed: {e}")


def job_gdelt():
    try:
        from collectors.gdelt_collector import GdeltCollector
        GdeltCollector().run()
    except Exception as e:
        logger.error(f"GDELT job failed: {e}")


def job_process_and_score():
    """Preprocessing + Sentiment scoring (runs after ingestion)."""
    try:
        from sentiment.scorer import SentimentScorer
        SentimentScorer().run()
    except Exception as e:
        logger.error(f"Scoring job failed: {e}")


def job_aggregate():
    try:
        from processors.aggregator import SentimentAggregator
        SentimentAggregator().run()
    except Exception as e:
        logger.error(f"Aggregator job failed: {e}")


def job_groq_risk_scores():
    """Score all tracked country pairs using Groq LLM."""
    try:
        from config import settings as _settings
        if not _settings.GROQ_API_KEY:
            logger.debug("Groq risk scoring skipped — GROQ_API_KEY not set")
            return
        from services.groq_risk_scorer import GroqRiskScoreEngine
        GroqRiskScoreEngine(_settings.GROQ_API_KEY).run()
    except Exception as e:
        logger.error(f"Groq risk score job failed: {e}")


def job_risk_scores():
    try:
        from scoring.risk_calculator import RiskScoreEngine
        RiskScoreEngine().run()
    except Exception as e:
        logger.error(f"Risk score job failed: {e}")


def job_alerts():
    try:
        from scoring.alert_checker import AlertChecker
        AlertChecker().run()
    except Exception as e:
        logger.error(f"Alert checker job failed: {e}")


def job_news():
    """Pre-warm the news aggregator cache every 20 minutes."""
    try:
        from services.news_aggregator import fetch_news
        result = fetch_news(force=True)
        logger.info(f"News cache refreshed: {result['total']} items")
    except Exception as e:
        logger.error(f"News aggregator job failed: {e}")


def job_apify_watcher():
    """Watch the project-root datasets/ directory and ingest any .txt or .json files found.
    
    After successful ingestion, files are moved to datasets/processed/ so they
    are not re-ingested on the next scheduler tick.
    """
    try:
        from collectors.apify_ingester import ApifyIngester
        import shutil

        # datasets/ lives one level above backend/ (project root)
        datasets_dir = Path(__file__).parent.parent / "datasets"
        processed_dir = datasets_dir / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)

        files = list(datasets_dir.glob("*.txt")) + list(datasets_dir.glob("*.json"))
        if not files:
            logger.debug("Apify watcher: no dataset files found in %s", datasets_dir)
            return

        logger.info("Apify watcher: found %d file(s) to ingest in %s", len(files), datasets_dir)
        ingester = ApifyIngester()
        for f in files:
            try:
                summary = ingester.ingest(f)
                logger.info(
                    "Apify watcher ingested %s — inserted=%d, duplicates=%d, skipped=%d",
                    f.name, summary.inserted, summary.duplicates, summary.skipped,
                )
                # Archive the file so it isn't re-ingested next run
                dest = processed_dir / f.name
                shutil.move(str(f), str(dest))
                logger.info("Apify watcher: archived %s → processed/%s", f.name, f.name)
            except Exception as e:
                logger.error("Apify watcher: failed to ingest %s: %s", f.name, e)
    except Exception as e:
        logger.error(f"Apify watcher job failed: {e}")


def job_apify_live():
    """Fetch live tweets from Apify API and ingest them."""
    try:
        from collectors.apify_collector import ApifyCollector
        ApifyCollector().run()
    except Exception as e:
        logger.error(f"Apify live collector job failed: {e}")


def job_briefs():
    """Scheduled brief generation for top 10 country pairs."""
    try:
        from llm.brief_generator import BriefGenerator
        from scoring.risk_calculator import TRACKED_PAIRS
        gen = BriefGenerator()
        # Generate for top 10 highest-risk pairs
        from database import get_db_session
        from models.risk_score import RiskScore
        with get_db_session() as db:
            top_pairs = db.query(RiskScore).order_by(
                RiskScore.score.desc()
            ).limit(10).all()
        for pair in top_pairs:
            try:
                gen.generate(pair.country_a, pair.country_b, trigger="scheduled")
            except Exception as e:
                logger.error(f"Brief gen failed for {pair.pair_key}: {e}")
    except Exception as e:
        logger.error(f"Briefs job failed: {e}")


# ── Scheduler Setup ───────────────────────────────────────────────────────────

def start_scheduler():
    global _scheduler
    _scheduler = BackgroundScheduler(
        job_defaults={"coalesce": True, "max_instances": 1, "misfire_grace_time": 300}
    )

    # Data collection — only if enabled
    if settings.enable_reddit:
        _scheduler.add_job(job_reddit, IntervalTrigger(seconds=settings.reddit_interval), id="reddit", replace_existing=True)
    if settings.enable_twitter:
        _scheduler.add_job(job_twitter, IntervalTrigger(seconds=settings.twitter_interval), id="twitter", replace_existing=True)
        _scheduler.add_job(
            job_apify_watcher,
            IntervalTrigger(seconds=settings.twitter_interval),
            id="apify_watcher",
            replace_existing=True,
        )
        # Live Apify API collector — only runs if an API key is configured
        if settings.apify_api_key:
            _scheduler.add_job(
                job_apify_live,
                IntervalTrigger(seconds=settings.twitter_interval),
                id="apify_live",
                replace_existing=True,
            )
    if settings.enable_markets:
        _scheduler.add_job(job_market, IntervalTrigger(seconds=settings.market_interval), id="market", replace_existing=True)
    if settings.enable_gdelt:
        _scheduler.add_job(job_gdelt, IntervalTrigger(seconds=settings.gdelt_interval), id="gdelt", replace_existing=True)

    # Processing + scoring — always on
    _scheduler.add_job(job_process_and_score, IntervalTrigger(seconds=settings.process_interval), id="scoring",   replace_existing=True)
    _scheduler.add_job(job_aggregate,          IntervalTrigger(seconds=settings.process_interval), id="aggregate", replace_existing=True)
    _scheduler.add_job(job_risk_scores,        IntervalTrigger(seconds=settings.process_interval), id="risk",      replace_existing=True)

    # Groq LLM risk scoring — every 30 minutes (if API key set)
    if settings.GROQ_API_KEY:
        _scheduler.add_job(job_groq_risk_scores, IntervalTrigger(seconds=1800), id="groq_risk", replace_existing=True)

    # Alerts — every 15 mins
    _scheduler.add_job(job_alerts, IntervalTrigger(seconds=settings.alert_interval), id="alerts", replace_existing=True)

    # LLM briefs — every 6 hours
    _scheduler.add_job(job_briefs, IntervalTrigger(seconds=settings.brief_interval), id="briefs", replace_existing=True)

    # News aggregator cache warm — every 20 minutes
    _scheduler.add_job(job_news, IntervalTrigger(seconds=1200), id="news", replace_existing=True)

    _scheduler.start()
    logger.info(
        f"Scheduler started with {len(_scheduler.get_jobs())} jobs:\n"
        + "\n".join(f"  • {j.id} → every {j.trigger}" for j in _scheduler.get_jobs())
    )


def shutdown_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler shut down.")

