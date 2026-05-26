'use client'

import React, { useEffect, useState, useCallback } from 'react'
import {
  RefreshCw, AlertTriangle, CheckCircle, Minus,
  Globe, Heart, Repeat2, Eye, ExternalLink, Brain,
} from 'lucide-react'
import { api } from '@/lib/api'

// ── Types ─────────────────────────────────────────────────────────────────────

interface Leader {
  username: string
  name: string
  title: string
  country: string
  country_code: string
  profile_picture: string
}

interface Tweet {
  id: string
  text: string
  created_at: string
  url: string
  like_count: number
  retweet_count: number
  view_count: number
}

interface Analysis {
  label: string
  risk_score: number
  p_negative: number
  p_neutral: number
  p_positive: number
  confidence: number
  model_used: string
  affected_countries: string[]
  affected_names: string[]
  intel_summary: string
}

interface Statement {
  leader: Leader
  tweet: Tweet
  analysis: Analysis
}

interface StatementsResponse {
  statements: Statement[]
  total: number
  leaders: number
  model_ready: boolean
  scored_at: string
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const COUNTRY_FLAGS: Record<string, string> = {
  US: '🇺🇸', CN: '🇨🇳', RU: '🇷🇺', IN: '🇮🇳', PK: '🇵🇰',
  GB: '🇬🇧', DE: '🇩🇪', FR: '🇫🇷', JP: '🇯🇵', KR: '🇰🇷',
  KP: '🇰🇵', IR: '🇮🇷', IL: '🇮🇱', SA: '🇸🇦', TR: '🇹🇷',
  UA: '🇺🇦', BR: '🇧🇷', CA: '🇨🇦', MX: '🇲🇽', AR: '🇦🇷', SV: '🇸🇻',
}

function getRiskColor(score: number): string {
  if (score >= 75) return '#ef4444'
  if (score >= 55) return '#f97316'
  if (score >= 35) return '#eab308'
  return '#22c55e'
}

function getRiskLabel(score: number): string {
  if (score >= 75) return 'CRITICAL'
  if (score >= 55) return 'HIGH'
  if (score >= 35) return 'MODERATE'
  return 'LOW'
}

function getSentimentIcon(label: string) {
  if (label === 'NEGATIVE') return <AlertTriangle size={12} style={{ color: '#ef4444' }} />
  if (label === 'POSITIVE') return <CheckCircle size={12} style={{ color: '#22c55e' }} />
  return <Minus size={12} style={{ color: '#94a3b8' }} />
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return String(n)
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric',
    })
  } catch {
    return iso
  }
}

// ── Statement Card ────────────────────────────────────────────────────────────

