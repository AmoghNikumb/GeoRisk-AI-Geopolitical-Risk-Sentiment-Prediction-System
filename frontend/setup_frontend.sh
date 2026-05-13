#!/bin/bash
# GeoRisk AI — Frontend File Setup Script
# Run this from inside your frontend/ directory
# Usage: bash setup_frontend.sh

set -e
echo "🎨 Setting up GeoRisk AI frontend files..."

mkdir -p app/bilateral app/entities
mkdir -p components/{layout,dashboard,bilateral,briefs,entities}
mkdir -p lib store hooks

echo "✅ Directories created"


# app/globals.css
cat > "app/globals.css" << 'FEOF_GLOBALS_CSS'
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Syne:wght@400;600;700;800&display=swap');

@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --bg-primary: #080c14;
  --bg-secondary: #0d1421;
  --bg-card: #111827;
  --bg-card-hover: #1a2332;
  --border: #1e2d40;
  --border-bright: #2a3f5a;
  --text-primary: #e2e8f0;
  --text-secondary: #94a3b8;
  --text-muted: #4a5568;
  --accent-blue: #3b82f6;
  --accent-cyan: #06b6d4;
  --risk-low: #22c55e;
  --risk-moderate: #eab308;
  --risk-high: #f97316;
  --risk-critical: #ef4444;
}

* { box-sizing: border-box; }

html, body {
  background-color: var(--bg-primary);
  color: var(--text-primary);
  font-family: 'Syne', sans-serif;
  margin: 0;
  padding: 0;
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg-secondary); }
::-webkit-scrollbar-thumb { background: var(--border-bright); border-radius: 2px; }

/* Grid scanline overlay */
body::before {
  content: '';
  position: fixed;
  inset: 0;
  background-image: 
    linear-gradient(rgba(59,130,246,0.015) 1px, transparent 1px),
    linear-gradient(90deg, rgba(59,130,246,0.015) 1px, transparent 1px);
  background-size: 40px 40px;
  pointer-events: none;
  z-index: 0;
}

.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
}

.card:hover {
  border-color: var(--border-bright);
}

.mono { font-family: 'Space Mono', monospace; }

.risk-glow-low      { box-shadow: 0 0 20px rgba(34,197,94,0.15); }
.risk-glow-moderate { box-shadow: 0 0 20px rgba(234,179,8,0.15); }
.risk-glow-high     { box-shadow: 0 0 20px rgba(249,115,22,0.15); }
.risk-glow-critical { box-shadow: 0 0 20px rgba(239,68,68,0.2); animation: pulse-critical 2s infinite; }

@keyframes pulse-critical {
  0%, 100% { box-shadow: 0 0 20px rgba(239,68,68,0.2); }
  50%       { box-shadow: 0 0 40px rgba(239,68,68,0.4); }
}

