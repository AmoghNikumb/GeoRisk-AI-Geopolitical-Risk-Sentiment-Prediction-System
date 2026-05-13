'use client'

import { RiskScore } from '@/lib/types'
import { getCountryFlag, COUNTRY_NAMES, formatScore } from '@/lib/utils'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface RiskHeatmapProps {
  risks: RiskScore[]
  onSelectPair: (a: string, b: string) => void
}

function getRiskStyle(score: number): { color: string; bg: string; border: string; label: string } {
  if (score >= 80) return { color: 'var(--risk-critical)', bg: 'var(--risk-critical-bg)', border: 'var(--risk-critical-border)', label: 'CRITICAL' }
  if (score >= 60) return { color: 'var(--risk-high)',     bg: 'var(--risk-high-bg)',     border: 'var(--risk-high-border)',     label: 'HIGH' }
  if (score >= 35) return { color: 'var(--risk-moderate)', bg: 'var(--risk-moderate-bg)', border: 'var(--risk-moderate-border)', label: 'MODERATE' }
  return              { color: 'var(--risk-low)',      bg: 'var(--risk-low-bg)',      border: 'var(--risk-low-border)',      label: 'LOW' }
}

export default function RiskHeatmap({ risks, onSelectPair }: RiskHeatmapProps) {
  const sorted = [...risks].sort((a, b) => b.score - a.score)

  if (sorted.length === 0) {
    return (
      <div className="surface" style={{ padding: 40, textAlign: 'center' }}>
        <p style={{ fontFamily: 'var(--font-sans)', fontSize: 13, color: 'var(--text-muted)' }}>
          Risk scores will appear after the first pipeline run.
        </p>
      </div>
    )
  }

  return (
    <div className="surface" style={{ overflow: 'hidden' }}>
      {/* Table header */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '2fr 1fr 1fr 1fr 80px',
        padding: '10px 20px',
        borderBottom: '1px solid var(--border)',
        background: 'var(--bg-subtle)',
      }}>
        {['Country Pair', 'Risk Score', 'Classification', 'Change', 'Action'].map(h => (
          <div key={h} className="label-caps">{h}</div>
        ))}
      </div>

      {/* Rows */}
      <div>
        {sorted.map((risk, i) => {
          const style = getRiskStyle(risk.score)
          const change = risk.score_change ?? 0
          const TrendIcon = change > 3 ? TrendingUp : change < -3 ? TrendingDown : Minus
          const trendColor = change > 3 ? 'var(--risk-critical)' : change < -3 ? 'var(--risk-low)' : 'var(--text-faint)'
          const nameA = COUNTRY_NAMES[risk.country_a] ?? risk.country_a
          const nameB = COUNTRY_NAMES[risk.country_b] ?? risk.country_b

          return (
            <div
              key={risk.pair_key}
              style={{
                display: 'grid',
                gridTemplateColumns: '2fr 1fr 1fr 1fr 80px',
                padding: '14px 20px',
                borderBottom: i < sorted.length - 1 ? '1px solid var(--bg-subtle)' : 'none',
                alignItems: 'center',
                cursor: 'pointer',
                transition: 'background 0.12s ease',
                borderLeft: `3px solid ${style.border}`,
              }}
              onClick={() => onSelectPair(risk.country_a, risk.country_b)}
              onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-subtle)')}
              onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
            >
              {/* Country pair */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ fontSize: 18, lineHeight: 1 }}>{getCountryFlag(risk.country_a)}</span>
                <span style={{ fontSize: 18, lineHeight: 1 }}>{getCountryFlag(risk.country_b)}</span>
                <div>
                  <div style={{ fontFamily: 'var(--font-sans)', fontWeight: 600, fontSize: 13, color: 'var(--text-primary)' }}>
                    {nameA} — {nameB}
                  </div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)', marginTop: 1 }}>
                    {risk.country_a} / {risk.country_b}
                  </div>
                </div>
              </div>

              {/* Score */}
              <div>
                <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, fontSize: 20, color: style.color, lineHeight: 1 }}>
                  {formatScore(risk.score)}
                </div>
                <div style={{ marginTop: 6, width: 80 }}>
                  <div className="score-bar">
                    <div className="score-bar-fill" style={{ width: `${risk.score}%`, background: style.color }} />
                  </div>
                </div>
              </div>

              {/* Classification */}
              <div>
                <span className="risk-badge" style={{
                  color: style.color,
                  background: style.bg,
                  borderColor: style.border,
                }}>
                  {style.label}
                </span>
              </div>

              {/* Change */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                <TrendIcon size={13} style={{ color: trendColor }} />
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: trendColor }}>
                  {change !== 0 ? `${change > 0 ? '+' : ''}${change.toFixed(1)}` : '—'}
                </span>
              </div>

              {/* Action */}
              <div>
                <button
                  className="btn btn-secondary"
                  style={{ fontSize: 11, padding: '4px 10px' }}
                  onClick={e => { e.stopPropagation(); onSelectPair(risk.country_a, risk.country_b) }}
                >
                  Analyse
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
