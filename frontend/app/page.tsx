'use client'

import React, { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { DashboardData } from '@/lib/types'
import SummaryStats from '@/components/dashboard/SummaryStats'
import RiskHeatmap from '@/components/dashboard/RiskHeatmap'
import MarketIndicators from '@/components/dashboard/MarketIndicators'
import RiskTrendChart from '@/components/dashboard/RiskTrendChart'
import ModelDemoPanel from '@/components/dashboard/PoliticalStatementsPanel'
import MarketTicker from '@/components/layout/MarketTicker'
import { useRouter } from 'next/navigation'
import { RefreshCw } from 'lucide-react'

export default function HomePage() {
  const router = useRouter()
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchDashboard = async () => {
    try {
      setError(null)
      const result = await api.dashboard()
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch dashboard')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchDashboard()
    const interval = setInterval(fetchDashboard, 30000)
    return () => clearInterval(interval)
  }, [])

  const handleRefresh = async () => { setRefreshing(true); await fetchDashboard() }
  const handleSelectPair = (a: string, b: string) => router.push(`/bilateral?a=${a}&b=${b}`)

  if (loading) {
    return (
      <>
        <MarketTicker market={null} />
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ width: 32, height: 32, border: '2px solid var(--border-strong)', borderTopColor: 'var(--navy)', borderRadius: '50%', animation: 'spin 0.8s linear infinite', margin: '0 auto 16px' }} />
            <p style={{ fontFamily: 'var(--font-sans)', fontSize: 13, color: 'var(--text-muted)' }}>Loading intelligence feed...</p>
          </div>
        </div>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </>
    )
  }

  if (error) {
    return (
      <>
        <MarketTicker market={null} />
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
          <div className="surface" style={{ padding: 32, maxWidth: 400, textAlign: 'center' }}>
            <p style={{ fontWeight: 600, color: 'var(--risk-critical)', marginBottom: 8 }}>Connection Error</p>
            <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 20 }}>{error}</p>
            <button onClick={handleRefresh} className="btn btn-primary">Retry</button>
          </div>
        </div>
      </>
    )
  }

  return (
    <div className="fade-in">
      {/* Market Ticker */}
      <div style={{ margin: '-32px -24px 0', marginBottom: 0 }}>
        <MarketTicker market={data?.market ?? null} />
      </div>

      {/* Hero Banner */}
      <div style={{
        margin: '0 -24px',
        position: 'relative',
        height: 280,
        overflow: 'hidden',
        background: 'var(--bg-navy)',
      }}>
        {/* Background image via CSS — Unsplash diplomatic/UN photo */}
        <div style={{
          position: 'absolute', inset: 0,
          backgroundImage: `url('https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=1600&q=80')`,
          backgroundSize: 'cover',
          backgroundPosition: 'center 40%',
          opacity: 0.18,
        }} />
        {/* Overlay gradient */}
        <div style={{
          position: 'absolute', inset: 0,
          background: 'linear-gradient(to right, rgba(13,27,42,0.95) 40%, rgba(13,27,42,0.6) 100%)',
        }} />
        {/* Content */}
        <div style={{ position: 'relative', zIndex: 1, maxWidth: 1440, margin: '0 auto', padding: '0 24px', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 24 }}>
            <div style={{ maxWidth: 560 }}>
              <div className="section-label" style={{ color: '#9aacbe', marginBottom: 12 }}>
                Geopolitical Risk Intelligence Platform
              </div>
              <h1 style={{ fontFamily: 'var(--font-serif)', fontWeight: 700, fontSize: 36, color: '#ffffff', lineHeight: 1.2, marginBottom: 14 }}>
                Global Risk Monitor
              </h1>
              <p style={{ fontFamily: 'var(--font-sans)', fontSize: 14, color: '#9aacbe', lineHeight: 1.7, marginBottom: 24, maxWidth: 440 }}>
                Continuous monitoring of geopolitical tensions, bilateral relations, and market stress indicators across tracked country pairs.
              </p>
              <div style={{ display: 'flex', gap: 10 }}>
                <button onClick={() => router.push('/bilateral')} className="btn btn-primary" style={{ background: 'rgba(255,255,255,0.12)', borderColor: 'rgba(255,255,255,0.2)', color: '#ffffff' }}>
                  Bilateral Analysis
                </button>
                <button onClick={() => router.push('/entities')} className="btn btn-secondary" style={{ borderColor: 'rgba(255,255,255,0.15)', color: '#9aacbe' }}>
                  Entity Monitor
                </button>
              </div>
            </div>

            {/* Live status panel */}
            <div style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 6, padding: '20px 24px', minWidth: 220 }}>
              <div className="section-label" style={{ color: '#9aacbe', marginBottom: 14 }}>System Status</div>
              {[
                { label: 'Data Feed', status: 'Operational' },
                { label: 'NLP Pipeline', status: 'Active' },
                { label: 'Risk Engine', status: 'Running' },
                { label: 'Alert System', status: 'Monitoring' },
              ].map(({ label, status }) => (
                <div key={label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <span style={{ fontFamily: 'var(--font-sans)', fontSize: 12, color: '#9aacbe' }}>{label}</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                    <span style={{ width: 5, height: 5, borderRadius: '50%', background: '#4ade80', display: 'inline-block' }} />
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: '#4ade80', letterSpacing: '0.05em' }}>{status}</span>
                  </span>
                </div>
              ))}
              <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', marginTop: 12, paddingTop: 12 }}>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: '#4a6080' }}>
                  Updated {data?.generated_at ? new Date(data.generated_at).toLocaleTimeString() : '—'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Page content */}
      <div style={{ paddingTop: 32 }}>

        {/* KPI Strip */}
        {data && (
          <div style={{ marginBottom: 32 }}>
            <SummaryStats stats={data.summary} />
          </div>
        )}

        {/* Section: Risk Heatmap */}
        <div style={{ marginBottom: 32 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <div>
              <div className="section-label" style={{ marginBottom: 4 }}>Risk Assessment</div>
              <h2 style={{ fontFamily: 'var(--font-sans)', fontWeight: 600, fontSize: 18, color: 'var(--text-primary)' }}>
                Country Pair Risk Heatmap
              </h2>
            </div>
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="btn btn-secondary"
              style={{ fontSize: 12 }}
            >
              <RefreshCw size={12} style={{ animation: refreshing ? 'spin 0.8s linear infinite' : 'none' }} />
              {refreshing ? 'Refreshing' : 'Refresh'}
            </button>
          </div>
          {data && <RiskHeatmap risks={data.risk_scores} onSelectPair={handleSelectPair} />}
        </div>

        {/* Section: Market Indicators (Full Width) */}
        <div style={{ marginBottom: 32 }}>
          <div style={{ marginBottom: 16 }}>
            <div className="section-label" style={{ marginBottom: 4 }}>Financial Signals</div>
            <h2 style={{ fontFamily: 'var(--font-sans)', fontWeight: 600, fontSize: 18, color: 'var(--text-primary)' }}>
              Market Indicators
            </h2>
            <p style={{ fontFamily: 'var(--font-sans)', fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
              Real-time market data and stress indicators tracking global financial conditions.
            </p>
          </div>
          {data && <MarketIndicators market={data.market} />}
        </div>

        {/* Section: Trend Chart */}
        {data && data.top_risks.length > 0 && (
          <div style={{ marginBottom: 32 }}>
            <div style={{ marginBottom: 16 }}>
              <div className="section-label" style={{ marginBottom: 4 }}>Trend Analysis</div>
              <h2 style={{ fontFamily: 'var(--font-sans)', fontWeight: 600, fontSize: 18, color: 'var(--text-primary)' }}>
                Top Risk Pair Scores
              </h2>
            </div>
            <RiskTrendChart
              data={data.top_risks.slice(0, 5).map((r) => ({
                time: r.pair_key,
                score: r.score,
                classification: r.classification,
              }))}
              title=""
            />
          </div>
        )}

        {/* Section: Political Statements Panel */}
        <div style={{ marginBottom: 32 }}>
          <div style={{ marginBottom: 16 }}>
            <div className="section-label" style={{ marginBottom: 4 }}>NLP Model Inference</div>
            <h2 style={{ fontFamily: 'var(--font-sans)', fontWeight: 600, fontSize: 18, color: 'var(--text-primary)' }}>
              Top Political Statements
            </h2>
            <p style={{ fontFamily: 'var(--font-sans)', fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
              Recent tweets from world leaders — scored by our RoBERTa + LogisticRegression pipeline with affected country detection and intelligence summaries.
            </p>
          </div>
          <ModelDemoPanel />
        </div>

        {/* Footer note */}
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontFamily: 'var(--font-sans)', fontSize: 11, color: 'var(--text-faint)' }}>
            Last updated: {data?.generated_at ? new Date(data.generated_at).toLocaleString() : 'Never'}
          </span>
          <span style={{ fontFamily: 'var(--font-sans)', fontSize: 11, color: 'var(--text-faint)' }}>
            Auto-refresh every 30 seconds
          </span>
        </div>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
