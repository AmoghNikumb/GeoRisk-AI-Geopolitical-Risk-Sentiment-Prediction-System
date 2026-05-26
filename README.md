# GeoRisk AI

Geopolitical risk sentiment prediction and intelligence platform.

GeoRisk AI combines social discourse, politician communications, conflict-event data, market indicators, NLP sentiment analysis, and LLM-ready intelligence brief generation to monitor geopolitical risk across country pairs.

The project currently contains a FastAPI backend, a Next.js frontend, database models, scheduled data collectors, risk scoring logic, alerting, and documentation for setup, architecture, and system review.

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
## Repository Layout

```text
.
|-- README.md
|-- QUICK_START.md
|-- SYSTEM_ARCHITECTURE.md
|-- SYSTEM_REVIEW_SUMMARY.md
|-- FRONTEND_BACKEND.md
|-- georisk_setup.sh
|-- GeoRisk_AI_Finetuning.ipynb
|-- georisk-ai/
|   |-- backend/
|   |   |-- main.py
|   |   |-- config.py
|   |   |-- database.py
|   |   |-- scheduler.py
|   |   |-- collectors/
|   |   |-- processors/
|   |   |-- sentiment/
|   |   |-- scoring/
|   |   |-- llm/
|   |   |-- models/
|   |   |-- routes/
|   |   |-- services/
|   |   |-- data/
|   |   |-- alembic/
|   |   |-- requirements.txt
|   |   `-- seed_demo.py
|   |-- frontend/
|   |   |-- app/
|   |   |-- components/
|   |   |-- hooks/
|   |   |-- lib/
|   |   |-- store/
|   |   |-- public/
|   |   |-- package.json
|   |   `-- tailwind.config.ts
|   |-- docker/
|   |-- ml/
|   `-- nlp/
|-- venv/
`-- new_venv/
```

## System Overview

GeoRisk AI is structured as an end-to-end risk intelligence pipeline:

```text
Data sources
  |-- Reddit public discourse
  |-- Twitter/X politician and keyword posts
  |-- GDELT conflict and geopolitical event data
  `-- Market data through yfinance

        |
        v

Raw ingestion
  -> raw_posts, gdelt_events, market_snapshots

        |
        v

Processing and NLP
  -> text cleaning
  -> language detection
  -> country/person entity extraction
  -> HuggingFace sentiment scoring
  -> hourly sentiment aggregation

        |
        v

Risk engine
  -> negative sentiment
  -> sentiment deterioration
  -> politician hostility
  -> GDELT conflict intensity
  -> VIX spike
  -> market stress

        |
        v

Application layer
  -> dashboard API
  -> bilateral analysis API
  -> entities API
  -> alerts API
  -> intelligence brief generation
  -> Next.js frontend
```

## Tech Stack

Backend:

- Python 3.10+
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- Redis, optional
- APScheduler
- HuggingFace Transformers
- spaCy
- langdetect
- PRAW
- ntscraper
- yfinance
- Gemini brief generation support, with Anthropic SDK present for optional Claude integration work

Frontend:

- Next.js 16
- React 19
- TypeScript
- Tailwind CSS
- Recharts
- Lucide React
- Zustand
- date-fns

## Quick Start

### 1. Backend Setup

```bash
cd georisk-ai/backend

python -m venv venv
source venv/bin/activate
# Windows PowerShell:
# .\venv\Scripts\Activate.ps1

pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

Create or update `georisk-ai/backend/.env`:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/georisk_ai
REDIS_URL=redis://localhost:6379/0
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
HUGGINGFACE_API_KEY=your_huggingface_token
GEMINI_API_KEY=your_gemini_key_if_used
APP_ENV=development
LOG_LEVEL=INFO
```

Initialize the database:

```bash
python -c "from database import init_db; init_db()"
```

Or, if using Alembic migrations:

```bash
alembic upgrade head
```

Start the backend:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend URLs:

- API: `http://localhost:8000`
- Health check: `http://localhost:8000/health`
- Swagger docs: `http://localhost:8000/docs`

### 2. Frontend Setup

```bash
cd georisk-ai/frontend
npm install
```

Create or update `georisk-ai/frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Start the frontend:

```bash
npm run dev
```

Frontend URL:

- `http://localhost:3000`

## API Endpoints

Core:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | Backend health check |
| GET | `/api/v1/system/status` | System status |
| GET | `/api/dashboard` | Dashboard summary, risk scores, market data, alerts |
| GET | `/api/bilateral?a=US&b=CN` | Detailed country-pair analysis |
| GET | `/api/entities?country=US` | Politicians, entities, posts, and inflammatory content |
| GET | `/api/alerts` | List recent alerts |
| PATCH | `/api/alerts/{alert_id}/read` | Mark one alert as read |
| PATCH | `/api/alerts/read-all` | Mark all alerts as read |
| POST | `/api/briefs/generate` | Generate an intelligence brief |

