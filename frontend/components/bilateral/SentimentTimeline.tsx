'use client'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { SentimentPoint } from '@/lib/types'
import { format } from 'date-fns'

interface Props {
  dataA: SentimentPoint[]
  dataB: SentimentPoint[]
  labelA: string
  labelB: string
}

const CustomTooltip = ({ active, payload, label, labelA, labelB }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 4, padding: '10px 14px', boxShadow: 'var(--shadow-md)' }}>
      <p style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)', marginBottom: 6 }}>
        {label ? format(new Date(label), 'MMM d, HH:mm') : ''}
      </p>
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: p.color, marginBottom: 2 }}>
          {p.dataKey === 'a' ? labelA : labelB}: {p.value?.toFixed(3) ?? 'N/A'}
        </p>
      ))}
    </div>
  )
}

export default function SentimentTimeline({ dataA, dataB, labelA, labelB }: Props) {
  const merged: any[] = []
  const mapA = new Map(dataA.map(d => [d.time, d]))
  const mapB = new Map(dataB.map(d => [d.time, d]))
  const allTimes = Array.from(new Set([...dataA, ...dataB].map(d => d.time))).sort()
  for (const t of allTimes) {
    merged.push({ time: t, a: mapA.get(t)?.avg ?? null, b: mapB.get(t)?.avg ?? null })
  }

  if (!merged.length) {
    return (
      <div style={{ textAlign: 'center', padding: '32px 0' }}>
        <p style={{ fontFamily: 'var(--font-sans)', fontSize: 13, color: 'var(--text-faint)' }}>
          Sentiment data will appear after the first scoring run.
        </p>
      </div>
    )
  }

  return (
    <div>
      <div style={{ display: 'flex', gap: 20, marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div style={{ width: 20, height: 2, background: 'var(--navy-mid)' }} />
          <span style={{ fontFamily: 'var(--font-sans)', fontSize: 12, color: 'var(--text-secondary)' }}>{labelA}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div style={{ width: 20, height: 2, background: 'var(--risk-high)' }} />
          <span style={{ fontFamily: 'var(--font-sans)', fontSize: 12, color: 'var(--text-secondary)' }}>{labelB}</span>
        </div>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)', marginLeft: 'auto' }}>72H WINDOW</span>
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={merged} margin={{ top: 4, right: 8, bottom: 4, left: -20 }}>
          <CartesianGrid strokeDasharray="2 4" stroke="var(--bg-muted)" vertical={false} />
          <XAxis
            dataKey="time"
            tickFormatter={t => format(new Date(t), 'HH:mm')}
            tick={{ fontFamily: 'var(--font-mono)', fontSize: 9, fill: 'var(--text-faint)' }}
            axisLine={{ stroke: 'var(--border)' }}
            tickLine={false}
          />
          <YAxis
            domain={[-1, 1]}
            tick={{ fontFamily: 'var(--font-mono)', fontSize: 9, fill: 'var(--text-faint)' }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip labelA={labelA} labelB={labelB} />} />
          <ReferenceLine y={0} stroke="var(--border-strong)" strokeDasharray="3 3" />
          <Line type="monotone" dataKey="a" stroke="var(--navy-mid)" strokeWidth={2} dot={false} connectNulls />
          <Line type="monotone" dataKey="b" stroke="var(--risk-high)" strokeWidth={2} dot={false} connectNulls />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
