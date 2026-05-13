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

const REGION_COLORS: Record<string, string> = {
  Europe: '#1e3a5f',
  'Middle East': '#5a3010',
  'Indo-Pacific': '#0a3a2a',
  Americas: '#1a1a4a',
  Africa: '#3a2a0a',
  Global: '#2a3a4a',
}

export default function NewsCard({ item }: Props) {
  const regionColor = REGION_COLORS[item.region] || REGION_COLORS.Global

  return (
    <a
      href={item.url}
      target="_blank"
      rel="noopener noreferrer"
      style={{ textDecoration: 'none', display: 'block' }}
    >
      <div
        className="surface"
        style={{
          overflow: 'hidden',
          transition: 'box-shadow 0.15s ease, transform 0.15s ease',
          cursor: 'pointer',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
        }}
        onMouseEnter={e => {
          const el = e.currentTarget as HTMLDivElement
          el.style.boxShadow = 'var(--shadow-md)'
          el.style.transform = 'translateY(-1px)'
        }}
        onMouseLeave={e => {
          const el = e.currentTarget as HTMLDivElement
          el.style.boxShadow = 'var(--shadow-sm)'
          el.style.transform = 'translateY(0)'
        }}
      >
        {/* Image or region color bar */}
        {item.image ? (
          <div style={{
            height: 148,
            backgroundImage: `url(${item.image})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            flexShrink: 0,
          }} />
        ) : (
          <div style={{
            height: 4,
            background: regionColor,
            flexShrink: 0,
          }} />
        )}

        {/* Body */}
        <div style={{ padding: '16px 18px 18px', flex: 1, display: 'flex', flexDirection: 'column' }}>
          {/* Tags */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10, flexWrap: 'wrap' }}>
            <span style={{
              fontFamily: 'var(--font-mono)', fontSize: 9, fontWeight: 600,
              letterSpacing: '0.1em', textTransform: 'uppercase',
              color: 'var(--steel)', border: '1px solid var(--border)',
              padding: '1px 6px', borderRadius: 'var(--radius-sm)',
            }}>
              {item.region}
            </span>
            {item.flags.slice(0, 2).map((f, i) => (
              <span key={i} style={{ fontSize: 13 }}>{f}</span>
            ))}
            {item.topics.slice(0, 1).map(t => (
              <span key={t} style={{
                fontFamily: 'var(--font-mono)', fontSize: 9, letterSpacing: '0.08em',
                textTransform: 'uppercase', color: 'var(--text-muted)',
                border: '1px solid var(--bg-muted)', padding: '1px 6px',
                borderRadius: 'var(--radius-sm)',
              }}>
                {t}
              </span>
            ))}
          </div>

          {/* Headline */}
          <h3 style={{
            fontFamily: 'var(--font-sans)', fontWeight: 600, fontSize: 14,
            color: 'var(--text-primary)', lineHeight: 1.45, marginBottom: 8,
            flex: 1,
          }}>
            {item.title}
          </h3>

          {/* Excerpt */}
          {item.summary && (
            <p style={{
              fontFamily: 'var(--font-sans)', fontSize: 12, color: 'var(--text-muted)',
              lineHeight: 1.6, marginBottom: 14,
              display: '-webkit-box',
              WebkitLineClamp: 3,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            } as React.CSSProperties}>
              {item.summary}
            </p>
          )}

          {/* Footer */}
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            borderTop: '1px solid var(--bg-subtle)', paddingTop: 10, marginTop: 'auto',
          }}>
            <div>
              <div style={{ fontFamily: 'var(--font-sans)', fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 1 }}>
                {item.source}
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)' }}>
                {formatAge(item.publishedAt)}
              </div>
            </div>
            <ExternalLink size={12} color="var(--text-faint)" />
          </div>
        </div>
      </div>
    </a>
  )
}
