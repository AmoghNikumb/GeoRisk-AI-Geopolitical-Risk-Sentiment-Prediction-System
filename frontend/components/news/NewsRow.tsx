'use client'
import { NewsItem } from '@/lib/types'
import { ExternalLink } from 'lucide-react'

interface Props { item: NewsItem; index: number }

function formatTime(iso: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  const diff = Date.now() - d.getTime()
  const h = Math.floor(diff / 3_600_000)
  const m = Math.floor((diff % 3_600_000) / 60_000)
  if (h > 48) return `${Math.floor(h / 24)}d`
  if (h > 0) return `${h}h`
  return `${m}m`
}

const TOPIC_SEVERITY: Record<string, { color: string; bg: string; border: string }> = {
  conflict:   { color: 'var(--risk-critical)', bg: 'var(--risk-critical-bg)', border: 'var(--risk-critical-border)' },
  sanctions:  { color: 'var(--risk-high)',     bg: 'var(--risk-high-bg)',     border: 'var(--risk-high-border)' },
  defence:    { color: 'var(--risk-high)',     bg: 'var(--risk-high-bg)',     border: 'var(--risk-high-border)' },
  diplomacy:  { color: 'var(--risk-moderate)', bg: 'var(--risk-moderate-bg)', border: 'var(--risk-moderate-border)' },
  trade:      { color: 'var(--risk-moderate)', bg: 'var(--risk-moderate-bg)', border: 'var(--risk-moderate-border)' },
  energy:     { color: 'var(--risk-moderate)', bg: 'var(--risk-moderate-bg)', border: 'var(--risk-moderate-border)' },
  elections:  { color: 'var(--risk-low)',      bg: 'var(--risk-low-bg)',      border: 'var(--risk-low-border)' },
  cyber:      { color: 'var(--risk-high)',     bg: 'var(--risk-high-bg)',     border: 'var(--risk-high-border)' },
}

export default function NewsRow({ item, index }: Props) {
  const primaryTopic = item.topics[0]
  const severity = primaryTopic ? TOPIC_SEVERITY[primaryTopic] : null

  return (
    <a
      href={item.url}
      target="_blank"
      rel="noopener noreferrer"
      style={{ textDecoration: 'none', display: 'block' }}
    >
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '52px 1fr auto',
          gap: 14,
          alignItems: 'flex-start',
          padding: '12px 0',
          borderBottom: '1px solid var(--border)',
          transition: 'background 0.12s ease',
          cursor: 'pointer',
          borderRadius: 2,
        }}
        onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.background = 'var(--bg-subtle)' }}
        onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.background = 'transparent' }}
      >
        {/* Timestamp */}
        <div style={{ textAlign: 'right', paddingTop: 2 }}>
          <span style={{
            fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-faint)',
            letterSpacing: '0.04em',
          }}>
            {formatTime(item.publishedAt)}
          </span>
        </div>

        {/* Content */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4, flexWrap: 'wrap' }}>
            {severity && primaryTopic && (
              <span style={{
                fontFamily: 'var(--font-mono)', fontSize: 9, fontWeight: 600,
                letterSpacing: '0.1em', textTransform: 'uppercase',
                color: severity.color, background: severity.bg,
                border: `1px solid ${severity.border}`,
                padding: '1px 6px', borderRadius: 'var(--radius-sm)',
              }}>
                {primaryTopic}
              </span>
            )}
            {item.flags.slice(0, 2).map((f, i) => (
              <span key={i} style={{ fontSize: 12 }}>{f}</span>
            ))}
            <span style={{
              fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-faint)',
              letterSpacing: '0.06em', textTransform: 'uppercase',
            }}>
              {item.region}
            </span>
          </div>
          <div style={{
            fontFamily: 'var(--font-sans)', fontSize: 13, fontWeight: 500,
            color: 'var(--text-primary)', lineHeight: 1.4,
          }}>
            {item.title}
          </div>
          <div style={{ fontFamily: 'var(--font-sans)', fontSize: 11, color: 'var(--text-muted)', marginTop: 3 }}>
            {item.source}
          </div>
        </div>

        {/* Link icon */}
        <div style={{ paddingTop: 3 }}>
          <ExternalLink size={11} color="var(--text-faint)" />
        </div>
      </div>
    </a>
  )
}
