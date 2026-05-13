'use client'
import { useState, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { useBilateral } from '@/hooks/useDashboard'
import { api } from '@/lib/api'
import RiskGauge from '@/components/bilateral/RiskGauge'
import SentimentTimeline from '@/components/bilateral/SentimentTimeline'
import BreakdownPanel from '@/components/bilateral/BreakdownPanel'
import IntelBriefPanel from '@/components/briefs/IntelBrief'
import PostFeed from '@/components/bilateral/PostFeed'
import { COUNTRY_NAMES, getCountryFlag, TRACKED_PAIRS } from '@/lib/utils'
import { RefreshCw } from 'lucide-react'

const COUNTRIES = Object.entries(COUNTRY_NAMES).map(([code, name]) => ({ code, name }))

function BilateralContent() {
  const params = useSearchParams()
  const router = useRouter()
  const [countryA, setCountryA] = useState(params.get('a') || 'US')
  const [countryB, setCountryB] = useState(params.get('b') || 'CN')
  const { data, loading, refetch } = useBilateral(countryA, countryB)

  const handleSwap = () => { setCountryA(countryB); setCountryB(countryA) }
  const handleRegenerate = async () => { await api.generateBrief(countryA, countryB); refetch() }

  const nameA = COUNTRY_NAMES[countryA] ?? countryA
  const nameB = COUNTRY_NAMES[countryB] ?? countryB

  return (
    <div className="fade-in">
      {/* Page header banner */}
      <div style={{
        margin: '-32px -24px 32px',
        background: 'var(--bg-navy)',
        position: 'relative',
        overflow: 'hidden',
        padding: '32px 24px',
      }}>
        <div style={{
          position: 'absolute', inset: 0,
          backgroundImage: `url('https://images.unsplash.com/photo-1551836022-d5d88e9218df?w=1600&q=80')`,
          backgroundSize: 'cover', backgroundPosition: 'center',
          opacity: 0.10,
        }} />
        <div style={{ position: 'relative', zIndex: 1, maxWidth: 1440, margin: '0 auto' }}>
          <div className="section-label" style={{ color: '#9aacbe', marginBottom: 12 }}>Bilateral Analysis</div>

          {/* Country pair display */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 20, marginBottom: 20, flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ fontSize: 32 }}>{getCountryFlag(countryA)}</span>
              <div>
                <div style={{ fontFamily: 'var(--font-serif)', fontWeight: 700, fontSize: 24, color: '#ffffff' }}>{nameA}</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#9aacbe' }}>{countryA}</div>
              </div>
            </div>
            <div style={{ fontFamily: 'var(--font-sans)', fontSize: 16, color: '#4a6080', padding: '0 8px' }}>—</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ fontSize: 32 }}>{getCountryFlag(countryB)}</span>
              <div>
                <div style={{ fontFamily: 'var(--font-serif)', fontWeight: 700, fontSize: 24, color: '#ffffff' }}>{nameB}</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#9aacbe' }}>{countryB}</div>
              </div>
            </div>
            {data?.risk_score && (
              <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 32, fontWeight: 600, color: '#ffffff' }}>
                  {data.risk_score.score?.toFixed(0) ?? '—'}
                </span>
                <div>
                  <div style={{ fontFamily: 'var(--font-sans)', fontSize: 10, color: '#9aacbe', letterSpacing: '0.08em', textTransform: 'uppercase' }}>Risk Score</div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#9aacbe' }}>/100</div>
                </div>
              </div>
            )}
          </div>

          {/* Controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            {/* Quick pairs */}
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {TRACKED_PAIRS.slice(0, 6).map(([a, b]) => {
                const active = countryA === a && countryB === b
                return (
                  <button
                    key={`${a}-${b}`}
                    onClick={() => { setCountryA(a); setCountryB(b) }}
                    style={{
                      fontFamily: 'var(--font-mono)', fontSize: 11,
                      padding: '4px 10px', borderRadius: 3,
                      background: active ? 'rgba(255,255,255,0.12)' : 'rgba(255,255,255,0.04)',
                      color: active ? '#ffffff' : '#9aacbe',
                      border: `1px solid ${active ? 'rgba(255,255,255,0.2)' : 'rgba(255,255,255,0.08)'}`,
                      cursor: 'pointer', transition: 'all 0.12s',
                    }}
                  >
                    {getCountryFlag(a)}{getCountryFlag(b)} {a}–{b}
                  </button>
                )
              })}
            </div>

            <div style={{ display: 'flex', gap: 6, marginLeft: 'auto', alignItems: 'center' }}>
              <select
                value={countryA}
                onChange={e => setCountryA(e.target.value)}
                style={{ fontFamily: 'var(--font-sans)', fontSize: 12, padding: '5px 8px', borderRadius: 3, background: 'rgba(255,255,255,0.06)', color: '#e8eef5', border: '1px solid rgba(255,255,255,0.12)', outline: 'none' }}
              >
                {COUNTRIES.map(c => <option key={c.code} value={c.code}>{c.code} — {c.name}</option>)}
              </select>
              <button onClick={handleSwap} style={{ fontFamily: 'var(--font-mono)', fontSize: 14, padding: '5px 10px', borderRadius: 3, background: 'rgba(255,255,255,0.06)', color: '#9aacbe', border: '1px solid rgba(255,255,255,0.12)', cursor: 'pointer' }}>
                ⇄
              </button>
              <select
                value={countryB}
                onChange={e => setCountryB(e.target.value)}
                style={{ fontFamily: 'var(--font-sans)', fontSize: 12, padding: '5px 8px', borderRadius: 3, background: 'rgba(255,255,255,0.06)', color: '#e8eef5', border: '1px solid rgba(255,255,255,0.12)', outline: 'none' }}
              >
                {COUNTRIES.map(c => <option key={c.code} value={c.code}>{c.code} — {c.name}</option>)}
              </select>
              <button onClick={refetch} className="btn btn-ghost" style={{ color: '#9aacbe', borderColor: 'rgba(255,255,255,0.12)', padding: '5px 10px' }}>
                <RefreshCw size={12} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 200 }}>
          <div style={{ width: 28, height: 28, border: '2px solid var(--border)', borderTopColor: 'var(--navy)', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
        </div>
      )}

      {/* Content */}
      {!loading && data && (
        <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr 1fr', gap: 24 }}>

          {/* Left column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* Risk gauge */}
            <div className="surface" style={{ padding: 24 }}>
              <div className="section-label" style={{ marginBottom: 16 }}>Risk Assessment</div>
              <RiskGauge score={data.risk_score.score} level={data.risk_score.classification} />
              {data.risk_score.score_change != null && (
                <div style={{ textAlign: 'center', marginTop: 8 }}>
                  <span style={{
                    fontFamily: 'var(--font-mono)', fontSize: 12,
                    color: data.risk_score.score_change > 0 ? 'var(--risk-critical)' : 'var(--risk-low)',
                  }}>
                    {data.risk_score.score_change > 0 ? '+' : ''}{data.risk_score.score_change.toFixed(1)} pts vs previous
                  </span>
                </div>
              )}
            </div>

            {/* Breakdown */}
            <div className="surface" style={{ padding: 24 }}>
              <div className="section-label" style={{ marginBottom: 16 }}>Risk Breakdown</div>
              <BreakdownPanel breakdown={data.risk_score.breakdown} />
            </div>

            {/* Key drivers */}
            {data.risk_score.contributing_factors?.length > 0 && (
              <div className="surface" style={{ padding: 24 }}>
                <div className="section-label" style={{ marginBottom: 14 }}>Key Drivers</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {data.risk_score.contributing_factors.map((f: any, i: number) => (
                    <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)', marginTop: 2, flexShrink: 0 }}>
                        {String(i + 1).padStart(2, '0')}
                      </span>
                      <span style={{ fontFamily: 'var(--font-sans)', fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                        {f.factor}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Center column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div className="surface" style={{ padding: 24 }}>
              <div className="section-label" style={{ marginBottom: 16 }}>Sentiment Timeline — 72H</div>
              <SentimentTimeline
                dataA={data.sentiment_timeline.country_a}
                dataB={data.sentiment_timeline.country_b}
                labelA={countryA}
                labelB={countryB}
              />
            </div>

            <div className="surface" style={{ padding: 24 }}>
              <div className="section-label" style={{ marginBottom: 16 }}>Intelligence Brief</div>
              <IntelBriefPanel brief={data.intel_brief} onRegenerate={handleRegenerate} />
            </div>
          </div>

          {/* Right column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div className="surface" style={{ padding: 24 }}>
              <div className="section-label" style={{ marginBottom: 16 }}>Hostile Posts — 72H</div>
              <div style={{ maxHeight: 340, overflowY: 'auto' }}>
                <PostFeed posts={data.top_posts?.slice(0, 10)} />
              </div>
            </div>

            <div className="surface" style={{ padding: 24 }}>
              <div className="section-label" style={{ marginBottom: 16 }}>GDELT Conflict Events</div>
              {!data.gdelt_events?.length ? (
                <p style={{ fontFamily: 'var(--font-sans)', fontSize: 13, color: 'var(--text-faint)', textAlign: 'center', padding: '20px 0' }}>
                  No high-conflict GDELT events detected
                </p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 280, overflowY: 'auto' }}>
                  {data.gdelt_events.slice(0, 10).map((e: any, i: number) => (
                    <div key={i} style={{ padding: '10px 12px', background: 'var(--bg-subtle)', borderRadius: 4, borderLeft: '2px solid var(--risk-high-border)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                        <span style={{ fontFamily: 'var(--font-sans)', fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>
                          {getCountryFlag(e.actor1 || '')} {e.actor1 || '?'} → {getCountryFlag(e.actor2 || '')} {e.actor2 || '?'}
                        </span>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--risk-high)' }}>
                          GS {e.goldstein_scale?.toFixed(1)}
                        </span>
                      </div>
                      <span style={{ fontFamily: 'var(--font-sans)', fontSize: 11, color: 'var(--text-faint)' }}>
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

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

export default function BilateralPage() {
  return <Suspense><BilateralContent /></Suspense>
}
