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

