'use client'

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from '@/lib/api'
import { NewsItem, NewsResponse } from '@/lib/types'
import TopStory from '@/components/news/TopStory'
import NewsCard from '@/components/news/NewsCard'
import NewsRow from '@/components/news/NewsRow'
import LiveWire from '@/components/news/LiveWire'
import NewsFilters, { NewsFilterState } from '@/components/news/NewsFilters'
import NewsSkeleton from '@/components/news/NewsSkeleton'
import { RefreshCw } from 'lucide-react'

const REFRESH_INTERVAL_MS = 20 * 60 * 1000   // 20 min — matches backend cache TTL

function applyClientFilters(items: NewsItem[], filters: NewsFilterState): NewsItem[] {
  let out = items
  if (filters.region) out = out.filter(i => i.region.toLowerCase() === filters.region.toLowerCase())
  if (filters.topic)  out = out.filter(i => i.topics.map(t => t.toLowerCase()).includes(filters.topic.toLowerCase()))
  if (filters.recency && filters.recency !== 'All time') {
    const hours = filters.recency === 'Last 6h' ? 6 : filters.recency === 'Last 24h' ? 24 : 48
    const cutoff = Date.now() - hours * 3_600_000
    out = out.filter(i => i.publishedAt ? new Date(i.publishedAt).getTime() > cutoff : false)
  }
  return out
}

