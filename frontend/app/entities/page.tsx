'use client'
import { useState } from 'react'
import { useEntities } from '@/hooks/useDashboard'
import PostFeed from '@/components/bilateral/PostFeed'
import { COUNTRY_NAMES, getCountryFlag, formatSentiment } from '@/lib/utils'

const TRACKED_COUNTRIES = ['US', 'CN', 'RU', 'IN', 'PK', 'GB', 'DE', 'FR',
  'JP', 'KR', 'IR', 'IL', 'SA', 'TR', 'UA']

function sentimentColor(score: number | null): string {
  if (score == null) return 'var(--text-faint)'
  if (score < -0.3) return 'var(--risk-critical)'
  if (score < 0)    return 'var(--risk-high)'
  if (score < 0.3)  return 'var(--risk-moderate)'
  return 'var(--risk-low)'
}

export default function EntitiesPage() {
  const [selected, setSelected] = useState('US')
  const { data, loading } = useEntities(selected)
  const countryName = COUNTRY_NAMES[selected] ?? selected

  return (
    <div className="fade-in">
      {/* Page header */}
      <div style={{
        margin: '-32px -24px 32px',
        background: 'var(--bg-navy)',
        padding: '32px 24px',
        position: 'relative',
        overflow: 'hidden',
      }}>
        <div style={{
          position: 'absolute', inset: 0,
          backgroundImage: `url('https://images.unsplash.com/photo-1568992687947-868a62a9f521?w=1600&q=80')`,
          backgroundSize: 'cover', backgroundPosition: 'center',
          opacity: 0.08,
        }} />
        <div style={{ position: 'relative', zIndex: 1, maxWidth: 1440, margin: '0 auto' }}>
          <div className="section-label" style={{ color: '#9aacbe', marginBottom: 8 }}>Intelligence Dossier</div>
          <h1 style={{ fontFamily: 'var(--font-serif)', fontWeight: 700, fontSize: 28, color: '#ffffff', marginBottom: 6 }}>
            Political Entities Monitor
          </h1>
          <p style={{ fontFamily: 'var(--font-sans)', fontSize: 13, color: '#9aacbe', maxWidth: 480 }}>
            Track key political figures, their public statements, and sentiment signals across monitored countries.
          </p>
        </div>
      </div>

      {/* Country selector */}
      <div style={{ marginBottom: 28 }}>
        <div className="section-label" style={{ marginBottom: 12 }}>Select Country</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {TRACKED_COUNTRIES.map(code => {
            const active = selected === code
            return (
              <button
                key={code}
                onClick={() => setSelected(code)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 6,
                  padding: '6px 12px', borderRadius: 3,
                  fontFamily: 'var(--font-sans)', fontSize: 12, fontWeight: active ? 600 : 400,
                  background: active ? 'var(--bg-navy)' : 'var(--bg-surface)',
                  color: active ? '#ffffff' : 'var(--text-secondary)',
                  border: `1px solid ${active ? 'var(--border-navy)' : 'var(--border)'}`,
                  cursor: 'pointer', transition: 'all 0.12s',
                }}
              >
                <span style={{ fontSize: 16 }}>{getCountryFlag(code)}</span>
                <span>{COUNTRY_NAMES[code] ?? code}</span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 200 }}>
          <div style={{ width: 28, height: 28, border: '2px solid var(--border)', borderTopColor: 'var(--navy)', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
        </div>
      )}

      {/* Content */}
      {!loading && data && (
        <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: 24 }}>

          {/* Politicians dossier */}
          <div>
            <div style={{ marginBottom: 14 }}>
              <div className="section-label" style={{ marginBottom: 4 }}>Tracked Officials</div>
              <h2 style={{ fontFamily: 'var(--font-sans)', fontWeight: 600, fontSize: 16, color: 'var(--text-primary)' }}>
                {getCountryFlag(selected)} {countryName}
              </h2>
            </div>

            {data.politicians?.length === 0 ? (
              <div className="surface" style={{ padding: 32, textAlign: 'center' }}>
                <p style={{ fontFamily: 'var(--font-sans)', fontSize: 13, color: 'var(--text-faint)' }}>
                  No politicians tracked for {countryName}.
                </p>
              </div>
            ) : (
              <div className="surface" style={{ overflow: 'hidden' }}>
                {/* Table header */}
                <div style={{
                  display: 'grid', gridTemplateColumns: '1fr 80px 60px',
                  padding: '10px 16px', borderBottom: '1px solid var(--border)',
                  background: 'var(--bg-subtle)',
                }}>
                  {['Official', 'Sentiment', 'Influence'].map(h => (
                    <div key={h} className="label-caps">{h}</div>
                  ))}
                </div>

                {data.politicians.map((pol: any, i: number) => {
                  const sentColor = sentimentColor(pol.avg_sentiment_72h)
                  return (
                    <div
                      key={pol.id}
                      style={{
                        display: 'grid', gridTemplateColumns: '1fr 80px 60px',
                        padding: '14px 16px',
                        borderBottom: i < data.politicians.length - 1 ? '1px solid var(--bg-subtle)' : 'none',
                        alignItems: 'center',
                      }}
                    >
                      {/* Name + role */}
                      <div>
                        <div style={{ fontFamily: 'var(--font-sans)', fontWeight: 600, fontSize: 13, color: 'var(--text-primary)', marginBottom: 2 }}>
                          {pol.name}
                        </div>
                        <div style={{ fontFamily: 'var(--font-sans)', fontSize: 11, color: 'var(--text-muted)', marginBottom: 2 }}>
                          {pol.title}
                        </div>
                        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--steel)' }}>
                          {pol.twitter_handle}
                        </div>
                      </div>

                      {/* Sentiment */}
                      <div>
                        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 14, fontWeight: 600, color: sentColor }}>
                          {formatSentiment(pol.avg_sentiment_72h)}
                        </div>
                        <div style={{ fontFamily: 'var(--font-sans)', fontSize: 10, color: 'var(--text-faint)', marginTop: 1 }}>72h avg</div>
                      </div>

                      {/* Influence */}
                      <div>
                        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-secondary)', marginBottom: 4 }}>
                          {(pol.influence_weight * 100).toFixed(0)}%
                        </div>
                        <div className="score-bar" style={{ width: 40 }}>
                          <div className="score-bar-fill" style={{ width: `${pol.influence_weight * 100}%`, background: 'var(--navy-mid)' }} />
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {/* Hostile posts */}
          <div>
            <div style={{ marginBottom: 14 }}>
              <div className="section-label" style={{ marginBottom: 4 }}>Signal Feed</div>
              <h2 style={{ fontFamily: 'var(--font-sans)', fontWeight: 600, fontSize: 16, color: 'var(--text-primary)' }}>
                Most Hostile Posts — {countryName} (72H)
              </h2>
            </div>
            <div className="surface" style={{ padding: 20, maxHeight: 640, overflowY: 'auto' }}>
              <PostFeed posts={data.inflammatory_posts} />
            </div>
          </div>
        </div>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