function StatementCard({ s, expanded, onToggle }: {
  s: Statement
  expanded: boolean
  onToggle: () => void
}) {
  const { leader, tweet, analysis } = s
  const riskColor = getRiskColor(analysis.risk_score)
  const riskLabel = getRiskLabel(analysis.risk_score)

  return (
    <div
      style={{
        background: 'var(--bg-surface, #0f172a)',
        border: `1px solid var(--border, #1e293b)`,
        borderLeft: `3px solid ${riskColor}`,
        borderRadius: 8,
        overflow: 'hidden',
        transition: 'box-shadow 0.15s ease',
      }}
    >
      {/* ── Card Header: Leader info ── */}
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: 12,
          padding: '14px 16px 10px',
          cursor: 'pointer',
        }}
        onClick={onToggle}
      >
        {/* Profile picture */}
        <div style={{ flexShrink: 0 }}>
          {leader.profile_picture ? (
            <img
              src={leader.profile_picture}
              alt={leader.name}
              width={40}
              height={40}
              style={{ borderRadius: '50%', border: `2px solid ${riskColor}30`, objectFit: 'cover' }}
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = 'none'
              }}
            />
          ) : (
            <div style={{
              width: 40, height: 40, borderRadius: '50%',
              background: `${riskColor}20`,
              border: `2px solid ${riskColor}40`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 16,
            }}>
              {COUNTRY_FLAGS[leader.country_code] || '🌐'}
            </div>
          )}
        </div>

        {/* Leader name + title */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <span style={{
              fontFamily: 'var(--font-sans, sans-serif)',
              fontWeight: 600,
              fontSize: 14,
              color: 'var(--text-primary, #f1f5f9)',
            }}>
              {leader.name}
            </span>
            {leader.country_code && (
              <span style={{ fontSize: 14 }}>{COUNTRY_FLAGS[leader.country_code]}</span>
            )}
            <span style={{
              fontFamily: 'var(--font-mono, monospace)',
              fontSize: 11,
              color: 'var(--text-faint, #475569)',
            }}>
              @{leader.username}
            </span>
          </div>
          {leader.title && (
            <div style={{
              fontFamily: 'var(--font-sans, sans-serif)',
              fontSize: 11,
              color: 'var(--text-muted, #64748b)',
              marginTop: 2,
            }}>
              {leader.title}
            </div>
          )}
        </div>

        {/* Risk badge */}
        <div style={{
          flexShrink: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'flex-end',
          gap: 4,
        }}>
          <div style={{
            background: `${riskColor}18`,
            border: `1px solid ${riskColor}40`,
            borderRadius: 4,
            padding: '3px 8px',
            display: 'flex',
            alignItems: 'center',
            gap: 5,
          }}>
            <span style={{
              fontFamily: 'var(--font-mono, monospace)',
              fontSize: 13,
              fontWeight: 700,
              color: riskColor,
            }}>
              {analysis.risk_score.toFixed(0)}
            </span>
            <span style={{
              fontFamily: 'var(--font-mono, monospace)',
              fontSize: 9,
              color: riskColor,
              letterSpacing: '0.06em',
            }}>
              {riskLabel}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            {getSentimentIcon(analysis.label)}
            <span style={{
              fontFamily: 'var(--font-mono, monospace)',
              fontSize: 9,
              color: analysis.label === 'NEGATIVE' ? '#ef4444'
                : analysis.label === 'POSITIVE' ? '#22c55e' : '#94a3b8',
            }}>
              {analysis.label}
            </span>
          </div>
        </div>
      </div>

      {/* ── Tweet text ── */}
      <div style={{ padding: '0 16px 10px' }}>
        <p style={{
          fontFamily: 'var(--font-sans, sans-serif)',
          fontSize: 13,
          color: 'var(--text-primary, #e2e8f0)',
          lineHeight: 1.6,
          margin: 0,
        }}>
          {tweet.text.length > 280 && !expanded
            ? tweet.text.slice(0, 280) + '…'
            : tweet.text}
        </p>
        {tweet.text.length > 280 && (
          <button
            onClick={onToggle}
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              fontFamily: 'var(--font-sans, sans-serif)',
              fontSize: 11, color: 'var(--navy, #3b82f6)',
              padding: '4px 0', marginTop: 2,
            }}
          >
            {expanded ? 'Show less' : 'Show more'}
          </button>
        )}
      </div>

      {/* ── Risk score bar ── */}
      <div style={{ padding: '0 16px 10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{
            flex: 1, height: 3,
            background: 'var(--border, #1e293b)',
            borderRadius: 2,
          }}>
            <div style={{
              width: `${analysis.risk_score}%`,
              height: '100%',
              background: riskColor,
              borderRadius: 2,
              transition: 'width 0.4s ease',
            }} />
          </div>
          <span style={{
            fontFamily: 'var(--font-mono, monospace)',
            fontSize: 10,
            color: 'var(--text-faint, #475569)',
            whiteSpace: 'nowrap',
          }}>
            {analysis.risk_score.toFixed(1)}/100
          </span>
        </div>
        {/* Probability breakdown */}
        <div style={{ display: 'flex', gap: 12, marginTop: 6 }}>
          {[
            { label: 'neg', val: analysis.p_negative, color: '#ef4444' },
            { label: 'neu', val: analysis.p_neutral, color: '#94a3b8' },
            { label: 'pos', val: analysis.p_positive, color: '#22c55e' },
          ].map(({ label, val, color }) => (
            <span key={label} style={{
              fontFamily: 'var(--font-mono, monospace)',
              fontSize: 9, color,
            }}>
              {label}={(val * 100).toFixed(1)}%
            </span>
          ))}
          <span style={{
            fontFamily: 'var(--font-mono, monospace)',
            fontSize: 9,
            color: 'var(--text-faint, #475569)',
            marginLeft: 'auto',
          }}>
            conf={(analysis.confidence * 100).toFixed(0)}% · {analysis.model_used}
          </span>
        </div>
      </div>

      {/* ── Affected countries ── */}
      {analysis.affected_countries.length > 0 && (
        <div style={{ padding: '0 16px 10px', display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
          <Globe size={11} style={{ color: 'var(--text-faint, #475569)', flexShrink: 0 }} />
          {analysis.affected_countries.map((code) => (
            <span key={code} style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 3,
              background: 'var(--bg-subtle, #0f172a)',
              border: '1px solid var(--border, #1e293b)',
              borderRadius: 3,
              padding: '2px 6px',
              fontFamily: 'var(--font-mono, monospace)',
              fontSize: 10,
              color: 'var(--text-muted, #64748b)',
            }}>
              {COUNTRY_FLAGS[code] || '🌐'} {code}
            </span>
          ))}
        </div>
      )}

      {/* ── Intel summary ── */}
      {analysis.intel_summary && (
        <div style={{
          margin: '0 16px 12px',
          background: 'var(--bg-subtle, #0a0f1a)',
          border: '1px solid var(--border, #1e293b)',
          borderLeft: `2px solid ${riskColor}60`,
          borderRadius: 4,
          padding: '8px 12px',
        }}>
          <div style={{
            fontFamily: 'var(--font-mono, monospace)',
            fontSize: 9,
            color: 'var(--text-faint, #475569)',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            marginBottom: 4,
          }}>
            Intelligence Summary
          </div>
          <p style={{
            fontFamily: 'var(--font-sans, sans-serif)',
            fontSize: 12,
            color: 'var(--text-muted, #94a3b8)',
            lineHeight: 1.5,
            margin: 0,
          }}>
            {analysis.intel_summary}
          </p>
        </div>
      )}

      {/* ── Footer: engagement + date + link ── */}
      <div style={{
        padding: '8px 16px',
        borderTop: '1px solid var(--border, #1e293b)',
        display: 'flex',
        alignItems: 'center',
        gap: 16,
        flexWrap: 'wrap',
      }}>
        {[
          { icon: <Heart size={11} />, val: tweet.like_count },
          { icon: <Repeat2 size={11} />, val: tweet.retweet_count },
          { icon: <Eye size={11} />, val: tweet.view_count },
        ].map(({ icon, val }, i) => (
          <div key={i} style={{
            display: 'flex', alignItems: 'center', gap: 4,
            fontFamily: 'var(--font-mono, monospace)',
            fontSize: 10,
            color: 'var(--text-faint, #475569)',
          }}>
            {icon}
            {formatNumber(val)}
          </div>
        ))}

        <span style={{
          fontFamily: 'var(--font-sans, sans-serif)',
          fontSize: 10,
          color: 'var(--text-faint, #475569)',
          marginLeft: 'auto',
        }}>
          {formatDate(tweet.created_at)}
        </span>

        {tweet.url && (
          <a
            href={tweet.url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'flex', alignItems: 'center', gap: 3,
              fontFamily: 'var(--font-sans, sans-serif)',
              fontSize: 10,
              color: 'var(--navy, #3b82f6)',
              textDecoration: 'none',
            }}
          >
            <ExternalLink size={10} />
            View
          </a>
        )}
      </div>
    </div>
  )
}

