'use client'
import { IntelBrief } from '@/lib/types'
import { RefreshCw } from 'lucide-react'

function riskStyle(level: string | null): { color: string; bg: string; border: string } {
  switch (level) {
    case 'CRITICAL': return { color: 'var(--risk-critical)', bg: 'var(--risk-critical-bg)', border: 'var(--risk-critical-border)' }
    case 'HIGH':     return { color: 'var(--risk-high)',     bg: 'var(--risk-high-bg)',     border: 'var(--risk-high-border)' }
    case 'MODERATE': return { color: 'var(--risk-moderate)', bg: 'var(--risk-moderate-bg)', border: 'var(--risk-moderate-border)' }
    default:         return { color: 'var(--risk-low)',      bg: 'var(--risk-low-bg)',      border: 'var(--risk-low-border)' }
  }
}

export default function IntelBriefPanel({ brief, onRegenerate }: { brief: IntelBrief; onRegenerate?: () => void }) {
  if (brief.is_generating && !brief.headline) {
    return (
      <div style={{ textAlign: 'center', padding: '32px 0' }}>
        <p style={{ fontFamily: 'var(--font-sans)', fontSize: 13, color: 'var(--text-muted)' }}>
          Generating intelligence brief...
        </p>
      </div>
    )
  }

  if (!brief.headline) {
    return (
      <div style={{ textAlign: 'center', padding: '32px 0' }}>
        <p style={{ fontFamily: 'var(--font-sans)', fontSize: 13, color: 'var(--text-faint)', marginBottom: 16 }}>
          No brief generated yet.
        </p>
        {onRegenerate && (
          <button onClick={onRegenerate} className="btn btn-secondary" style={{ fontSize: 12 }}>
            <RefreshCw size={12} /> Generate Brief
          </button>
        )}
      </div>
    )
  }

  const rs = riskStyle(brief.risk_level)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Headline + level */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
        <h3 style={{ fontFamily: 'var(--font-serif)', fontWeight: 600, fontSize: 16, color: 'var(--text-primary)', lineHeight: 1.4, margin: 0 }}>
          {brief.headline}
        </h3>
        {brief.risk_level && (
          <span className="risk-badge" style={{ color: rs.color, background: rs.bg, borderColor: rs.border, flexShrink: 0 }}>
            {brief.risk_level}
          </span>
        )}
      </div>

      {/* Summary */}
      {brief.summary && (
        <p style={{ fontFamily: 'var(--font-sans)', fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.7, margin: 0 }}>
          {brief.summary}
        </p>
      )}

      {/* Key drivers */}
      {brief.key_drivers?.length > 0 && (
        <div>
          <div className="section-label" style={{ marginBottom: 10 }}>Key Drivers</div>
          <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 6 }}>
            {brief.key_drivers.map((d, i) => (
              <li key={i} style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)', marginTop: 3, flexShrink: 0 }}>
                  {String(i + 1).padStart(2, '0')}
                </span>
                <span style={{ fontFamily: 'var(--font-sans)', fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{d}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Market implications */}
      {brief.market_implications && (
        <div style={{ padding: '12px 14px', background: '#eef2f7', border: '1px solid #c0cfe0', borderRadius: 4 }}>
          <div className="section-label" style={{ color: 'var(--navy-mid)', marginBottom: 6 }}>Market Implications</div>
          <p style={{ fontFamily: 'var(--font-sans)', fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>
            {brief.market_implications}
          </p>
        </div>
      )}

      {/* 72hr outlook */}
      {brief.outlook_72hr && (
        <div style={{ padding: '12px 14px', background: 'var(--risk-moderate-bg)', border: '1px solid var(--risk-moderate-border)', borderRadius: 4 }}>
          <div className="section-label" style={{ color: 'var(--risk-moderate)', marginBottom: 6 }}>72-Hour Outlook</div>
          <p style={{ fontFamily: 'var(--font-sans)', fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>
            {brief.outlook_72hr}
          </p>
        </div>
      )}

      {/* Footer */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: 12, borderTop: '1px solid var(--border)' }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)' }}>
          {brief.generated_at ? new Date(brief.generated_at).toLocaleString() : 'Unknown'}
          {brief.confidence != null && ` · Confidence ${(brief.confidence * 100).toFixed(0)}%`}
        </span>
        {onRegenerate && (
          <button onClick={onRegenerate} className="btn btn-ghost" style={{ fontSize: 11 }}>
            <RefreshCw size={11} /> Regenerate
          </button>
        )}
      </div>
    </div>
  )
}
