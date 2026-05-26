"""Clear and reseed database with only 4 CRITICAL/HIGH pairs"""
import logging
from database import get_db_session, init_db
from models.risk_score import RiskScore
from models.intel_brief import IntelBrief
from models.alert import Alert
from models.sentiment_score import SentimentScore
from models.market_snapshot import MarketSnapshot
from models.gdelt_event import GdeltEvent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def clear_all_data():
    """Clear all existing data from the database"""
    with get_db_session() as db:
        logger.info("Clearing existing data...")
        
        # Delete in order to respect foreign key constraints
        db.query(IntelBrief).delete()
        db.query(Alert).delete()
        db.query(RiskScore).delete()
        db.query(SentimentScore).delete()
        db.query(MarketSnapshot).delete()
        db.query(GdeltEvent).delete()
        
        db.commit()
        logger.info("All data cleared successfully")

if __name__ == "__main__":
    init_db()
    clear_all_data()
    
    # Now run the seed
    logger.info("Running seed_demo.py...")
    from seed_demo import run_seed
    run_seed()
    
    print("\n" + "="*80)
    print("DATABASE RESEEDED WITH 4 CRITICAL/HIGH PAIRS")
    print("="*80)
    print("\n✅ CRITICAL/HIGH pairs:")
    print("  1. RU-UA: 95.0 (CRITICAL) - Active war")
    print("  2. IL-IR: 88.0 (CRITICAL) - Shadow conflict")
    print("  3. US-IR: 75.0 (CRITICAL) - Nuclear tensions")
    print("  4. IL-PS: 72.0 (HIGH) - Israeli-Palestinian conflict")
    print("\n✅ All other pairs: LOW (6-28 range)")
    print("\nPlease refresh your browser to see the updated data.")