Additional current routes:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/markets/ticker` | Market ticker lookup |
| GET | `/api/markets/snapshot` | Market snapshot data |
| GET | `/api/jobs/status` | Scheduler/job status |
| POST | `/api/jobs/run/{job_name}` | Run a named background job manually |
| POST | `/api/model/predict` | Model prediction endpoint |
| GET | `/api/model/status` | Model service status |

## Risk Score Formula

The composite risk score is calculated on a 0-100 scale:

```text
risk_score = (
  0.25 * negative_sentiment_score +
  0.20 * sentiment_deterioration_rate +
  0.15 * politician_hostility_score +
  0.20 * gdelt_conflict_intensity +
  0.10 * vix_spike_score +
  0.10 * market_stress_score
) * 100
```

Risk bands:

| Score | Classification |
| --- | --- |
| 0-30 | Low |
| 30-60 | Moderate |
| 60-80 | High |
| 80-100 | Critical |

## Scheduled Jobs

The backend scheduler runs recurring jobs for data ingestion and analysis:

| Job | Purpose | Typical Interval |
| --- | --- | --- |
| `reddit` | Collect Reddit posts from geopolitical communities and keywords | 30 minutes |
| `twitter` | Collect politician and keyword posts | 30 minutes |
| `market` | Fetch VIX, S&P 500, oil, gold, and other market indicators | 15 minutes |
| `gdelt` | Fetch conflict and geopolitical events | 15 minutes |
| `scoring` | Clean, process, and score unprocessed posts | 60 minutes |
| `aggregate` | Aggregate sentiment into time buckets | 60 minutes |
| `risk` | Compute composite risk scores | 60 minutes |
| `alerts` | Detect risk jumps and alert conditions | 15 minutes |
| `briefs` | Generate intelligence briefs for top pairs | 6 hours |

Exact intervals are controlled through backend settings.

## Frontend Progress

Implemented frontend capabilities include:

- Main dashboard with monitored country-pair summary.
- Risk heatmap for tracked pairs.
- Market indicators panel.
- Alerts widget with read/unread handling.
- Risk trend chart using Recharts.
- Bilateral analysis page with country-pair detail.
- Entities page foundation for tracked politicians and key figures.
- API utility layer and React hooks for data fetching.
- Responsive layout using Next.js, React, TypeScript, and Tailwind CSS.

## Backend Progress

Implemented backend capabilities include:

- FastAPI app entry point in `backend/main.py`.
- Modular route files under `backend/routes/`.
- SQLAlchemy database setup in `backend/database.py`.
- ORM models under `backend/models/`.
- Scheduled job orchestration in `backend/scheduler.py`.
- Collectors for Reddit, Twitter/X, market data, and GDELT.
- Processing modules for text cleaning, language detection, entity extraction, and aggregation.
- HuggingFace-based sentiment scoring.
- Risk scoring and alerting modules.
- LLM-ready brief generator.
- Demo seed script in `backend/seed_demo.py`.

## Data Model Summary

Primary tables/models:

- `raw_posts`: source posts before processing.
- `processed_posts`: cleaned posts, extracted entities, language metadata, and sentiment.
- `sentiment_scores`: aggregated sentiment by country and time bucket.
- `risk_scores`: final country-pair risk scores and component breakdowns.
- `market_snapshots`: market indicators and stress data.
- `gdelt_events`: geopolitical and conflict event records.
- `alerts`: alert records for risk spikes and critical signals.
- `intel_briefs`: generated intelligence reports.
- `countries`: country reference data.
- `politicians`: tracked political figures and influence metadata.

## Tracked Country Pairs

The documented baseline tracks these pairs:

```text
CN-US
IN-PK
RU-UA
IL-IR
IN-CN
KP-US
KP-KR
IL-SA
RU-GB
CN-TW
TR-GR
IN-US
```

## API Credentials

Required or optional credentials:

| Service | Required | Notes |
| --- | --- | --- |
| Reddit | Yes for Reddit collection | Create an app at Reddit preferences/apps |
| HuggingFace | Recommended | Used for hosted/model access depending on configuration |
| Gemini | Optional/current brief generator integration | Used for AI-generated intelligence briefs if configured |
| Anthropic | Optional/future integration path | SDK is present in dependencies, older docs mention Claude support |
| Twitter/X | No API key in documented setup | Uses ntscraper |
| GDELT | No | Public data source |
| yfinance | No | Public market data library |

## Testing and Verification

Backend checks:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/dashboard
curl "http://localhost:8000/api/bilateral?a=US&b=CN"
curl http://localhost:8000/api/alerts
```

Frontend checks:

```bash
cd georisk-ai/frontend
npm run lint
npm run build
```

Database check:

```bash
cd georisk-ai/backend
python -c "from database import init_db; init_db(); print('database ok')"
```

## Deployment Notes

Before production deployment:

- Use a real PostgreSQL instance and secure `DATABASE_URL`.
- Keep `.env` and `.env.local` out of source control.
- Restrict CORS origins to deployed frontend domains.
- Add authentication and authorization before exposing sensitive endpoints.
- Add API rate limiting.
- Configure structured logging and monitoring.
- Set up database backups and retention policy.
- Run frontend production build with `npm run build`.
- Run backend behind a production ASGI server/process manager.
- Review collector rate limits and API terms for each data source.

## Roadmap

Recommended next work:

- Replace template/mock intelligence briefs with live LLM generation where not already enabled.
- Add model evaluation and fine-tuned geopolitical sentiment model workflow.
- Add 24-72 hour risk forecasting.
- Add anomaly detection for abnormal sentiment/event spikes.
- Add WebSocket or server-sent-events support for live dashboard updates.
- Add authentication, user roles, and audit logging.
- Add deployment manifests for cloud hosting.
- Add automated test coverage for collectors, processors, scoring, and routes.

## Documentation Map

Read these files for more detail:

- `QUICK_START.md`: practical setup and local deployment guide.
- `SYSTEM_ARCHITECTURE.md`: deeper backend/frontend/data-flow architecture.
- `SYSTEM_REVIEW_SUMMARY.md`: implementation review and progress summary.
- `FRONTEND_BACKEND.md`: frontend/backend integration notes.
- `georisk-ai/README.md`: older project README retained for reference.

## Project Version

Current documented version: `1.0.0-rc1`

Last updated in this README: 2026-05-05
