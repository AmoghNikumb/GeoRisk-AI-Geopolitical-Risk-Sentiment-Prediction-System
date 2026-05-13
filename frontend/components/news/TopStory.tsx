'use client'
import { NewsItem } from '@/lib/types'
import { ExternalLink } from 'lucide-react'

interface Props { item: NewsItem }

function formatAge(iso: string | null): string {
  if (!iso) return '—'
  const diff = Date.now() - new Date(iso).getTime()
  const h = Math.floor(diff / 3_600_000)
  const m = Math.floor((diff % 3_600_000) / 60_000)
  if (h > 48) return `${Math.floor(h / 24)}d ago`
  if (h > 0) return `${h}h ago`
  return `${m}m ago`
}

export default function TopStory({ item }: Props) {
  return (
    <div className="surface" style={{ overflow: 'hidden', marginBottom: 24 }}>
      <div style={{
        display: 'grid',
        gridTemplateColumns: item.image ? '1fr 360px' : '1fr',
        minHeight: 260,
      }}>
        {/* Content */}
        <div style={{ padding: '36px 36px 32px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            {/* Meta row */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16, flexWrap: 'wrap' }}>
              <span style={{
                fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 600,
                letterSpacing: '0.12em', textTransform: 'uppercase',
                color: 'var(--risk-critical)', background: 'var(--risk-critical-bg)',
                border: '1px solid var(--risk-critical-border)',
                padding: '2px 8px', borderRadius: 'var(--radius-sm)',
              }}>
                Lead Story
              </span>
              <span style={{
                fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: '0.08em',
                textTransform: 'uppercase', color: 'var(--steel)',
                background: 'var(--bg-subtle)', border: '1px solid var(--border)',
                padding: '2px 8px', borderRadius: 'var(--radius-sm)',
              }}>
                {item.region}
              </span>
              {item.flags.slice(0, 3).map((f, i) => (
                <span key={i} style={{ fontSize: 16, lineHeight: 1 }}>{f}</span>
              ))}
            </div>

            {/* Headline */}
            <h2 style={{
              fontFamily: 'var(--font-serif)', fontWeight: 700, fontSize: 26,
              color: 'var(--text-primary)', lineHeight: 1.3, marginBottom: 14,
            }}>
              {item.title}
            </h2>

            {/* Summary */}
            {item.summary && (
              <p style={{
                fontFamily: 'var(--font-sans)', fontSize: 14, color: 'var(--text-secondary)',
                lineHeight: 1.7, marginBottom: 20, maxWidth: 600,
              }}>
                {item.summary}
              </p>
            )}

            {/* Topics */}
            {item.topics.length > 0 && (
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 20 }}>
                {item.topics.slice(0, 4).map(t => (
                  <span key={t} style={{
                    fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: '0.06em',
                    textTransform: 'uppercase', color: 'var(--slate)',
                    border: '1px solid var(--border)', padding: '2px 7px',
                    borderRadius: 'var(--radius-sm)',
                  }}>
                    {t}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span style={{ fontFamily: 'var(--font-sans)', fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>
                {item.source}
              </span>
              <span style={{ width: 3, height: 3, borderRadius: '50%', background: 'var(--border-strong)', display: 'inline-block' }} />
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>
                {formatAge(item.publishedAt)}
              </span>
            </div>
            <a
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-primary"
              style={{ fontSize: 12, gap: 6 }}
            >
              Read full article
              <ExternalLink size={11} />
            </a>
          </div>
        </div>

        {/* Image */}
        {item.image && (
          <div style={{
            backgroundImage: `url(${item.image})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            minHeight: 200,
            position: 'relative',
          }}>
            <div style={{
              position: 'absolute', inset: 0,
              background: 'linear-gradient(to right, rgba(255,255,255,0.08) 0%, transparent 40%)',
            }} />
          </div>
        )}
      </div>
    </div>
  )
}
