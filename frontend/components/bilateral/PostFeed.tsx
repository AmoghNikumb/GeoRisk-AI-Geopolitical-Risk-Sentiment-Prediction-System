'use client'
import { Post } from '@/lib/types'
import { timeAgo } from '@/lib/utils'

function sentimentColor(score: number | null): string {
  if (score == null) return 'var(--text-faint)'
  if (score < -0.5) return 'var(--risk-critical)'
  if (score < -0.2) return 'var(--risk-high)'
  if (score < 0.2)  return 'var(--risk-moderate)'
  if (score < 0.5)  return 'var(--risk-low)'
  return 'var(--risk-low)'
}

export default function PostFeed({ posts }: { posts: Post[] }) {
  if (!posts?.length) {
    return (
      <div style={{ textAlign: 'center', padding: '24px 0' }}>
        <p style={{ fontFamily: 'var(--font-sans)', fontSize: 13, color: 'var(--text-faint)' }}>
          Posts will appear after the first collection run.
        </p>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {posts.map((p, i) => {
        const score = p.sentiment_score ?? 0
        const color = sentimentColor(p.sentiment_score)

        return (
          <div
            key={i}
            style={{
              padding: '10px 12px',
              background: 'var(--bg-subtle)',
              borderRadius: 4,
              borderLeft: `2px solid ${color}`,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 5 }}>
              <span style={{ fontFamily: 'var(--font-sans)', fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>
                {p.author}
              </span>
              {p.is_politician && (
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--risk-moderate)', background: 'var(--risk-moderate-bg)', border: '1px solid var(--risk-moderate-border)', borderRadius: 2, padding: '1px 5px', letterSpacing: '0.06em' }}>
                  OFFICIAL
                </span>
              )}
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)', marginLeft: 'auto' }}>
                {timeAgo(p.posted_at)}
              </span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color, fontWeight: 600 }}>
                {score > 0 ? '+' : ''}{score.toFixed(2)}
              </span>
            </div>
            <p style={{ fontFamily: 'var(--font-sans)', fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
              {p.text?.slice(0, 240)}{(p.text?.length ?? 0) > 240 ? '...' : ''}
            </p>
          </div>
        )
      })}
    </div>
  )
}
