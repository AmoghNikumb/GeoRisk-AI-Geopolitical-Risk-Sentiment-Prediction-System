'use client'

import React, { useEffect, useState } from 'react'
import { AlertTriangle, CheckCircle, Minus, RefreshCw, Brain, FlaskConical } from 'lucide-react'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ── Types ─────────────────────────────────────────────────────────────────────

interface PostScore {
  text: string
  label: number
  label_name: string
  p_negative: number
  p_neutral: number
  p_positive: number
  confidence: number
  risk_score: number
  // demo tweet extras
  pair?: string
  source?: string
  posted_at?: string
  query?: string
  // validation extras
  expected?: string
  correct?: boolean
  context?: string
}

interface ValidationResult {
  results: PostScore[]
  summary: {
    total: number
    correct: number
    accuracy: number
    avg_risk_score: number
  }
  model_status: {
    roberta_ready: boolean
    lr_ready: boolean
    model_source: string
    roberta_model: string
  }
  scored_at: string
}

interface DemoPairData {
  pair_key: string
  country_a: string
  country_b: string
  posts: PostScore[]
  aggregate: {
    risk_score: number
    risk_name: string
    p_high: number
    p_low: number
    confidence: number
    model_used: string
    roberta_risk_score: number
    n_posts: number
    n_negative: number
    n_neutral: number
    n_positive: number
    neg_ratio: number
    signal: string
  }
  data_note: string
}

interface DemoTweetsResult {
  pairs: Record<string, DemoPairData>
  total_posts: number
  scored_at: string
  data_note: string
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function getLabelStyle(label: number) {
  if (label === 0) return { color: 'var(--risk-critical)', icon: <AlertTriangle size={11} /> }
  if (label === 2) return { color: 'var(--risk-low)', icon: <CheckCircle size={11} /> }
  return { color: 'var(--text-muted)', icon: <Minus size={11} /> }
}

function getRiskColor(score: number) {
  if (score >= 75) return 'var(--risk-critical)'
  if (score >= 55) return 'var(--risk-high)'
  if (score >= 35) return 'var(--risk-moderate)'
  return 'var(--risk-low)'
}

function formatPct(v: number) {
  return `${(v * 100).toFixed(1)}%`
}

// ── Sub-components ────────────────────────────────────────────────────────────

function PostCard({ post, showExpected = false }: { post: PostScore; showExpected?: boolean }) {
  const ls = getLabelStyle(post.label)
  const riskColor = getRiskColor(post.risk_score)

  return (
    <div style={{
      background: 'var(--bg-subtle)',
      border: '1px solid var(--border)',
      borderLeft: `3px solid ${riskColor}`,
      borderRadius: 4,
      padding: '10px 14px',
      marginBottom: 8,
    }}>
      {/* Text */}
      <p style={{
        fontFamily: 'var(--font-sans)',
        fontSize: 12,
        color: 'var(--text-primary)',
        lineHeight: 1.5,
        marginBottom: 8,
      }}>
        {post.text}
      </p>

      {/* Scores row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
        {/* Label */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <span style={{ color: ls.color }}>{ls.icon}</span>
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            fontWeight: 600,
            color: ls.color,
            letterSpacing: '0.05em',
          }}>
            {post.label_name}
          </span>
        </div>

        {/* Risk score */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontFamily: 'var(--font-sans)', fontSize: 10, color: 'var(--text-faint)' }}>Risk</span>
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 13,
            fontWeight: 600,
            color: riskColor,
          }}>
            {post.risk_score.toFixed(1)}
          </span>
          <div style={{ width: 60, height: 3, background: 'var(--border)', borderRadius: 2 }}>
            <div style={{ width: `${post.risk_score}%`, height: '100%', background: riskColor, borderRadius: 2 }} />
          </div>
        </div>

        {/* Confidence */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <span style={{ fontFamily: 'var(--font-sans)', fontSize: 10, color: 'var(--text-faint)' }}>Conf</span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)' }}>
            {formatPct(post.confidence)}
          </span>
        </div>

        {/* Probabilities */}
        <div style={{ display: 'flex', gap: 8 }}>
          {[
            { label: 'neg', val: post.p_negative, color: 'var(--risk-critical)' },
            { label: 'neu', val: post.p_neutral,  color: 'var(--text-muted)' },
            { label: 'pos', val: post.p_positive, color: 'var(--risk-low)' },
          ].map(({ label, val, color }) => (
            <span key={label} style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color }}>
              {label}={formatPct(val)}
            </span>
          ))}
        </div>

        {/* Validation: expected vs actual */}
        {showExpected && post.expected && (
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ fontFamily: 'var(--font-sans)', fontSize: 10, color: 'var(--text-faint)' }}>
              expected: <span style={{ color: 'var(--text-muted)' }}>{post.expected}</span>
            </span>
            <span style={{ fontSize: 12 }}>{post.correct ? '✅' : '❌'}</span>
          </div>
        )}

        {/* Demo tweet: source tag */}
        {post.source && (
          <span style={{
            marginLeft: 'auto',
            fontFamily: 'var(--font-mono)',
            fontSize: 9,
            color: 'var(--text-faint)',
            background: 'var(--bg-surface)',
            border: '1px solid var(--border)',
            borderRadius: 3,
            padding: '1px 5px',
          }}>
            {post.source}
          </span>
        )}
      </div>
    </div>
  )
}

