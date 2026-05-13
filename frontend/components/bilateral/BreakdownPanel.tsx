'use client'
import { RiskBreakdown } from '@/lib/types'

const FACTORS = [
  { key: 'negative_sentiment',      label: 'Negative Sentiment',   weight: 25 },
  { key: 'sentiment_deterioration', label: 'Deterioration Rate',   weight: 20 },
  { key: 'politician_hostility',    label: 'Politician Hostility', weight: 15 },
  { key: 'gdelt_conflict',          label: 'GDELT Conflict',       weight: 20 },
  { key: 'vix_spike',               label: 'VIX Spike',            weight: 10 },
  { key: 'market_stress',           label: 'Market Stress',        weight: 10 },
]

function factorColor(pct: number): string {
  if (pct > 70) return 'var(--risk-critical)'
  if (pct > 45) return 'var(--risk-high)'
  if (pct > 20) return 'var(--risk-moderate)'
  return 'var(--risk-low)'
}

export default function BreakdownPanel({ breakdown }: { breakdown: RiskBreakdown }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {FACTORS.map(f => {
        const val = breakdown[f.key as keyof RiskBreakdown] ?? 0
        const pct = Math.round(val * 100)
        const color = factorColor(pct)

        return (
          <div key={f.key}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 5 }}>
              <span style={{ fontFamily: 'var(--font-sans)', fontSize: 12, color: 'var(--text-secondary)' }}>
                {f.label}
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)' }}>
                  w={f.weight}%
                </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 600, color, minWidth: 28, textAlign: 'right' }}>
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