// ── Main Panel ────────────────────────────────────────────────────────────────

export default function PoliticalStatementsPanel() {
  const [data, setData] = useState<StatementsResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())

  const fetchStatements = useCallback(async (forceReload = false) => {
    setLoading(true)
    setError(null)
    try {
      const result = await api.politicalStatements(30, forceReload)
      setData(result)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load statements')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchStatements() }, [fetchStatements])

  const toggleExpanded = (id: string) => {
    setExpandedIds(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  // Sort by risk score (highest first)
  const filtered = (data?.statements ?? [])
    .sort((a, b) => b.analysis.risk_score - a.analysis.risk_score)

  return (
    <div className="surface" style={{ overflow: 'hidden' }}>
      {/* ── Header ── */}
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
            <div style={{
              fontFamily: 'var(--font-sans)',
              fontWeight: 600,
              fontSize: 14,
              color: 'var(--text-primary)',
            }}>
              Top Political Statements
            </div>
            <div style={{
              fontFamily: 'var(--font-sans)',
              fontSize: 11,
              color: 'var(--text-faint)',
              marginTop: 1,
            }}>
              Recent tweets from world leaders · scored by RoBERTa + LR
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button
            onClick={() => fetchStatements(true)}
            disabled={loading}
            className="btn btn-secondary"
            style={{ fontSize: 11, padding: '4px 10px' }}
          >
            <RefreshCw
              size={11}
              style={{ animation: loading ? 'spin 0.8s linear infinite' : 'none' }}
            />
            {loading ? 'Scoring…' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* ── Content ── */}
      <div style={{ padding: '16px 20px', maxHeight: 800, overflowY: 'auto' }}>
        {error && (
          <div style={{
            background: '#7f1d1d20',
            border: '1px solid #dc262640',
            borderRadius: 4,
            padding: '10px 14px',
            marginBottom: 16,
            fontFamily: 'var(--font-sans)',
            fontSize: 12,
            color: '#ef4444',
          }}>
            {error}
          </div>
        )}

        {loading && !data && (
          <div style={{
            textAlign: 'center',
            padding: '48px 0',
            color: 'var(--text-faint)',
            fontSize: 12,
          }}>
            <div style={{
              width: 24, height: 24,
              border: '2px solid var(--border)',
              borderTopColor: 'var(--navy)',
              borderRadius: '50%',
              animation: 'spin 0.8s linear infinite',
              margin: '0 auto 12px',
            }} />
            Scoring {data ? '' : 'political statements'} with RoBERTa model…
          </div>
        )}

        {filtered.length === 0 && !loading && (
          <div style={{
            textAlign: 'center',
            padding: '32px 0',
            color: 'var(--text-faint)',
            fontSize: 12,
          }}>
            No statements match the current filter.
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {filtered.map((s) => (
            <StatementCard
              key={`${s.leader.username}-${s.tweet.id}`}
              s={s}
              expanded={expandedIds.has(s.tweet.id)}
              onToggle={() => toggleExpanded(s.tweet.id)}
            />
          ))}
        </div>

        {data && (
          <div style={{
            fontFamily: 'var(--font-sans)',
            fontSize: 10,
            color: 'var(--text-faint)',
            marginTop: 16,
            textAlign: 'center',
          }}>
            Scored at {new Date(data.scored_at).toLocaleTimeString()} ·
            {' '}Model: RoBERTa → risk score (0–100)
          </div>
        )}
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