function AggregateBar({ data }: { data: DemoPairData['aggregate'] }) {
  const riskColor = getRiskColor(data.risk_score)
  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: `1px solid ${riskColor}`,
      borderRadius: 4,
      padding: '12px 16px',
      marginBottom: 12,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
        <div>
          <span style={{ fontFamily: 'var(--font-sans)', fontSize: 10, color: 'var(--text-faint)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Model Aggregate Score
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginTop: 2 }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 24, fontWeight: 700, color: riskColor }}>
              {data.risk_score.toFixed(1)}
            </span>
            <span style={{ fontFamily: 'var(--font-sans)', fontSize: 11, color: riskColor }}>
              / 100 — {data.risk_name}
            </span>
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            color: 'var(--text-faint)',
            marginBottom: 4,
          }}>
            model: {data.model_used}
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)' }}>
            P(High)={data.p_high.toFixed(3)} · P(Low)={data.p_low.toFixed(3)}
          </div>
        </div>
      </div>

      {/* Score bar */}
      <div style={{ width: '100%', height: 4, background: 'var(--border)', borderRadius: 2, marginBottom: 10 }}>
        <div style={{ width: `${data.risk_score}%`, height: '100%', background: riskColor, borderRadius: 2 }} />
      </div>

      {/* Breakdown */}
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        {[
          { label: 'Posts', val: data.n_posts },
          { label: 'Negative', val: data.n_negative, color: 'var(--risk-critical)' },
          { label: 'Neutral', val: data.n_neutral },
          { label: 'Positive', val: data.n_positive, color: 'var(--risk-low)' },
          { label: 'Neg ratio', val: formatPct(data.neg_ratio) },
          { label: 'RoBERTa', val: data.roberta_risk_score.toFixed(1) },
        ].map(({ label, val, color }) => (
          <div key={label}>
            <div style={{ fontFamily: 'var(--font-sans)', fontSize: 9, color: 'var(--text-faint)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{label}</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 600, color: color ?? 'var(--text-primary)' }}>{val}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

type Tab = 'validation' | 'demo_tweets'

export default function ModelDemoPanel() {
  const [tab, setTab] = useState<Tab>('validation')
  const [validation, setValidation] = useState<ValidationResult | null>(null)
  const [demoTweets, setDemoTweets] = useState<DemoTweetsResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedPair, setSelectedPair] = useState<string | null>(null)

  const fetchValidation = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/api/model/demo?t=${Date.now()}`)
      if (!res.ok) throw new Error(`API error ${res.status}`)
      setValidation(await res.json())
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load demo')
    } finally {
      setLoading(false)
    }
  }

  const fetchDemoTweets = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/api/model/demo-tweets?t=${Date.now()}`)
      if (!res.ok) throw new Error(`API error ${res.status}`)
      const data = await res.json()
      setDemoTweets(data)
      // Reset to first pair on refresh so user sees new data
      if (data.pairs) {
        setSelectedPair(Object.keys(data.pairs)[0] ?? null)
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load demo tweets')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (tab === 'validation') fetchValidation()
    else fetchDemoTweets()
  }, [tab])

  const handleRefresh = () => {
    if (tab === 'validation') fetchValidation()
    else fetchDemoTweets()
  }

  const pairKeys = demoTweets ? Object.keys(demoTweets.pairs) : []
  const activePairData = selectedPair && demoTweets ? demoTweets.pairs[selectedPair] : null

  return (
    <div className="surface" style={{ overflow: 'hidden' }}>
      {/* Header */}
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 12,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Brain size={16} style={{ color: 'var(--navy)' }} />
          <div>
            <div style={{ fontFamily: 'var(--font-sans)', fontWeight: 600, fontSize: 14, color: 'var(--text-primary)' }}>
              Model Inference Demo
            </div>
            <div style={{ fontFamily: 'var(--font-sans)', fontSize: 11, color: 'var(--text-faint)', marginTop: 1 }}>
              RoBERTa → feature vector → LogisticRegression (Acc: 92.8%, F1: 0.907)
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {/* Demo data badge */}
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 9,
            color: '#b45309',
            background: '#fef3c7',
            border: '1px solid #fde68a',
            borderRadius: 3,
            padding: '2px 7px',
            letterSpacing: '0.05em',
          }}>
            ⚠️ DEMO DATA
          </span>

          <button
            onClick={handleRefresh}
            disabled={loading}
            className="btn btn-secondary"
            style={{ fontSize: 11, padding: '4px 10px' }}
          >
            <RefreshCw size={11} style={{ animation: loading ? 'spin 0.8s linear infinite' : 'none' }} />
            {loading ? 'Loading' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div style={{
        display: 'flex',
        borderBottom: '1px solid var(--border)',
        background: 'var(--bg-subtle)',
      }}>
        {([
          { key: 'validation', label: 'Validation Sentences', icon: <FlaskConical size={12} /> },
          { key: 'demo_tweets', label: 'Demo Collected Posts', icon: <Brain size={12} /> },
        ] as { key: Tab; label: string; icon: React.ReactNode }[]).map(({ key, label, icon }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '10px 18px',
              fontFamily: 'var(--font-sans)',
              fontSize: 12,
              fontWeight: tab === key ? 600 : 400,
              color: tab === key ? 'var(--navy)' : 'var(--text-muted)',
              background: 'transparent',
              border: 'none',
              borderBottom: tab === key ? '2px solid var(--navy)' : '2px solid transparent',
              cursor: 'pointer',
              transition: 'all 0.12s ease',
            }}
          >
            {icon}
            {label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={{ padding: '16px 20px' }}>
        {error && (
          <div style={{
            background: 'var(--risk-critical-bg)',
            border: '1px solid var(--risk-critical-border)',
            borderRadius: 4,
            padding: '10px 14px',
            marginBottom: 16,
            fontFamily: 'var(--font-sans)',
            fontSize: 12,
            color: 'var(--risk-critical)',
          }}>
            {error}
          </div>
        )}

        {loading && !validation && !demoTweets && (
          <div style={{ textAlign: 'center', padding: '32px 0', color: 'var(--text-faint)', fontSize: 12 }}>
            Running model inference...
          </div>
        )}

        {/* ── Validation tab ── */}
        {tab === 'validation' && validation && (
          <div>
            {/* Model status */}
            <div style={{
              display: 'flex',
              gap: 16,
              marginBottom: 16,
              padding: '10px 14px',
              background: 'var(--bg-subtle)',
              borderRadius: 4,
              border: '1px solid var(--border)',
              flexWrap: 'wrap',
            }}>
              {[
                { label: 'RoBERTa', ready: validation.model_status.roberta_ready },
                { label: 'LR Model', ready: validation.model_status.lr_ready },
              ].map(({ label, ready }) => (
                <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                  <span style={{ width: 6, height: 6, borderRadius: '50%', background: ready ? '#4ade80' : '#f87171', display: 'inline-block' }} />
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)' }}>{label}</span>
                </div>
              ))}
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)', marginLeft: 'auto' }}>
                {validation.model_status.roberta_model}
              </div>
              <div style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
                color: validation.summary.accuracy >= 0.8 ? 'var(--risk-low)' : 'var(--risk-moderate)',
              }}>
                {validation.summary.correct}/{validation.summary.total} correct ({(validation.summary.accuracy * 100).toFixed(0)}%)
              </div>
            </div>

            {/* Sentences */}
            {validation.results.map((r, i) => (
              <PostCard key={i} post={r} showExpected />
            ))}

            <div style={{ fontFamily: 'var(--font-sans)', fontSize: 10, color: 'var(--text-faint)', marginTop: 8 }}>
              Scored at {new Date(validation.scored_at).toLocaleTimeString()} · Model validation only — not real-time data
            </div>
          </div>
        )}

        {/* ── Demo tweets tab ── */}
        {tab === 'demo_tweets' && demoTweets && (
          <div>
            {/* Data note */}
            <div style={{
              background: '#fef3c7',
              border: '1px solid #fde68a',
              borderRadius: 4,
              padding: '8px 12px',
              marginBottom: 14,
              fontFamily: 'var(--font-sans)',
              fontSize: 11,
              color: '#92400e',
            }}>
              {demoTweets.data_note}
            </div>

            {/* Pair selector */}
            <div style={{ display: 'flex', gap: 6, marginBottom: 14, flexWrap: 'wrap' }}>
              {pairKeys.map(pk => {
                const pairData = demoTweets.pairs[pk]
                const agg = pairData.aggregate
                const riskColor = getRiskColor(agg.risk_score)
                const isActive = selectedPair === pk
                return (
                  <button
                    key={pk}
                    onClick={() => setSelectedPair(pk)}
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 11,
                      padding: '5px 10px',
                      borderRadius: 4,
                      border: `1px solid ${isActive ? riskColor : 'var(--border)'}`,
                      background: isActive ? `${riskColor}18` : 'var(--bg-subtle)',
                      color: isActive ? riskColor : 'var(--text-muted)',
                      cursor: 'pointer',
                      transition: 'all 0.12s ease',
                    }}
                  >
                    {pk}
                    <span style={{ marginLeft: 5, fontWeight: 700 }}>{agg.risk_score.toFixed(0)}</span>
                  </button>
                )
              })}
            </div>

            {/* Active pair */}
            {activePairData && (
              <div>
                <AggregateBar data={activePairData.aggregate} />
                <div style={{ fontFamily: 'var(--font-sans)', fontSize: 11, color: 'var(--text-faint)', marginBottom: 10 }}>
                  {activePairData.posts.length} posts · {activePairData.data_note}
                </div>
                {activePairData.posts.map((post, i) => (
                  <PostCard key={i} post={post} />
                ))}
              </div>
            )}

            <div style={{ fontFamily: 'var(--font-sans)', fontSize: 10, color: 'var(--text-faint)', marginTop: 8 }}>
              Refreshed at {new Date(demoTweets.scored_at).toLocaleTimeString()} ·
              {demoTweets.total_posts} posts sampled from pool · {pairKeys.length} pairs ·
              <span style={{ color: '#92400e' }}> each refresh draws a new random sample</span>
            </div>
          </div>
        )}
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
