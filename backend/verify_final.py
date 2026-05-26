"""Verify final database state"""
from database import get_db_session
from models.risk_score import RiskScore
from models.intel_brief import IntelBrief

with get_db_session() as db:
    # Get latest risk scores
    scores = db.query(RiskScore).order_by(RiskScore.computed_at.desc()).limit(30).all()
    
    print("=" * 80)
    print("FINAL RISK SCORES")
    print("=" * 80)
    
    seen_pairs = set()
    for s in scores:
        if s.pair_key not in seen_pairs:
            seen_pairs.add(s.pair_key)
            print(f"{s.country_a}-{s.country_b}: {s.score:.1f} ({s.classification})")
    
    print("\n" + "=" * 80)
    print("CRITICAL/HIGH PAIRS WITH INTELLIGENCE BRIEFS")
    print("=" * 80)
    
    critical_high = db.query(RiskScore).filter(
        RiskScore.score >= 70
    ).order_by(RiskScore.score.desc()).limit(10).all()
    
    for s in critical_high:
        if s.pair_key in seen_pairs:
            brief = db.query(IntelBrief).filter(
                IntelBrief.pair_key == s.pair_key
            ).first()
            
            print(f"\n{s.country_a}-{s.country_b}: {s.score:.1f} ({s.classification})")
            if brief:
                print(f"  Brief: {brief.risk_level} - Score: {brief.risk_score_val}")
                print(f"  Headline: {brief.headline[:70]}...")
            else:
                print("  ❌ NO BRIEF!")
