'use client'

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'

interface RiskTrendChartProps {
  data: Array<{ time: string; score: number; classification: string }>
  title: string
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border)',
      borderRadius: 4,
      padding: '10px 14px',
      boxShadow: 'var(--shadow-md)',
    }}>
      <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>{label}</p>
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--navy)', fontWeight: 600 }}>
          Score: {typeof p.value === 'number' ? p.value.toFixed(1) : p.value}
        </p>
      ))}
    </div>
  )
}

export default function RiskTrendChart({ data, title }: RiskTrendChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="surface" style={{ padding: 40, textAlign: 'center' }}>
        <p style={{ fontFamily: 'var(--font-sans)', fontSize: 13, color: 'var(--text-muted)' }}>
          Trend data will appear after multiple scoring runs.
        </p>
      </div>
    )
  }

  return (
    <div className="surface" style={{ overflow: 'hidden' }}>
      <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', background: 'var(--bg-subtle)' }}>
        <span style={{ fontFamily: 'var(--font-sans)', fontWeight: 600, fontSize: 13, color: 'var(--text-primary)' }}>
          {title || 'Risk Score Trends'}
        </span>
      </div>
      <div style={{ padding: '20px 20px 16px' }}>
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={data} margin={{ top: 4, right: 16, left: -16, bottom: 4 }}>
            <CartesianGrid strokeDasharray="2 4" stroke="var(--bg-muted)" vertical={false} />
            <XAxis
              dataKey="time"
              tick={{ fontFamily: 'var(--font-mono)', fontSize: 10, fill: 'var(--text-faint)' }}
              axisLine={{ stroke: 'var(--border)' }}
              tickLine={false}
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fontFamily: 'var(--font-mono)', fontSize: 10, fill: 'var(--text-faint)' }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine y={80} stroke="var(--risk-critical-border)" strokeDasharray="3 3" />
            <ReferenceLine y={60} stroke="var(--risk-high-border)" strokeDasharray="3 3" />
            <ReferenceLine y={35} stroke="var(--risk-moderate-border)" strokeDasharray="3 3" />
            <Line
              type="monotone"
              dataKey="score"
              stroke="var(--navy-mid)"
              strokeWidth={2}
              dot={{ fill: 'var(--navy-mid)', r: 3, strokeWidth: 0 }}
              activeDot={{ r: 5, fill: 'var(--navy)' }}
            />
          </LineChart>
        </ResponsiveContainer>
        <div style={{ display: 'flex', gap: 20, marginTop: 8, paddingLeft: 4 }}>
          {[
            { label: 'Critical (80+)', color: 'var(--risk-critical-border)' },
            { label: 'High (60+)',     color: 'var(--risk-high-border)' },
            { label: 'Moderate (35+)', color: 'var(--risk-moderate-border)' },
          ].map(({ label, color }) => (
            <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
              <div style={{ width: 16, height: 1, background: color, borderTop: `1px dashed ${color}` }} />
              <span style={{ fontFamily: 'var(--font-sans)', fontSize: 10, color: 'var(--text-faint)' }}>{label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
