'use client'

interface SummaryStatsProps {
  stats: {
    total_monitored_pairs: number
    critical_risk_pairs: number
    high_risk_pairs: number
    moderate_risk_pairs: number
    low_risk_pairs: number
    unread_alerts: number
  }
}

interface KPI {
  label: string
  value: number | string
  sub?: string
  accent?: string
}

export default function SummaryStats({ stats }: SummaryStatsProps) {
  const kpis: KPI[] = [
    {
      label: 'Monitored Pairs',
      value: stats.total_monitored_pairs,
      sub: 'Country relationships tracked',
    },
    {
      label: 'Critical Risk',
      value: stats.critical_risk_pairs,
      sub: 'Pairs at critical level',
      accent: stats.critical_risk_pairs > 0 ? 'var(--risk-critical)' : undefined,
    },
    {
      label: 'High Risk',
      value: stats.high_risk_pairs,
      sub: 'Pairs at high level',
      accent: stats.high_risk_pairs > 0 ? 'var(--risk-high)' : undefined,
    },
    {
      label: 'Moderate Risk',
      value: stats.moderate_risk_pairs,
      sub: 'Pairs at moderate level',
      accent: stats.moderate_risk_pairs > 0 ? 'var(--risk-moderate)' : undefined,
    },
    {
      label: 'Unread Alerts',
      value: stats.unread_alerts,
      sub: 'Pending review',
      accent: stats.unread_alerts > 0 ? 'var(--risk-high)' : undefined,
    },
  ]

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(5, 1fr)',
      gap: 1,
      background: 'var(--border)',
      border: '1px solid var(--border)',
      borderRadius: 6,
      overflow: 'hidden',
    }}>
      {kpis.map((kpi, i) => (
        <div
          key={i}
          style={{
            background: 'var(--bg-surface)',
            padding: '20px 24px',
            borderLeft: kpi.accent ? `3px solid ${kpi.accent}` : '3px solid transparent',
          }}
        >
          <div className="label-caps" style={{ marginBottom: 8 }}>{kpi.label}</div>
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 28,
            fontWeight: 500,
            color: kpi.accent ?? 'var(--text-primary)',
            lineHeight: 1,
            marginBottom: 6,
          }}>
            {kpi.value}
          </div>
          {kpi.sub && (
            <div style={{ fontFamily: 'var(--font-sans)', fontSize: 11, color: 'var(--text-faint)' }}>
              {kpi.sub}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