export default function NewsPage() {
  const [data, setData] = useState<NewsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState<NewsFilterState>({ region: '', topic: '', source: '', recency: '' })
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null)

  const fetchNews = useCallback(async (force = false) => {
    try {
      setError(null)
      const result = await api.news({ force_refresh: force, limit: 120 })
      setData(result)
      setLastRefreshed(new Date())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch news feed')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    fetchNews()
    const interval = setInterval(() => fetchNews(), REFRESH_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [fetchNews])

  const handleRefresh = () => { setRefreshing(true); fetchNews(true) }

  const allItems = data?.items ?? []
  const filtered = useMemo(() => applyClientFilters(allItems, filters), [allItems, filters])

  // Partition: featured top story, next 6 as cards, rest as rows
  const topStory   = filtered.find(i => i.featured) ?? filtered[0] ?? null
  const cardItems  = filtered.filter(i => i !== topStory).slice(0, 6)
  const rowItems   = filtered.filter(i => i !== topStory).slice(6)
  const wireItems  = allItems.slice(0, 20)   // live wire always shows latest unfiltered

  // ── Loading ──────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="fade-in">
        <PageHeader refreshing={false} lastRefreshed={null} onRefresh={() => {}} />
        <NewsSkeleton />
      </div>
    )
  }

  // ── Error ─────────────────────────────────────────────────────────────────
  if (error) {
    return (
      <div className="fade-in">
        <PageHeader refreshing={refreshing} lastRefreshed={lastRefreshed} onRefresh={handleRefresh} />
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '40vh' }}>
          <div className="surface" style={{ padding: 32, maxWidth: 420, textAlign: 'center' }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--risk-critical)', marginBottom: 10 }}>
              Feed Unavailable
            </div>
            <p style={{ fontFamily: 'var(--font-sans)', fontSize: 13, color: 'var(--text-muted)', marginBottom: 20, lineHeight: 1.6 }}>
              {error}
            </p>
            <button onClick={handleRefresh} className="btn btn-primary">Retry</button>
          </div>
        </div>
      </div>
    )
  }

  // ── Empty ─────────────────────────────────────────────────────────────────
  if (filtered.length === 0) {
    return (
      <div className="fade-in">
        <PageHeader refreshing={refreshing} lastRefreshed={lastRefreshed} onRefresh={handleRefresh} />
        <NewsFilters
          filters={filters}
          onChange={setFilters}
          availableSources={data?.sources ?? []}
          totalShown={0}
          totalAll={allItems.length}
        />
        <div style={{ textAlign: 'center', padding: '64px 0' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 10 }}>
            No results
          </div>
          <p style={{ fontFamily: 'var(--font-sans)', fontSize: 13, color: 'var(--text-faint)' }}>
            No stories match the current filters. Try adjusting your selection.
          </p>
        </div>
      </div>
    )
  }

  // ── Main render ───────────────────────────────────────────────────────────
  return (
    <div className="fade-in">
      <PageHeader refreshing={refreshing} lastRefreshed={lastRefreshed} onRefresh={handleRefresh} />

      {/* Filters */}
      <NewsFilters
        filters={filters}
        onChange={setFilters}
        availableSources={data?.sources ?? []}
        totalShown={filtered.length}
        totalAll={allItems.length}
      />

      {/* Top Story */}
      {topStory && <TopStory item={topStory} />}

      {/* Two-column layout: main + right rail */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 24, alignItems: 'flex-start' }}>

        {/* Main column */}
        <div>
          {/* Card grid */}
          {cardItems.length > 0 && (
            <div style={{ marginBottom: 32 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                <div className="section-label">Latest Developments</div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
                {cardItems.map(item => (
                  <NewsCard key={item.id} item={item} />
                ))}
              </div>
            </div>
          )}

          {/* Row list */}
          {rowItems.length > 0 && (
            <div>
              <div style={{ marginBottom: 12 }}>
                <div className="section-label">Further Reporting</div>
              </div>
              <div>
                {rowItems.map((item, i) => (
                  <NewsRow key={item.id} item={item} index={i} />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right rail */}
        <div style={{ position: 'sticky', top: 24 }}>
          <div style={{ marginBottom: 12 }}>
            <div className="section-label" style={{ marginBottom: 4 }}>Situation Room</div>
          </div>
          <LiveWire items={wireItems} />

          {/* Source list */}
          <div className="surface" style={{ marginTop: 16, padding: '16px 18px' }}>
            <div className="section-label" style={{ marginBottom: 12 }}>Active Sources</div>
            {(data?.sources ?? []).map(s => (
              <div key={s} style={{
                fontFamily: 'var(--font-sans)', fontSize: 12, color: 'var(--text-secondary)',
                padding: '5px 0', borderBottom: '1px solid var(--bg-subtle)',
                display: 'flex', alignItems: 'center', gap: 6,
              }}>
                <span style={{ width: 4, height: 4, borderRadius: '50%', background: 'var(--border-strong)', display: 'inline-block', flexShrink: 0 }} />
                {s}
              </div>
            ))}
            <div style={{ fontFamily: 'var(--font-sans)', fontSize: 11, color: 'var(--text-faint)', marginTop: 10 }}>
              {data?.sources.length ?? 0} sources monitored
            </div>
          </div>
        </div>
      </div>

      {/* Footer strip */}
      <div style={{ borderTop: '1px solid var(--border)', paddingTop: 16, marginTop: 32, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
        <span style={{ fontFamily: 'var(--font-sans)', fontSize: 11, color: 'var(--text-faint)' }}>
          Feed refreshed: {data?.fetched_at ? new Date(data.fetched_at).toLocaleString() : '—'}
          {data?.cached && <span style={{ marginLeft: 6, color: 'var(--text-faint)' }}>(cached)</span>}
        </span>
        <span style={{ fontFamily: 'var(--font-sans)', fontSize: 11, color: 'var(--text-faint)' }}>
          For analytical purposes only. Source articles are third-party content.
        </span>
      </div>
    </div>
  )
}

// ── Sub-component: page header ────────────────────────────────────────────────
function PageHeader({
  refreshing,
  lastRefreshed,
  onRefresh,
}: {
  refreshing: boolean
  lastRefreshed: Date | null
  onRefresh: () => void
}) {
  return (
    <>
      {/* Hero */}
      <div style={{
        margin: '-32px -24px 0',
        background: 'var(--bg-navy)',
        borderBottom: '1px solid var(--border-navy)',
        padding: '40px 24px 36px',
        marginBottom: 28,
        position: 'relative',
        overflow: 'hidden',
      }}>
        {/* Background image */}
        <div style={{
          position: 'absolute', inset: 0,
          backgroundImage: `url('/news-bg.jpg')`,
          backgroundSize: 'cover',
          backgroundPosition: 'center 40%',
          opacity: 0.10,
        }} />
        <div style={{ position: 'relative', zIndex: 1, maxWidth: 1440, margin: '0 auto' }}>
          <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
            <div>
              <div className="section-label" style={{ color: '#9aacbe', marginBottom: 10 }}>
                Intelligence Desk
              </div>
              <h1 style={{
                fontFamily: 'var(--font-serif)', fontWeight: 700, fontSize: 32,
                color: '#ffffff', lineHeight: 1.2, marginBottom: 10,
              }}>
                Daily Geopolitical News
              </h1>
              <p style={{
                fontFamily: 'var(--font-sans)', fontSize: 13, color: '#9aacbe',
                lineHeight: 1.7, maxWidth: 520,
              }}>
                Aggregated live feed of global developments from institutional, policy, and strategic affairs sources.
                Updated every 20 minutes.
              </p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              {lastRefreshed && (
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: '#4a6080', letterSpacing: '0.06em' }}>
                  Updated {lastRefreshed.toLocaleTimeString()}
                </span>
              )}
              <button
                onClick={onRefresh}
                disabled={refreshing}
                className="btn btn-secondary"
                style={{ fontSize: 12, borderColor: 'rgba(255,255,255,0.15)', color: '#9aacbe' }}
              >
                <RefreshCw size={12} style={{ animation: refreshing ? 'spin 0.8s linear infinite' : 'none' }} />
                {refreshing ? 'Refreshing' : 'Refresh feed'}
              </button>
            </div>
          </div>
        </div>
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </>
  )
}

