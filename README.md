# 🌍 GeoRisk AI — Geopolitical Risk Sentiment Prediction System

> Fuses Twitter/X politician tweets + Reddit public discourse + live financial market data → NLP sentiment analysis → LLM-generated intelligence briefs

---

## 🗂 Project Structure

```
georisk-ai/
├── backend/                  ← FastAPI Python backend
│   ├── main.py               ← App entry point
│   ├── config.py             ← All settings (loaded from .env)
│   ├── database.py           ← SQLAlchemy engine + session
│   ├── scheduler.py          ← APScheduler jobs
│   ├── models/               ← 10 SQLAlchemy ORM tables
│   ├── collectors/           ← Reddit, Twitter, Market, GDELT
│   ├── processors/           ← Clean, detect language, extract entities, aggregate
│   ├── sentiment/            ← HuggingFace scoring
│   ├── scoring/              ← Risk calculation + alerts
│   ├── llm/                  ← Claude API brief generation
│   ├── routes/               ← FastAPI route handlers
│   └── data/                 ← countries.json + politicians.json
├── docker/
│   └── docker-compose.yml    ← Postgres + Redis
└── frontend/                 ← Next.js (Phase 9)
```

---

## ⚡ Quick Start (Phase 0 Setup)

### 1. Clone and set up Python environment
```bash
cd georisk-ai/backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env with your API keys (see below)
```

### 3. Start Postgres + Redis (or use existing local installs)
```bash
cd ../docker
docker-compose up -d
```

### 4. Initialize database
```bash
cd ../backend
alembic upgrade head          # Run migrations
```

### 5. Start the server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**API docs:** http://localhost:8000/docs  
**Health check:** http://localhost:8000/health

---

## 🔑 Required API Keys

| Service | How to Get | Cost |
|---------|-----------|------|
| Reddit | reddit.com/prefs/apps → create app | Free |
| HuggingFace | huggingface.co/settings/tokens | Free |
| Anthropic (Claude) | console.anthropic.com | Pay-per-use |
| Twitter/X | Not needed (ntscraper) | Free |
| GDELT | Not needed (public API) | Free |
| yfinance | Not needed | Free |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/dashboard` | All country risk scores, market data, alerts |
| GET | `/api/bilateral?a=US&b=CN` | Full bilateral analysis |
| GET | `/api/entities?country=US` | Politicians + inflammatory posts |
| POST | `/api/briefs/generate` | Trigger LLM intel brief |
| GET | `/api/alerts` | Recent risk alerts |
| PATCH | `/api/alerts/{id}/read` | Mark alert as read |

---

## 🔄 Pipeline Flow

```
Reddit (PRAW) ──────┐
Twitter (ntscraper) ─┼──► raw_posts ──► processed_posts ──► sentiment_scores
Market (yfinance) ──┤                              ↓
GDELT (free API) ───┘                        risk_scores
                                                   ↓
                                           intel_briefs (Claude)
                                                   ↓
                                          alerts + dashboard
```

---

## ⏱ Scheduler Jobs

| Job | Frequency | What it does |
|-----|-----------|-------------|
| Reddit collector | Every 30 min | Scrapes 15 subreddits + keywords |
| Twitter collector | Every 30 min | Scrapes 26 politicians + keywords |
| Market collector | Every 15 min | Fetches VIX, S&P, Oil, Gold, indices |
| GDELT collector | Every 15 min | Downloads latest conflict events |
| Sentiment scorer | Every hour | Cleans + scores all unprocessed posts |
| Aggregator | Every hour | Aggregates into per-country per-hour buckets |
| Risk engine | Every hour | Computes 0–100 risk score per country pair |
| Alert checker | Every 15 min | Triggers alerts on significant score jumps |
| Brief generator | Every 6 hours | Generates Claude intelligence briefs |

---

## 🧮 Risk Score Formula

```
risk_score = (
  0.25 × negative_sentiment_score +
  0.20 × sentiment_deterioration_rate +
  0.15 × politician_hostility_score +
  0.20 × gdelt_conflict_intensity +
  0.10 × vix_spike_score +
  0.10 × market_stress_score
) × 100
```

**Classifications:**
- 🟢 0–30: LOW
- 🟡 30–60: MODERATE  
- 🟠 60–80: HIGH
- 🔴 80–100: CRITICAL

---

## 📊 Tracked Country Pairs

CN-US, IN-PK, RU-UA, IL-IR, IN-CN, KP-US, KP-KR, IL-SA, RU-GB, CN-TW, TR-GR, IN-US

---

## 🚀 Next Steps (Phase 9 — Frontend)

```bash
cd frontend
npm install
npm run dev      # http://localhost:3000
```

