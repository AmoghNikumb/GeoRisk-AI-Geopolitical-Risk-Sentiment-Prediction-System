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

