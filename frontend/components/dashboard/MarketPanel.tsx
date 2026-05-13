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

