'use client'
import { NewsItem } from '@/lib/types'

export interface NewsFilterState {
  region: string
  topic: string
  source: string
  recency: string
}

interface Props {
  filters: NewsFilterState
  onChange: (f: NewsFilterState) => void
  availableSources: string[]
  totalShown: number
  totalAll: number
}

const REGIONS = ['Global', 'Americas', 'Europe', 'Middle East', 'Africa', 'Indo-Pacific']
const TOPICS  = ['conflict', 'diplomacy', 'sanctions', 'defence', 'trade', 'energy', 'elections', 'cyber']
const RECENCY = ['All time', 'Last 6h', 'Last 24h', 'Last 48h']

const pill = (active: boolean): React.CSSProperties => ({
  display: 'inline-flex',
  alignItems: 'center',
  padding: '4px 12px',
  borderRadius: 2,
  fontSize: 11,
  fontWeight: 500,
  fontFamily: 'var(--font-sans)',
  letterSpacing: '0.04em',
  cursor: 'pointer',
  border: '1px solid',
  transition: 'all 0.12s ease',
  background: active ? 'var(--navy)' : 'transparent',
  color: active ? '#ffffff' : 'var(--text-secondary)',
  borderColor: active ? 'var(--navy)' : 'var(--border)',
  textTransform: 'uppercase',
  userSelect: 'none',
})

export default function NewsFilters({ filters, onChange, availableSources, totalShown, totalAll }: Props) {
  const set = (key: keyof NewsFilterState, val: string) =>
    onChange({ ...filters, [key]: filters[key] === val ? '' : val })

  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)',
      padding: '16px 20px',
      marginBottom: 24,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14, flexWrap: 'wrap', gap: 8 }}>
        <span className="section-label">Filter Intelligence Feed</span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>
          {totalShown} of {totalAll} items
        </span>
      </div>

      {/* Region */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 8 }}>
          Region
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {REGIONS.map(r => (
            <span key={r} style={pill(filters.region === r)} onClick={() => set('region', r)}>{r}</span>
          ))}
        </div>
      </div>

      {/* Topic */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 8 }}>
          Topic
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {TOPICS.map(t => (
            <span key={t} style={pill(filters.topic === t)} onClick={() => set('topic', t)}>{t}</span>
          ))}
        </div>
      </div>

      {/* Recency */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 8 }}>
            Recency
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {RECENCY.map(r => (
              <span key={r} style={pill(filters.recency === r)} onClick={() => set('recency', r)}>{r}</span>
            ))}
          </div>
        </div>

        {/* Clear */}
        {(filters.region || filters.topic || filters.source || filters.recency) && (
          <button
            onClick={() => onChange({ region: '', topic: '', source: '', recency: '' })}
            className="btn btn-ghost"
            style={{ fontSize: 11, padding: '4px 10px' }}
          >
            Clear filters
          </button>
        )}
      </div>
    </div>
  )
}
