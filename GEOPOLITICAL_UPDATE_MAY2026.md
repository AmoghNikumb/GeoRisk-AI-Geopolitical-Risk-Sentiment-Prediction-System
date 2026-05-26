# Geopolitical Risk Score Update — May 22, 2026

## Overview
This update calibrates the GeoRisk AI system to reflect **accurate real-world geopolitical risk scores** as of May 22, 2026, based on the detailed analysis in `datasets/currentgeo.txt`.

## Key Changes

### 1. Updated Risk Score Classification Thresholds
**Previous thresholds:**
- LOW: 0-29
- MODERATE: 30-59
- HIGH: 60-79
- CRITICAL: 80-100

**New thresholds (aligned with currentgeo.txt):**
- LOW: 0-20 (stable relations, no significant tensions)
- MODERATE: 21-40 (some friction, manageable tensions)
- HIGH: 41-60 (confrontation risk, elevated tensions)
- CRITICAL: 61-100 (severe crisis potential to active war)

### 2. Updated Country Pair Risk Scores

#### Tier 1 — Extreme / Active Conflict (CRITICAL: 78-95)
| Rank | Pair | Score | Status |
|------|------|-------|--------|
| 1 | Russia — Ukraine | 95 | Active war |
| 2 | Israel — Iran | 88 | Shadow regional conflict |
| 3 | United States — China | 82 | Systemic superpower rivalry |
| 4 | Russia — United States | 80 | Proxy confrontation |
| 5 | India — Pakistan | 78 | Fragile deterrence |

#### Tier 2 — Severe Strategic Rivalry (HIGH/CRITICAL: 60-76)
| Rank | Pair | Score | Status |
|------|------|-------|--------|
| 6 | China — Taiwan | 76 | Biggest military flashpoint in Asia |
| 7 | China — Japan | 71 | East China Sea disputes |
| 8 | Russia — United Kingdom | 69 | UK support for Ukraine |
| 9 | Russia — Germany | 68 | German rearmament |
| 10 | Russia — France | 66 | European security leadership |
| 11 | United States — Iran | 65 | Nuclear program tensions |
| 12 | China — India | 64 | Himalayan border disputes |
| 13 | North Korea — United States | 63 | Missile testing |
| 14 | North Korea — South Korea | 62 | Border militarization |
| 15 | Russia — Japan | 60 | Kuril Islands dispute |

#### Tier 3 — Moderate Strategic Friction (MODERATE: 36-48)
| Pair | Score | Summary |
|------|-------|---------|
| India — United States | 48 | Strategic partners with differences |
| Israel — Saudi Arabia | 46 | Quiet coordination |
| China — Germany | 44 | Industrial competition |
| China — France | 43 | Strategic hedging |
| China — United Kingdom | 42 | Indo-Pacific friction |
| Canada — China | 41 | Diplomatic distrust |
| Turkey — Greece | 40 | Eastern Mediterranean competition |
| Russia — Canada | 40 | Arctic tensions |
| Iran — United Kingdom | 39 | Maritime tensions |
| Iran — France | 37 | Nuclear diplomacy |
| Iran — Germany | 36 | EU sanctions |

### 3. Updated Alert Messages
Alerts now reflect the accurate severity and context:
- **RU-UA**: "Active war at 95/100 - most dangerous interstate conflict globally"
- **IL-IR**: "Shadow conflict at 88/100 - near-war environment"
- **US-CN**: "Systemic rivalry at 82/100 - defining rivalry of the decade"
- **RU-US**: "Proxy confrontation at 80/100 - primary strategic adversaries"
- **IN-PK**: "Fragile deterrence at 78/100 - nuclear dyad with crisis history"

### 4. Updated GDELT Event Data
GDELT events now reflect the intensity and frequency aligned with actual conflict levels:
- **RU-UA**: 95 articles, Goldstein -9.2 (most severe)
- **IL-IR**: 78 articles, Goldstein -8.5
- **US-CN**: 68 articles, Goldstein -7.8
- **CN-TW**: 71 articles, Goldstein -8.8

### 5. Updated Sentiment Scores
Base sentiment values calibrated to reflect actual geopolitical tensions:
- **Tier 1 conflicts**: -0.40 to -0.42 (very hostile)
- **Tier 2 rivalries**: -0.15 to -0.26 (moderately negative)
- **Tier 3 friction**: -0.04 to -0.08 (mildly negative)

## Files Modified

1. **backend/seed_demo.py**
   - Updated `DEMO_PAIRS` with 31 country pairs and accurate scores
   - Updated `DEMO_ALERTS` to reflect current crisis levels
   - Updated `base_sentiment` values for all tracked countries
   - Updated `seed_gdelt_events()` with realistic event data
   - Added new countries: JP, DE, FR, CA

2. **backend/models/risk_score.py**
   - Updated `classify()` method with new thresholds
   - Added detailed documentation of scoring model

## How to Apply Changes

### Option 1: Reset Database (Recommended)
```bash
# Delete existing database
rm backend/georisk.db

# Restart the backend - it will auto-seed with new data
cd backend
python main.py
```

### Option 2: Manual Re-seed
```bash
cd backend
python seed_demo.py
```

## Verification

After applying changes, verify in the UI:

1. **Risk Heatmap** should show:
   - RU-UA at top with 95 (CRITICAL)
   - IL-IR at 88 (CRITICAL)
   - US-CN at 82 (CRITICAL)
   - Multiple pairs in 60-80 range (CRITICAL/HIGH)

2. **Alerts** should reflect:
   - Updated severity levels
   - Accurate descriptions of conflicts
   - Proper context for each crisis

3. **Market Indicators** should display:
   - Full-width layout (no alerts section)
   - Enhanced card-based design
   - Trend indicators and descriptions

## Geopolitical Context (May 2026)

### Biggest Escalation Risks
1. **Taiwan military incident** - highest probability trigger
2. **Israel-Iran proxy escalation** - one miscalculation away
3. **Russia-NATO accidental confrontation** - proxy war spillover
4. **India-Pakistan border crisis** - nuclear dyad volatility
5. **Red Sea/Gulf maritime disruption** - regional instability

### Structural Trends
The world is fragmenting into overlapping strategic blocs:
- **Western Bloc**: US, GB, FR, DE, JP, CA
- **China-Russia Alignment**: CN, RU, partially IR
- **Non-Aligned Powers**: IN, Gulf states, others balancing

This fragmentation drives:
- Defense spending increases
- Supply-chain restructuring
- Energy-security prioritization
- Technological decoupling

## Notes

- All scores are calibrated to **real-world geopolitical conditions** as of May 22, 2026
- The scoring model uses 0-100 scale where:
  - 0-20 = stable/cooperative
  - 21-40 = manageable friction
  - 41-60 = confrontation risk
  - 61-80 = severe crisis potential
  - 81-100 = active war / near-war
- These scores will be overwritten by live ML pipeline once real data flows in
- The seed data provides realistic baseline for immediate UI functionality
