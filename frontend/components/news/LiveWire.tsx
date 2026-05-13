'use client'
import { NewsItem } from '@/lib/types'
import { ExternalLink } from 'lucide-react'

interface Props { items: NewsItem[] }

function formatTime(iso: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  const diff = Date.now() - d.getTime()
  const h = Math.floor(diff / 3_600_000)
  const m = Math.floor((diff % 3_600_000) / 60_000)
  if (h > 48) return `${Math.floor(h / 24)}d ago`
  if (h > 0) return `${h}h ago`
  return `${m}m ago`
}

const TOPIC_DOT: Record<string, string> = {
  conflict:  '#9a1a1a',
  sanctions: '#b84a00',
  defence:   '#b84a00',
  cyber:     '#b84a00',
  diplomacy: '#8a6200',
  trade:     '#8a6200',
  energy:    '#8a6200',
  elections: '#1a7a4a',
}

export default function LiveWire({ items }: Props) {
  return (
    <div className="surface-navy" style={{ padding: '20px 0', overflow: 'hidden' }}>
      {/* Header */}
      <div style={{ padding: '0 20px 14px', borderBottom: '1px solid var(--border-navy)', display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#4ade80', display: 'inline-block', flexShrink: 0 }} />
        <span className="section-label" style={{ color: '#9aacbe' }}>Intelligence Wire</span>
      </div>

      {/* Items */}
      <div style={{ maxHeight: 520, overflowY: 'auto', padding: '4px 0' }}>
        {items.length === 0 ? (
          <div style={{ padding: '24px 20px', fontFamily: 'var(--font-sans)', fontSize: 12, color: '#4a6080', textAlign: 'center' }}>
            No updates available
          </div>
        ) : items.map((item, i) => {
          const dot = item.topics[0] ? TOPIC_DOT[item.topics[0]] : '#4a6080'
          return (
            <a
              key={item.id}
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              style={{ textDecoration: 'none', display: 'block' }}
            >
              <div
                style={{
                  padding: '10px 20px',
                  borderBottom: i < items.length - 1 ? '1px solid rgba(255,255,255,0.04)' : 'none',
                  display: 'grid',
                  gridTemplateColumns: '8px 1fr',
                  gap: 10,
                  alignItems: 'flex-start',
                  transition: 'background 0.12s ease',
                  cursor: 'pointer',
                }}
                onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.background = 'rgba(255,255,255,0.03)' }}
                onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.background = 'transparent' }}
              >
                {/* Severity dot */}
                <div style={{ paddingTop: 5 }}>
                  <span style={{ width: 5, height: 5, borderRadius: '50%', background: dot, display: 'inline-block' }} />
                </div>

                {/* Content */}
                <div>
                  <div style={{
                    fontFamily: 'var(--font-sans)', fontSize: 12, fontWeight: 500,
                    color: '#d4d8de', lineHeight: 1.45, marginBottom: 4,
                  }}>
                    {item.title}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: '#4a6080' }}>
                      {formatTime(item.publishedAt)}
                    </span>
                    <span style={{ width: 2, height: 2, borderRadius: '50%', background: '#2a3f5a', display: 'inline-block' }} />
                    <span style={{ fontFamily: 'var(--font-sans)', fontSize: 10, color: '#4a6080' }}>
                      {item.source}
                    </span>
                    {item.flags.slice(0, 2).map((f, fi) => (
                      <span key={fi} style={{ fontSize: 11 }}>{f}</span>
                    ))}
                  </div>
                </div>
              </div>
            </a>
          )
        })}
      </div>
    </div>
  )
}
