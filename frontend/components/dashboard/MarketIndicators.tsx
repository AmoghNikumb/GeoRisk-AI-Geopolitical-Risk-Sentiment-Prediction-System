'use client'

import { MarketData } from '@/lib/types'

interface MarketIndicatorsProps {
  market: MarketData | null
}

function MarketRow({ label, value, change, prefix = '' }: {
  label: string
  value: number | null
  change?: number | null
  prefix?: string
}) {
  const isPos = (change ?? 0) >= 0
  const changeColor = change == null ? 'var(--text-faint)' : change > 0 ? 'var(--positive)' : 'var(--negative)'

  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '11px 0',
      borderBottom: '1px solid var(--bg-subtle)',
    }}>
      <span style={{ fontFamily: 'var(--font-sans)', fontSize: 13, color: 'var(--text-secondary)' }}>
        {label}
      </span>
      <div style={{ textAlign: 'right' }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 14, fontWeight: 500, color: 'var(--text-primary)' }}>
          {value != null ? `${prefix}${value.toFixed(2)}` : '—'}
        </span>
        {change != null && (
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: changeColor, marginLeft: 8 }}>
            {change > 0 ? '+' : ''}{change.toFixed(2)}%
          </span>
        )}
      </div>
    </div>
  )
}

function stressLabel(score: number | null): { label: string; color: string } {
  if (score == null) return { label: 'UNKNOWN', color: 'var(--text-faint)' }
  if (score > 0.8) return { label: 'CRITICAL', color: 'var(--risk-critical)' }
  if (score > 0.6) return { label: 'HIGH',     color: 'var(--risk-high)' }
  if (score > 0.4) return { label: 'MODERATE', color: 'var(--risk-moderate)' }
  return               { label: 'LOW',      color: 'var(--risk-low)' }
}

export default function MarketIndicators({ market }: MarketIndicatorsProps) {
  const stress = stressLabel(market?.market_stress_score ?? null)
  const stressPct = (market?.market_stress_score ?? 0) * 100

  return (
    <div className="surface" style={{ overflow: 'hidden' }}>
      {/* Header */}
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid var(--border)',
        background: 'var(--bg-subtle)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <span style={{ fontFamily: 'var(--font-sans)', fontWeight: 600, fontSize: 13, color: 'var(--text-primary)' }}>
          Market Indicators
        </span>
        {market?.captured_at && (
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)' }}>
            {new Date(market.captured_at).toLocaleTimeString()}
          </span>
        )}
      </div>

      <div style={{ padding: '4px 20px 16px' }}>
        <MarketRow label="VIX — Fear Index"  value={market?.vix ?? null} />
        <MarketRow label="S&P 500"           value={market?.sp500 ?? null} change={market?.sp500_change_pct ?? null} />
        <MarketRow label="WTI Crude Oil"     value={market?.crude_oil ?? null} prefix="$" />
        <MarketRow label="Gold (spot)"       value={market?.gold ?? null} prefix="$" />
        {market?.dxy != null && (
          <MarketRow label="USD Index (DXY)" value={market.dxy} />
        )}
      </div>

      {/* Stress score */}
      {market && (
        <div style={{
          padding: '14px 20px',
          borderTop: '1px solid var(--border)',
          background: 'var(--bg-subtle)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
            <span style={{ fontFamily: 'var(--font-sans)', fontSize: 12, color: 'var(--text-muted)' }}>
              Market Stress Index
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 600, color: stress.color, letterSpacing: '0.06em' }}>
              {stress.label}
            </span>
          </div>
          <div className="score-bar">
            <div className="score-bar-fill" style={{ width: `${stressPct}%`, background: stress.color }} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)' }}>0</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: stress.color }}>{stressPct.toFixed(0)}%</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)' }}>100</span>
          </div>
        </div>
      )}
    </div>
  )
}