.fade-in {
  animation: fadeIn 0.4s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

.score-bar {
  height: 4px;
  border-radius: 2px;
  background: var(--border);
  overflow: hidden;
}

.score-bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Recharts overrides */
.recharts-cartesian-grid-horizontal line,
.recharts-cartesian-grid-vertical line {
  stroke: #1e2d40 !important;
}
.recharts-tooltip-wrapper .recharts-default-tooltip {
  background: #111827 !important;
  border: 1px solid #1e2d40 !important;
  border-radius: 6px !important;
}

FEOF_GLOBALS_CSS

# app/layout.tsx
cat > "app/layout.tsx" << 'FEOF_LAYOUT_TSX'
import type { Metadata } from 'next'
import './globals.css'
import Navbar from '@/components/layout/Navbar'

export const metadata: Metadata = {
  title: 'GeoRisk AI — Geopolitical Intelligence',
  description: 'Real-time geopolitical risk prediction powered by AI',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen" style={{ background: 'var(--bg-primary)' }}>
        <div className="relative z-10">
          <Navbar />
          <main className="max-w-[1600px] mx-auto px-4 py-6">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}

FEOF_LAYOUT_TSX

# app/page.tsx
cat > "app/page.tsx" << 'FEOF_PAGE_TSX'
'use client'
import { useDashboard } from '@/hooks/useDashboard'
import AlertBanner from '@/components/layout/AlertBanner'
import TopRisksPanel from '@/components/dashboard/TopRisksPanel'
import MarketPanel from '@/components/dashboard/MarketPanel'
import GlobalFeed from '@/components/dashboard/GlobalFeed'
import { RefreshCw, Clock } from 'lucide-react'

export default function DashboardPage() {
  const { data, loading, error, lastUpdated, refetch } = useDashboard()

  if (loading) return (
    <div className="flex items-center justify-center h-96">
      <div className="text-center space-y-3">
        <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-sm mono" style={{ color: 'var(--text-muted)' }}>
          Connecting to GeoRisk AI...
        </p>
      </div>
    </div>
  )

  if (error) return (
    <div className="flex items-center justify-center h-96">
      <div className="card p-8 text-center max-w-md">
        <p className="text-red-400 font-bold mb-2">Backend Unreachable</p>
        <p className="text-sm mb-4" style={{ color: 'var(--text-muted)' }}>
          Make sure uvicorn is running on port 8000
        </p>
        <code className="text-xs mono block p-2 rounded mb-4"
          style={{ background: 'var(--bg-secondary)', color: 'var(--accent-cyan)' }}>
          uvicorn main:app --reload --port 8000
        </code>
        <button onClick={refetch}
          className="px-4 py-2 rounded text-sm font-medium transition-all"
          style={{ background: 'rgba(59,130,246,0.2)', color: '#60a5fa',
            border: '1px solid rgba(59,130,246,0.3)' }}>
          Retry
        </button>
      </div>
    </div>
  )

  return (
    <div className="space-y-4 fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight">
            Geopolitical Risk{' '}
            <span style={{ color: 'var(--accent-cyan)' }}>Intelligence</span>
          </h1>
          <p className="text-sm mt-0.5" style={{ color: 'var(--text-muted)' }}>
            Real-time sentiment fusion across {data?.risk_scores?.length ?? 0} country pairs
          </p>
        </div>
        <div className="flex items-center gap-3">
          {lastUpdated && (
            <div className="flex items-center gap-1.5 text-xs mono"
              style={{ color: 'var(--text-muted)' }}>
              <Clock size={11} />
              {lastUpdated.toLocaleTimeString()}
            </div>
          )}
          <button onClick={refetch}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-all"
            style={{ background: 'rgba(59,130,246,0.1)', color: '#60a5fa',
              border: '1px solid rgba(59,130,246,0.2)' }}>
            <RefreshCw size={12} />
            Refresh
          </button>
        </div>
      </div>

      {/* Alerts */}
      {data?.alerts && data.alerts.length > 0 && (
        <AlertBanner alerts={data.alerts} />
      )}

      {/* Stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Tracked Pairs', value: data?.risk_scores?.length ?? 0, unit: 'pairs' },
          {
            label: 'Critical/High',
            value: data?.risk_scores?.filter(r =>
              r.classification === 'CRITICAL' || r.classification === 'HIGH').length ?? 0,
            unit: 'active',
            alert: true
          },
          { label: 'Active Alerts', value: data?.alerts?.length ?? 0, unit: 'unread' },
          { label: 'VIX', value: data?.market?.vix?.toFixed(1) ?? '—', unit: 'fear idx' },
        ].map(stat => (
          <div key={stat.label} className="card p-4">
            <div className="text-xs mono mb-1" style={{ color: 'var(--text-muted)' }}>
              {stat.label}
            </div>
            <div className="text-2xl font-extrabold mono"
              style={{ color: stat.alert && Number(stat.value) > 0 ? '#ef4444' : 'var(--text-primary)' }}>
              {stat.value}
            </div>
            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>{stat.unit}</div>
          </div>
        ))}
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-1 space-y-4">
          <TopRisksPanel risks={data?.top_risks ?? []} />
          <MarketPanel market={data?.market ?? null} />
        </div>
        <div className="lg:col-span-2">
          <GlobalFeed scores={data?.risk_scores ?? []} />
        </div>
      </div>
    </div>
  )
}

FEOF_PAGE_TSX

# app/bilateral/page.tsx
cat > "app/bilateral/page.tsx" << 'FEOF_PAGE_TSX'
'use client'
import { useState, useEffect, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { useBilateral } from '@/hooks/useDashboard'
import { api } from '@/lib/api'
import RiskGauge from '@/components/bilateral/RiskGauge'
import SentimentTimeline from '@/components/bilateral/SentimentTimeline'
import BreakdownPanel from '@/components/bilateral/BreakdownPanel'
import IntelBriefPanel from '@/components/briefs/IntelBrief'
import PostFeed from '@/components/bilateral/PostFeed'
import { COUNTRY_NAMES, getCountryFlag, TRACKED_PAIRS } from '@/lib/utils'
import { RefreshCw, Zap } from 'lucide-react'

const COUNTRIES = Object.entries(COUNTRY_NAMES).map(([code, name]) => ({ code, name }))

function BilateralContent() {
  const params = useSearchParams()
  const router = useRouter()
  const [countryA, setCountryA] = useState(params.get('a') || 'US')
  const [countryB, setCountryB] = useState(params.get('b') || 'CN')
  const { data, loading, refetch } = useBilateral(countryA, countryB)

  const handleSwap = () => { setCountryA(countryB); setCountryB(countryA) }

  const handleRegenerate = async () => {
    await api.generateBrief(countryA, countryB)
    refetch()
  }

  return (
    <div className="space-y-4 fade-in">
      {/* Header + Country Selector */}
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-xl font-extrabold tracking-tight">
          Bilateral <span style={{ color: 'var(--accent-cyan)' }}>Analysis</span>
        </h1>

        <div className="flex items-center gap-2 ml-auto">
          {/* Quick pairs */}
          <div className="flex flex-wrap gap-1.5">
            {TRACKED_PAIRS.slice(0, 5).map(([a, b]) => (
              <button key={`${a}-${b}`}
                onClick={() => { setCountryA(a); setCountryB(b) }}
                className="text-xs px-2 py-1 rounded mono transition-all"
                style={{
                  background: countryA === a && countryB === b
                    ? 'rgba(6,182,212,0.15)' : 'var(--bg-secondary)',
                  color: countryA === a && countryB === b
                    ? 'var(--accent-cyan)' : 'var(--text-muted)',
                  border: `1px solid ${countryA === a && countryB === b
                    ? 'rgba(6,182,212,0.3)' : 'var(--border)'}`,
                }}>
                {getCountryFlag(a)}{getCountryFlag(b)} {a}-{b}
              </button>
            ))}
          </div>

          {/* Selectors */}
          <select value={countryA} onChange={e => setCountryA(e.target.value)}
            className="px-2 py-1.5 rounded text-sm"
            style={{ background: 'var(--bg-card)', color: 'var(--text-primary)',
              border: '1px solid var(--border)', outline: 'none' }}>
            {COUNTRIES.map(c => (
              <option key={c.code} value={c.code}>{getCountryFlag(c.code)} {c.code}</option>
            ))}
          </select>

          <button onClick={handleSwap}
            className="px-2 py-1.5 rounded text-sm"
            style={{ background: 'var(--bg-card)', color: 'var(--text-muted)',
              border: '1px solid var(--border)' }}>
            ⇄
          </button>

          <select value={countryB} onChange={e => setCountryB(e.target.value)}
            className="px-2 py-1.5 rounded text-sm"
            style={{ background: 'var(--bg-card)', color: 'var(--text-primary)',
              border: '1px solid var(--border)', outline: 'none' }}>
            {COUNTRIES.map(c => (
              <option key={c.code} value={c.code}>{getCountryFlag(c.code)} {c.code}</option>
            ))}
          </select>

          <button onClick={refetch}
            className="flex items-center gap-1 px-2 py-1.5 rounded text-xs"
            style={{ background: 'rgba(59,130,246,0.1)', color: '#60a5fa',
              border: '1px solid rgba(59,130,246,0.2)' }}>
            <RefreshCw size={11} />
          </button>
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center h-48">
          <div className="w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {!loading && data && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Left — Gauge + Breakdown */}
          <div className="space-y-4">
            <div className="card p-4">
              <div className="text-center mb-2">
                <span className="text-lg font-bold">
                  {getCountryFlag(countryA)} {countryA}
                  <span style={{ color: 'var(--text-muted)' }} className="mx-2 text-sm">vs</span>
                  {getCountryFlag(countryB)} {countryB}
                </span>
              </div>
              <RiskGauge
                score={data.risk_score.score}
                level={data.risk_score.classification} />
              {data.risk_score.score_change != null && (
                <p className="text-center text-xs mono mt-1"
                  style={{ color: data.risk_score.score_change > 0 ? '#ef4444' : '#22c55e' }}>
                  {data.risk_score.score_change > 0 ? '▲' : '▼'}{' '}
                  {Math.abs(data.risk_score.score_change).toFixed(1)} pts vs last score
                </p>
              )}
            </div>

            <div className="card p-4">
              <h3 className="text-xs font-bold uppercase tracking-widest mb-3"
                style={{ color: 'var(--text-muted)' }}>Risk Breakdown</h3>
              <BreakdownPanel breakdown={data.risk_score.breakdown} />
            </div>

            {/* Contributing factors */}
            {data.risk_score.contributing_factors?.length > 0 && (
              <div className="card p-4">
                <h3 className="text-xs font-bold uppercase tracking-widest mb-3"
                  style={{ color: 'var(--text-muted)' }}>Top Drivers</h3>
                <div className="space-y-2">
                  {data.risk_score.contributing_factors.map((f: any, i: number) => (
                    <div key={i} className="flex items-start gap-2">
                      <Zap size={11} className="mt-0.5 shrink-0"
                        style={{ color: 'var(--accent-cyan)' }} />
                      <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                        {f.factor}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Center — Timeline + Brief */}
          <div className="space-y-4">
            <div className="card p-4">
              <h3 className="text-xs font-bold uppercase tracking-widest mb-3"
                style={{ color: 'var(--text-muted)' }}>Sentiment Timeline</h3>
              <SentimentTimeline
                dataA={data.sentiment_timeline.country_a}
                dataB={data.sentiment_timeline.country_b}
                labelA={countryA}
                labelB={countryB} />
            </div>

            <div className="card p-4">
              <h3 className="text-xs font-bold uppercase tracking-widest mb-3"
                style={{ color: 'var(--text-muted)' }}>Intelligence Brief</h3>
              <IntelBriefPanel
                brief={data.intel_brief}
                onRegenerate={handleRegenerate} />
            </div>
          </div>

          {/* Right — Posts + GDELT */}
          <div className="space-y-4">
            <div className="card p-4">
              <h3 className="text-xs font-bold uppercase tracking-widest mb-3"
                style={{ color: 'var(--text-muted)' }}>Hostile Posts (72H)</h3>
              <div className="max-h-80 overflow-y-auto space-y-2">
                <PostFeed posts={data.top_posts?.slice(0, 10)} />
              </div>
            </div>

            <div className="card p-4">
              <h3 className="text-xs font-bold uppercase tracking-widest mb-3"
                style={{ color: 'var(--text-muted)' }}>GDELT Events</h3>
              {data.gdelt_events?.length === 0 ? (
                <p className="text-xs text-center py-4" style={{ color: 'var(--text-muted)' }}>
                  No high-conflict GDELT events detected
                </p>
              ) : (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {data.gdelt_events?.slice(0, 10).map((e: any, i: number) => (
                    <div key={i} className="p-2 rounded text-xs"
                      style={{ background: 'var(--bg-secondary)' }}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold" style={{ color: 'var(--text-primary)' }}>
                          {getCountryFlag(e.actor1 || '')} {e.actor1 || '?'}
                          {' → '}
                          {getCountryFlag(e.actor2 || '')} {e.actor2 || '?'}
                        </span>
                        <span className="mono" style={{ color: '#ef4444' }}>
                          GS: {e.goldstein_scale?.toFixed(1)}
                        </span>
                      </div>
                      <span style={{ color: 'var(--text-muted)' }}>
                        {e.geo || e.event_code} · {e.num_articles} articles
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default function BilateralPage() {
  return (
    <Suspense>
      <BilateralContent />
    </Suspense>
  )
}

FEOF_PAGE_TSX

# app/entities/page.tsx
cat > "app/entities/page.tsx" << 'FEOF_PAGE_TSX'
'use client'
import { useState } from 'react'
import { useEntities } from '@/hooks/useDashboard'
import PostFeed from '@/components/bilateral/PostFeed'
import { COUNTRY_NAMES, getCountryFlag, getSentimentColor, formatSentiment } from '@/lib/utils'
import { Shield, Twitter } from 'lucide-react'

const TRACKED_COUNTRIES = ['US', 'CN', 'RU', 'IN', 'PK', 'GB', 'DE', 'FR',
  'JP', 'KR', 'IR', 'IL', 'SA', 'TR', 'UA']

export default function EntitiesPage() {
  const [selected, setSelected] = useState('US')
  const { data, loading } = useEntities(selected)

  return (
    <div className="space-y-4 fade-in">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-extrabold tracking-tight">
          Political <span style={{ color: 'var(--accent-cyan)' }}>Entities</span>
        </h1>
      </div>

      {/* Country tabs */}
      <div className="flex flex-wrap gap-2">
        {TRACKED_COUNTRIES.map(code => (
          <button key={code}
            onClick={() => setSelected(code)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm transition-all"
            style={{
              background: selected === code ? 'rgba(6,182,212,0.12)' : 'var(--bg-card)',
              color: selected === code ? 'var(--accent-cyan)' : 'var(--text-secondary)',
              border: `1px solid ${selected === code ? 'rgba(6,182,212,0.3)' : 'var(--border)'}`,
            }}>
            <span>{getCountryFlag(code)}</span>
            <span className="font-medium">{code}</span>
          </button>
        ))}
      </div>

      {loading && (
        <div className="flex items-center justify-center h-48">
          <div className="w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {!loading && data && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Politicians */}
          <div className="lg:col-span-1 space-y-3">
            <div className="card p-4">
              <h3 className="text-xs font-bold uppercase tracking-widest mb-3"
                style={{ color: 'var(--text-muted)' }}>
                {getCountryFlag(selected)} Tracked Politicians
              </h3>
              {data.politicians?.length === 0 ? (
                <p className="text-xs text-center py-4" style={{ color: 'var(--text-muted)' }}>
                  No politicians tracked for {selected}
                </p>
              ) : (
                <div className="space-y-2">
                  {data.politicians?.map((pol: any) => {
                    const sentColor = getSentimentColor(pol.avg_sentiment_72h)
                    return (
                      <div key={pol.id} className="p-3 rounded-lg"
                        style={{ background: 'var(--bg-secondary)' }}>
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-1.5 mb-0.5">
                              <Twitter size={11} style={{ color: '#1da1f2' }} />
                              <span className="text-xs font-bold"
                                style={{ color: 'var(--text-primary)' }}>
                                {pol.name}
                              </span>
                            </div>
                            <p className="text-xs truncate" style={{ color: 'var(--text-muted)' }}>
                              {pol.title}
                            </p>
                            <p className="text-xs mono mt-0.5" style={{ color: '#60a5fa' }}>
                              {pol.twitter_handle}
                            </p>
                          </div>
                          <div className="text-right shrink-0">
                            <p className="text-sm font-bold mono" style={{ color: sentColor }}>
                              {formatSentiment(pol.avg_sentiment_72h)}
                            </p>
                            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                              72h avg
                            </p>
                          </div>
                        </div>
                        {/* Influence bar */}
                        <div className="mt-2">
                          <div className="flex items-center justify-between mb-0.5">
                            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                              Influence
                            </span>
                            <span className="text-xs mono" style={{ color: 'var(--text-muted)' }}>
                              {pol.influence_weight}
                            </span>
                          </div>
                          <div className="score-bar">
                            <div className="score-bar-fill"
                              style={{ width: `${pol.influence_weight * 100}%`,
                                background: 'var(--accent-cyan)' }} />
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Inflammatory Posts */}
          <div className="lg:col-span-2">
            <div className="card p-4">
              <h3 className="text-xs font-bold uppercase tracking-widest mb-3"
                style={{ color: 'var(--text-muted)' }}>
                Most Hostile Posts — {getCountryFlag(selected)} {COUNTRY_NAMES[selected]} (72H)
              </h3>
              <div className="max-h-[600px] overflow-y-auto">
                <PostFeed posts={data.inflammatory_posts} />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

FEOF_PAGE_TSX

# components/bilateral/BreakdownPanel.tsx
cat > "components/bilateral/BreakdownPanel.tsx" << 'FEOF_BREAKDOWNPANEL_TSX'
'use client'
import { RiskBreakdown } from '@/lib/types'

const FACTORS = [
  { key: 'negative_sentiment',    label: 'Negative Sentiment',     weight: '25%' },
  { key: 'sentiment_deterioration', label: 'Deterioration Rate',   weight: '20%' },
  { key: 'politician_hostility',  label: 'Politician Hostility',    weight: '15%' },
  { key: 'gdelt_conflict',        label: 'GDELT Conflict Events',   weight: '20%' },
  { key: 'vix_spike',             label: 'VIX Spike',               weight: '10%' },
  { key: 'market_stress',         label: 'Market Stress',           weight: '10%' },
]

export default function BreakdownPanel({ breakdown }: { breakdown: RiskBreakdown }) {
  return (
    <div className="space-y-3">
      {FACTORS.map(f => {
        const val = breakdown[f.key as keyof RiskBreakdown] ?? 0
        const pct = Math.round(val * 100)
        const color = pct > 70 ? '#ef4444' : pct > 40 ? '#f97316' : pct > 20 ? '#eab308' : '#22c55e'

        return (
          <div key={f.key}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                {f.label}
              </span>
              <div className="flex items-center gap-2">
                <span className="text-xs mono" style={{ color: 'var(--text-muted)' }}>
                  w={f.weight}
                </span>
                <span className="text-xs mono font-bold" style={{ color }}>
                  {pct}%
                </span>
              </div>
            </div>
            <div className="score-bar">
              <div className="score-bar-fill" style={{ width: `${pct}%`, background: color }} />
            </div>
          </div>
        )
      })}
    </div>
  )
}

FEOF_BREAKDOWNPANEL_TSX

# components/bilateral/PostFeed.tsx
cat > "components/bilateral/PostFeed.tsx" << 'FEOF_POSTFEED_TSX'
'use client'
import { Post } from '@/lib/types'
import { getSentimentColor, timeAgo } from '@/lib/utils'
import { Twitter, MessageSquare, Shield } from 'lucide-react'

export default function PostFeed({ posts, title = 'Recent Posts' }:
  { posts: Post[]; title?: string }) {

  if (!posts?.length) return (
    <div className="text-center py-8 text-sm" style={{ color: 'var(--text-muted)' }}>
      Posts will appear after first collection run
    </div>
  )

  return (
    <div className="space-y-2">
      {posts.map((p, i) => {
        const score = p.sentiment_score ?? 0
        const color = getSentimentColor(p.sentiment_score)
        const Icon = p.source === 'twitter' ? Twitter : MessageSquare

        return (
          <div key={i} className="p-3 rounded-lg"
            style={{ background: 'var(--bg-secondary)', borderLeft: `3px solid ${color}` }}>
            <div className="flex items-center gap-2 mb-1.5">
              <Icon size={11} style={{ color: p.source === 'twitter' ? '#1da1f2' : '#ff4500' }} />
              <span className="text-xs font-bold" style={{ color: 'var(--text-primary)' }}>
                {p.author}
              </span>
              {p.is_politician && (
                <Shield size={10} className="text-yellow-400" />
              )}
              <span className="text-xs ml-auto mono" style={{ color }}>
                {score > 0 ? '+' : ''}{score.toFixed(2)}
              </span>
              <span className="text-xs mono" style={{ color: 'var(--text-muted)' }}>
                {timeAgo(p.posted_at)}
              </span>
            </div>
            <p className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
              {p.text?.slice(0, 240)}{(p.text?.length ?? 0) > 240 ? '...' : ''}
            </p>
          </div>
        )
      })}
    </div>
  )
}

FEOF_POSTFEED_TSX

# components/bilateral/RiskGauge.tsx
cat > "components/bilateral/RiskGauge.tsx" << 'FEOF_RISKGAUGE_TSX'
'use client'
import { getRiskColor, getRiskBg } from '@/lib/utils'
import { RiskLevel } from '@/lib/types'

export default function RiskGauge({ score, level }: { score: number | null; level: RiskLevel }) {
  const s = score ?? 0
  const color = getRiskColor(level)
  const circumference = 2 * Math.PI * 54
  const offset = circumference - (s / 100) * circumference

  return (
    <div className="flex flex-col items-center justify-center py-6">
      <div className="relative w-36 h-36">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
          <circle cx="60" cy="60" r="54" fill="none"
            stroke="var(--border)" strokeWidth="8" />
          <circle cx="60" cy="60" r="54" fill="none"
            stroke={color} strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ transition: 'stroke-dashoffset 1s cubic-bezier(0.4,0,0.2,1)', filter: `drop-shadow(0 0 8px ${color}66)` }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-extrabold mono" style={{ color }}>
            {s.toFixed(0)}
          </span>
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>/100</span>
        </div>
      </div>
      <span className={`mt-3 text-xs px-3 py-1 rounded-full border mono font-bold ${getRiskBg(level)}`}>
        {level}
      </span>
    </div>
  )
}

FEOF_RISKGAUGE_TSX

# components/bilateral/SentimentTimeline.tsx
cat > "components/bilateral/SentimentTimeline.tsx" << 'FEOF_SENTIMENTTIMELINE_TSX'
'use client'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { SentimentPoint } from '@/lib/types'
import { format } from 'date-fns'

interface Props {
  dataA: SentimentPoint[]
  dataB: SentimentPoint[]
  labelA: string
  labelB: string
}

export default function SentimentTimeline({ dataA, dataB, labelA, labelB }: Props) {
  // Merge by time
  const merged: any[] = []
  const mapA = new Map(dataA.map(d => [d.time, d]))
  const mapB = new Map(dataB.map(d => [d.time, d]))
  const allTimes = Array.from(new Set([...dataA, ...dataB].map(d => d.time))).sort()

  for (const t of allTimes) {
    merged.push({
      time: t,
      a: mapA.get(t)?.avg ?? null,
      b: mapB.get(t)?.avg ?? null,
    })
  }

  if (!merged.length) return (
    <div className="flex items-center justify-center h-48"
      style={{ color: 'var(--text-muted)' }} className="text-sm text-center">
      Sentiment data will appear after first scoring run
    </div>
  )

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null
    return (
      <div className="card p-2 text-xs space-y-1" style={{ minWidth: 120 }}>
        <p className="mono" style={{ color: 'var(--text-muted)' }}>
          {label ? format(new Date(label), 'MMM d, HH:mm') : ''}
        </p>
        {payload.map((p: any) => (
          <p key={p.dataKey} style={{ color: p.color }}>
            {p.dataKey === 'a' ? labelA : labelB}: {p.value?.toFixed(3) ?? 'N/A'}
          </p>
        ))}
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center gap-4 mb-3">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-0.5 rounded" style={{ background: '#3b82f6' }} />
          <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{labelA}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-0.5 rounded" style={{ background: '#f97316' }} />
          <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{labelB}</span>
        </div>
        <span className="text-xs ml-auto mono" style={{ color: 'var(--text-muted)' }}>
          72H SENTIMENT
        </span>
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={merged} margin={{ top: 5, right: 5, bottom: 5, left: -20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey="time" tickFormatter={t => format(new Date(t), 'HH:mm')}
            tick={{ fontSize: 10, fill: 'var(--text-muted)' }} />
          <YAxis domain={[-1, 1]} tick={{ fontSize: 10, fill: 'var(--text-muted)' }} />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine y={0} stroke="var(--border-bright)" strokeDasharray="4 4" />
          <Line type="monotone" dataKey="a" stroke="#3b82f6" strokeWidth={2}
            dot={false} connectNulls />
          <Line type="monotone" dataKey="b" stroke="#f97316" strokeWidth={2}
            dot={false} connectNulls />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

FEOF_SENTIMENTTIMELINE_TSX

# components/briefs/IntelBrief.tsx
cat > "components/briefs/IntelBrief.tsx" << 'FEOF_INTELBRIEF_TSX'
'use client'
import { IntelBrief } from '@/lib/types'
import { getRiskBg } from '@/lib/utils'
import { Brain, Clock, RefreshCw } from 'lucide-react'

export default function IntelBriefPanel({ brief, onRegenerate }:
  { brief: IntelBrief; onRegenerate?: () => void }) {

  if (brief.is_generating && !brief.headline) {
    return (
      <div className="flex flex-col items-center justify-center py-10 space-y-3">
        <Brain size={24} style={{ color: 'var(--accent-cyan)' }} className="animate-pulse" />
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
          Generating intelligence brief...
        </p>
      </div>
    )
  }

  if (!brief.headline) {
    return (
      <div className="flex flex-col items-center justify-center py-10 space-y-3">
        <Brain size={24} style={{ color: 'var(--text-muted)' }} />
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
          No brief generated yet
        </p>
        {onRegenerate && (
          <button onClick={onRegenerate}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs"
            style={{ background: 'rgba(59,130,246,0.1)', color: '#60a5fa',
              border: '1px solid rgba(59,130,246,0.2)' }}>
            <RefreshCw size={11} /> Generate Brief
          </button>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <h3 className="font-bold text-base leading-snug" style={{ color: 'var(--text-primary)' }}>
          {brief.headline}
        </h3>
        {brief.risk_level && (
          <span className={`text-xs px-2 py-1 rounded border mono shrink-0 ${getRiskBg(brief.risk_level)}`}>
            {brief.risk_level}
          </span>
        )}
      </div>

      {/* Summary */}
      {brief.summary && (
        <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
          {brief.summary}
        </p>
      )}

      {/* Key Drivers */}
      {brief.key_drivers?.length > 0 && (
        <div>
          <p className="text-xs font-bold uppercase tracking-widest mb-2"
            style={{ color: 'var(--text-muted)' }}>Key Drivers</p>
          <ul className="space-y-1.5">
            {brief.key_drivers.map((d, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <span style={{ color: 'var(--accent-cyan)' }} className="mt-0.5 shrink-0">›</span>
                <span style={{ color: 'var(--text-secondary)' }}>{d}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Market Implications */}
      {brief.market_implications && (
        <div className="p-3 rounded-lg" style={{ background: 'rgba(59,130,246,0.06)',
          border: '1px solid rgba(59,130,246,0.15)' }}>
          <p className="text-xs font-bold uppercase tracking-widest mb-1.5"
            style={{ color: '#60a5fa' }}>Market Implications</p>
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
            {brief.market_implications}
          </p>
        </div>
      )}

      {/* 72hr Outlook */}
      {brief.outlook_72hr && (
        <div className="p-3 rounded-lg" style={{ background: 'rgba(234,179,8,0.06)',
          border: '1px solid rgba(234,179,8,0.15)' }}>
          <p className="text-xs font-bold uppercase tracking-widest mb-1.5"
            style={{ color: '#eab308' }}>72H Outlook</p>
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
            {brief.outlook_72hr}
          </p>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-2"
        style={{ borderTop: '1px solid var(--border)' }}>
        <div className="flex items-center gap-1.5 text-xs mono" style={{ color: 'var(--text-muted)' }}>
          <Clock size={11} />
          {brief.generated_at ? new Date(brief.generated_at).toLocaleString() : 'Unknown'}
        </div>
        <div className="flex items-center gap-2">
          {brief.confidence != null && (
            <span className="text-xs mono" style={{ color: 'var(--text-muted)' }}>
              Confidence: {(brief.confidence * 100).toFixed(0)}%
            </span>
          )}
          {onRegenerate && (
            <button onClick={onRegenerate}
              className="flex items-center gap-1 text-xs px-2 py-1 rounded"
              style={{ color: 'var(--text-muted)', border: '1px solid var(--border)' }}>
              <RefreshCw size={10} /> Regenerate
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

FEOF_INTELBRIEF_TSX

# components/dashboard/GlobalFeed.tsx
cat > "components/dashboard/GlobalFeed.tsx" << 'FEOF_GLOBALFEED_TSX'
'use client'
import { RiskScore } from '@/lib/types'
import { getRiskColor, getRiskBg, getCountryFlag, formatScore } from '@/lib/utils'
import Link from 'next/link'

export default function GlobalFeed({ scores }: { scores: RiskScore[] }) {
  const sorted = [...scores].sort((a, b) => b.score - a.score)

  return (
    <div className="card p-4 fade-in">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-bold text-sm tracking-widest uppercase"
          style={{ color: 'var(--text-secondary)' }}>All Tracked Pairs</h2>
        <span className="text-xs mono" style={{ color: 'var(--text-muted)' }}>
          {scores.length} PAIRS
        </span>
      </div>

      {sorted.length === 0 ? (
        <div className="text-center py-8 text-sm" style={{ color: 'var(--text-muted)' }}>
          Risk scores will appear after first pipeline run (~1 hour)
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {sorted.map(r => (
            <Link key={r.pair_key} href={`/bilateral?a=${r.country_a}&b=${r.country_b}`}
              className="no-underline block">
              <div className="flex items-center justify-between p-2.5 rounded-lg transition-all"
                style={{ background: 'var(--bg-secondary)' }}
                onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-card-hover)')}
                onMouseLeave={e => (e.currentTarget.style.background = 'var(--bg-secondary)')}>
                <div className="flex items-center gap-2">
                  <span>{getCountryFlag(r.country_a)}</span>
                  <span className="text-xs font-bold" style={{ color: 'var(--text-primary)' }}>
                    {r.country_a}
                  </span>
                  <span className="text-xs" style={{ color: 'var(--text-muted)' }}>↔</span>
                  <span>{getCountryFlag(r.country_b)}</span>
                  <span className="text-xs font-bold" style={{ color: 'var(--text-primary)' }}>
                    {r.country_b}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="mono text-sm font-bold"
                    style={{ color: getRiskColor(r.classification) }}>
                    {formatScore(r.score)}
                  </span>
                  <span className={`text-xs px-1.5 py-0.5 rounded border mono ${getRiskBg(r.classification)}`}>
                    {r.classification}
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

FEOF_GLOBALFEED_TSX

# components/dashboard/MarketPanel.tsx
cat > "components/dashboard/MarketPanel.tsx" << 'FEOF_MARKETPANEL_TSX'
'use client'
import { MarketData } from '@/lib/types'
import { TrendingUp, TrendingDown } from 'lucide-react'

function Ticker({ label, value, change, prefix = '' }:
  { label: string; value: number | null; change?: number | null; prefix?: string }) {
  const isUp = (change ?? 0) >= 0
  return (
    <div className="p-3 rounded-lg" style={{ background: 'var(--bg-secondary)' }}>
      <div className="text-xs mono mb-1" style={{ color: 'var(--text-muted)' }}>{label}</div>
      <div className="font-bold text-lg mono" style={{ color: 'var(--text-primary)' }}>
        {value != null ? `${prefix}${value.toFixed(2)}` : '—'}
      </div>
      {change != null && (
        <div className="flex items-center gap-1 mt-0.5">
          {isUp ? <TrendingUp size={10} className="text-red-400" />
                : <TrendingDown size={10} className="text-emerald-400" />}
          <span className={`text-xs mono ${isUp ? 'text-red-400' : 'text-emerald-400'}`}>
            {isUp ? '+' : ''}{change.toFixed(2)}%
          </span>
        </div>
      )}
    </div>
  )
}

export default function MarketPanel({ market }: { market: MarketData | null }) {
  const stress = market?.market_stress_score ?? 0
  const stressColor = stress > 0.7 ? '#ef4444' : stress > 0.4 ? '#f97316' : '#22c55e'

  return (
    <div className="card p-4 fade-in">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-bold text-sm tracking-widest uppercase"
          style={{ color: 'var(--text-secondary)' }}>Market Signals</h2>
        {market && (
          <div className="flex items-center gap-2">
            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>Stress</span>
            <div className="w-16 h-1.5 rounded-full" style={{ background: 'var(--border)' }}>
              <div className="h-full rounded-full transition-all"
                style={{ width: `${stress * 100}%`, background: stressColor }} />
            </div>
            <span className="text-xs mono" style={{ color: stressColor }}>
              {(stress * 100).toFixed(0)}%
            </span>
          </div>
        )}
      </div>

      {!market ? (
        <div className="text-center py-6 text-sm" style={{ color: 'var(--text-muted)' }}>
          Awaiting first market snapshot...
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-2">
          <Ticker label="VIX (Fear)" value={market.vix} />
          <Ticker label="S&P 500" value={market.sp500} change={market.sp500_change_pct} />
          <Ticker label="WTI Crude" value={market.crude_oil} prefix="$" />
          <Ticker label="Gold" value={market.gold} prefix="$" />
        </div>
      )}
    </div>
  )
}

FEOF_MARKETPANEL_TSX

# components/dashboard/TopRisksPanel.tsx
cat > "components/dashboard/TopRisksPanel.tsx" << 'FEOF_TOPRISKSPANEL_TSX'
'use client'
import { RiskScore } from '@/lib/types'
import { getRiskColor, getRiskBg, getCountryFlag, COUNTRY_NAMES, formatScore } from '@/lib/utils'
import Link from 'next/link'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

export default function TopRisksPanel({ risks }: { risks: RiskScore[] }) {
  return (
    <div className="card p-4 fade-in">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-bold text-sm tracking-widest uppercase"
          style={{ color: 'var(--text-secondary)' }}>Top Risk Pairs</h2>
        <span className="text-xs mono" style={{ color: 'var(--text-muted)' }}>
          72H WINDOW
        </span>
      </div>

      <div className="space-y-2">
        {risks.length === 0 && (
          <div className="text-center py-8 text-sm" style={{ color: 'var(--text-muted)' }}>
            Collecting data... Check back in 30 mins
          </div>
        )}
        {risks.map((r, i) => {
          const change = r.score_change ?? 0
          const TrendIcon = change > 2 ? TrendingUp : change < -2 ? TrendingDown : Minus
          const trendColor = change > 2 ? '#ef4444' : change < -2 ? '#22c55e' : '#6b7280'

          return (
            <Link key={r.pair_key} href={`/bilateral?a=${r.country_a}&b=${r.country_b}`}
              className="block no-underline">
              <div className="flex items-center gap-3 p-3 rounded-lg transition-all cursor-pointer"
                style={{ background: 'var(--bg-secondary)' }}
                onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-card-hover)')}
                onMouseLeave={e => (e.currentTarget.style.background = 'var(--bg-secondary)')}>

                {/* Rank */}
                <span className="text-xs mono w-4 text-center" style={{ color: 'var(--text-muted)' }}>
                  {i + 1}
                </span>

                {/* Flags + Countries */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 mb-1">
                    <span className="text-base">{getCountryFlag(r.country_a)}</span>
                    <span className="text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>
                      {r.country_a}
                    </span>
                    <span style={{ color: 'var(--text-muted)' }} className="text-xs">vs</span>
                    <span className="text-base">{getCountryFlag(r.country_b)}</span>
                    <span className="text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>
                      {r.country_b}
                    </span>
                  </div>
                  {/* Score bar */}
                  <div className="score-bar">
                    <div className="score-bar-fill"
                      style={{ width: `${r.score}%`, background: getRiskColor(r.classification) }} />
                  </div>
                </div>

                {/* Score + Badge */}
                <div className="flex items-center gap-2">
                  <TrendIcon size={12} style={{ color: trendColor }} />
                  <span className="mono font-bold text-sm"
                    style={{ color: getRiskColor(r.classification) }}>
                    {formatScore(r.score)}
                  </span>
                  <span className={`text-xs px-1.5 py-0.5 rounded border mono ${getRiskBg(r.classification)}`}>
                    {r.classification}
                  </span>
                </div>
              </div>
            </Link>
          )
        })}
      </div>
    </div>
  )
}

FEOF_TOPRISKSPANEL_TSX

# components/layout/AlertBanner.tsx
cat > "components/layout/AlertBanner.tsx" << 'FEOF_ALERTBANNER_TSX'
'use client'
import { AlertTriangle, X } from 'lucide-react'
import { Alert } from '@/lib/types'
import { timeAgo } from '@/lib/utils'
import { useState } from 'react'

export default function AlertBanner({ alerts }: { alerts: Alert[] }) {
  const [dismissed, setDismissed] = useState<number[]>([])
  const visible = alerts.filter(a => !dismissed.includes(a.id)).slice(0, 3)
  if (!visible.length) return null

  return (
    <div className="space-y-2 mb-4 fade-in">
      {visible.map(alert => (
        <div key={alert.id}
          className="flex items-center justify-between px-4 py-2.5 rounded-lg"
          style={{
            background: alert.severity === 'CRITICAL'
              ? 'rgba(239,68,68,0.08)' : 'rgba(249,115,22,0.08)',
            border: `1px solid ${alert.severity === 'CRITICAL'
              ? 'rgba(239,68,68,0.3)' : 'rgba(249,115,22,0.3)'}`,
          }}>
          <div className="flex items-center gap-2">
            <AlertTriangle size={14}
              style={{ color: alert.severity === 'CRITICAL' ? '#ef4444' : '#f97316' }} />
            <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
              {alert.title}
            </span>
            <span className="text-xs mono" style={{ color: 'var(--text-muted)' }}>
              {timeAgo(alert.triggered_at)}
            </span>
          </div>
          <button onClick={() => setDismissed(d => [...d, alert.id])}
            style={{ color: 'var(--text-muted)' }} className="hover:text-white transition-colors">
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  )
}

FEOF_ALERTBANNER_TSX

# components/layout/Navbar.tsx
cat > "components/layout/Navbar.tsx" << 'FEOF_NAVBAR_TSX'
'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Globe, Activity, Users, AlertTriangle } from 'lucide-react'

const links = [
  { href: '/',          label: 'Dashboard',  icon: Globe },
  { href: '/bilateral', label: 'Bilateral',  icon: Activity },
  { href: '/entities',  label: 'Entities',   icon: Users },
]

export default function Navbar() {
  const path = usePathname()

  return (
    <nav style={{ background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border)' }}
      className="sticky top-0 z-50">
      <div className="max-w-[1600px] mx-auto px-4 h-14 flex items-center justify-between">

        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 no-underline">
          <div className="w-7 h-7 rounded flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, #3b82f6, #06b6d4)' }}>
            <Globe size={14} className="text-white" />
          </div>
          <span className="font-bold text-base tracking-tight" style={{ color: 'var(--text-primary)' }}>
            GeoRisk<span style={{ color: 'var(--accent-cyan)' }}>AI</span>
          </span>
          <span className="text-xs mono px-1.5 py-0.5 rounded"
            style={{ background: 'rgba(59,130,246,0.1)', color: '#60a5fa', border: '1px solid rgba(59,130,246,0.2)' }}>
            LIVE
          </span>
        </Link>

        {/* Nav Links */}
        <div className="flex items-center gap-1">
          {links.map(({ href, label, icon: Icon }) => {
            const active = path === href
            return (
              <Link key={href} href={href}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm font-medium transition-all no-underline"
                style={{
                  color: active ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                  background: active ? 'rgba(6,182,212,0.1)' : 'transparent',
                  border: active ? '1px solid rgba(6,182,212,0.2)' : '1px solid transparent',
                }}>
                <Icon size={14} />
                {label}
              </Link>
            )
          })}
        </div>

        {/* Status */}
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs mono" style={{ color: 'var(--text-muted)' }}>
            API CONNECTED
          </span>
        </div>
      </div>
    </nav>
  )
}

FEOF_NAVBAR_TSX

# hooks/useDashboard.ts
cat > "hooks/useDashboard.ts" << 'FEOF_USEDASHBOARD_TS'
import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { DashboardData } from '@/lib/types'

export function useDashboard(pollInterval = 300000) {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const fetch = async () => {
    try {
      const d = await api.dashboard()
      setData(d)
      setLastUpdated(new Date())
      setError(null)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetch()
    const interval = setInterval(fetch, pollInterval)
    return () => clearInterval(interval)
  }, [])

  return { data, loading, error, lastUpdated, refetch: fetch }
}

export function useBilateral(countryA: string, countryB: string) {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetch = async () => {
    setLoading(true)
    try {
      const d = await api.bilateral(countryA, countryB)
      setData(d)
      setError(null)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetch()
    const interval = setInterval(fetch, 300000)
    return () => clearInterval(interval)
  }, [countryA, countryB])

  return { data, loading, error, refetch: fetch }
}

export function useEntities(country: string) {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    api.entities(country)
      .then(d => { setData(d); setError(null) })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [country])

  return { data, loading, error }
}

FEOF_USEDASHBOARD_TS

# lib/api.ts
cat > "lib/api.ts" << 'FEOF_API_TS'
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function fetchAPI<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`)
  return res.json()
}

export const api = {
  dashboard: () => fetchAPI<any>('/api/dashboard'),
  bilateral: (a: string, b: string) => fetchAPI<any>(`/api/bilateral?a=${a}&b=${b}`),
  entities: (country: string) => fetchAPI<any>(`/api/entities?country=${country}`),
  alerts: () => fetchAPI<any>('/api/alerts'),
  generateBrief: (a: string, b: string) =>
    fetch(`${API_BASE}/api/briefs/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ country_a: a, country_b: b }),
    }).then(r => r.json()),
  markAlertRead: (id: number) =>
    fetch(`${API_BASE}/api/alerts/${id}/read`, { method: 'PATCH' }),
}

FEOF_API_TS

# lib/types.ts
cat > "lib/types.ts" << 'FEOF_TYPES_TS'
export type RiskLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL' | 'UNKNOWN'

export interface RiskScore {
  pair_key: string
  country_a: string
  country_b: string
  score: number
  classification: RiskLevel
  score_change: number | null
  computed_at: string
  headline_factors?: string[]
}

export interface MarketData {
  vix: number | null
  sp500: number | null
  sp500_change_pct: number | null
  crude_oil: number | null
  gold: number | null
  market_stress_score: number | null
  captured_at: string | null
}

export interface Alert {
  id: number
  pair_key: string
  title: string
  severity: 'INFO' | 'WARNING' | 'CRITICAL'
  triggered_at: string
}

export interface DashboardData {
  risk_scores: RiskScore[]
  top_risks: RiskScore[]
  market: MarketData | null
  alerts: Alert[]
  generated_at: string
}

export interface SentimentPoint {
  time: string
  avg: number | null
  politician: number | null
  public: number | null
  count: number
}

export interface RiskBreakdown {
  negative_sentiment: number | null
  sentiment_deterioration: number | null
  politician_hostility: number | null
  gdelt_conflict: number | null
  vix_spike: number | null
  market_stress: number | null
}

export interface IntelBrief {
  headline: string | null
  risk_level: RiskLevel | null
  summary: string | null
  key_drivers: string[]
  market_implications: string | null
  outlook_72hr: string | null
  confidence: number | null
  generated_at: string | null
  is_generating: boolean
}

export interface Post {
  source: string
  author: string
  text: string
  sentiment_score: number | null
  sentiment_label: string | null
  posted_at: string | null
  is_politician: boolean
}

export interface GdeltEvent {
  actor1: string
  actor2: string
  event_code: string
  goldstein_scale: number
  num_articles: number
  event_date: string | null
  geo: string | null
}

export interface BilateralData {
  pair_key: string
  country_a: string
  country_b: string
  risk_score: {
    score: number | null
    classification: RiskLevel
    score_change: number | null
    contributing_factors: Array<{ factor: string; impact: number; category: string }>
    breakdown: RiskBreakdown
    computed_at: string | null
  }
  sentiment_timeline: {
    country_a: SentimentPoint[]
    country_b: SentimentPoint[]
  }
  top_posts: Post[]
  intel_brief: IntelBrief
  gdelt_events: GdeltEvent[]
}

export interface Politician {
  id: number
  name: string
  twitter_handle: string
  title: string
  influence_weight: number
  avg_sentiment_72h: number | null
  recent_posts: Post[]
}

export interface EntitiesData {
  country: string
  politicians: Politician[]
  inflammatory_posts: Post[]
}

FEOF_TYPES_TS

# lib/utils.ts
cat > "lib/utils.ts" << 'FEOF_UTILS_TS'
import { RiskLevel } from './types'

export function getRiskColor(level: RiskLevel): string {
  switch (level) {
    case 'LOW':      return '#22c55e'
    case 'MODERATE': return '#eab308'
    case 'HIGH':     return '#f97316'
    case 'CRITICAL': return '#ef4444'
    default:         return '#6b7280'
  }
}

export function getRiskBg(level: RiskLevel): string {
  switch (level) {
    case 'LOW':      return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
    case 'MODERATE': return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30'
    case 'HIGH':     return 'bg-orange-500/10 text-orange-400 border-orange-500/30'
    case 'CRITICAL': return 'bg-red-500/10 text-red-400 border-red-500/30'
    default:         return 'bg-gray-500/10 text-gray-400 border-gray-500/30'
  }
}

export function getSentimentColor(score: number | null): string {
  if (score === null) return '#6b7280'
  if (score < -0.5) return '#ef4444'
  if (score < -0.2) return '#f97316'
  if (score < 0.2)  return '#eab308'
  if (score < 0.5)  return '#84cc16'
  return '#22c55e'
}

export function formatScore(score: number | null): string {
  if (score === null) return 'N/A'
  return score.toFixed(1)
}

export function formatSentiment(score: number | null): string {
  if (score === null) return 'N/A'
  return (score > 0 ? '+' : '') + score.toFixed(2)
}

export function timeAgo(dateStr: string | null): string {
  if (!dateStr) return 'Unknown'
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

export function getCountryFlag(code: string): string {
  return code.toUpperCase().replace(/./g, c =>
    String.fromCodePoint(127397 + c.charCodeAt(0))
  )
}

export const COUNTRY_NAMES: Record<string, string> = {
  US: 'United States', CN: 'China', RU: 'Russia', IN: 'India',
  PK: 'Pakistan', GB: 'United Kingdom', DE: 'Germany', FR: 'France',
  JP: 'Japan', KR: 'South Korea', KP: 'North Korea', IR: 'Iran',
  IL: 'Israel', SA: 'Saudi Arabia', TR: 'Turkey', UA: 'Ukraine',
  BR: 'Brazil', AU: 'Australia', CA: 'Canada', MX: 'Mexico',
}

export const TRACKED_PAIRS = [
  ['CN', 'US'], ['IN', 'PK'], ['RU', 'UA'], ['IL', 'IR'],
  ['IN', 'CN'], ['KP', 'US'], ['KP', 'KR'], ['IL', 'SA'],
  ['RU', 'GB'], ['IN', 'US'],
]

FEOF_UTILS_TS

# store/useStore.ts
cat > "store/useStore.ts" << 'FEOF_USESTORE_TS'
import { create } from 'zustand'
import { DashboardData, BilateralData } from '@/lib/types'

interface GeoRiskStore {
  dashboard: DashboardData | null
  setDashboard: (d: DashboardData) => void
  selectedPair: [string, string]
  setSelectedPair: (pair: [string, string]) => void
  bilateral: BilateralData | null
  setBilateral: (d: BilateralData) => void
  unreadAlerts: number
  setUnreadAlerts: (n: number) => void
}

export const useStore = create<GeoRiskStore>((set) => ({
  dashboard: null,
  setDashboard: (d) => set({ dashboard: d }),
  selectedPair: ['US', 'CN'],
  setSelectedPair: (pair) => set({ selectedPair: pair }),
  bilateral: null,
  setBilateral: (d) => set({ bilateral: d }),
  unreadAlerts: 0,
  setUnreadAlerts: (n) => set({ unreadAlerts: n }),
}))

FEOF_USESTORE_TS

echo ""
echo "✅ All frontend files written!"
echo ""
echo "Now run: npm run dev"
echo "Then open: http://localhost:3000"
