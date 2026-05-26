'use client'

import { MarketData } from '@/lib/types'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface MarketIndicatorsProps {
  market: MarketData | null
}

function MarketCard({ label, value, change, prefix = '', suffix = '', description }: {
  label: string
  value: number | null
  change?: number | null
  prefix?: string
  suffix?: string
  description?: string
}) {
  const isPos = (change ?? 0) >= 0
  const changeColor = change == null ? 'var(--text-faint)' : change > 0 ? 'var(--positive)' : 'var(--negative)'
  const TrendIcon = change == null ? Minus : change > 0 ? TrendingUp : TrendingDown

  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border)',
      borderRadius: 8,
      padding: '16px 20px',
      transition: 'border-color 0.2s ease',
    }}
    onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--border-strong)'}
    onMouseLeave={(e) => e.currentTarget.style.borderColor = 'var(--border)'}
    >
      <div style={{ marginBottom: 8 }}>
        <span style={{ 
          fontFamily: 'var(--font-sans)', 
          fontSize: 12, 
          color: 'var(--text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
        }}>
          {label}
        </span>
      </div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 4 }}>
        <span style={{ 
          fontFamily: 'var(--font-mono)', 
          fontSize: 28, 
          fontWeight: 600, 
          color: 'var(--text-primary)',
        }}>
          {value != null ? `${prefix}${value.toFixed(2)}${suffix}` : '—'}
        </span>
        {change != null && (
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: 4,
            background: change > 0 ? 'var(--positive-bg)' : 'var(--negative-bg)',
            border: `1px solid ${change > 0 ? 'var(--positive-border)' : 'var(--negative-border)'}`,
            borderRadius: 4,
            padding: '2px 8px',
          }}>
            <TrendIcon size={12} style={{ color: changeColor }} />
            <span style={{ 
              fontFamily: 'var(--font-mono)', 
              fontSize: 12, 
              fontWeight: 600,
              color: changeColor,
            }}>
              {Math.abs(change).toFixed(2)}%
            </span>
          </div>
        )}
      </div>
      {description && (
        <p style={{ 
          fontFamily: 'var(--font-sans)', 
          fontSize: 11, 
          color: 'var(--text-faint)',
          margin: 0,
          lineHeight: 1.4,
        }}>
          {description}
        </p>
      )}
    </div>
  )
}

function stressLabel(score: number | null): { label: string; color: string } {
  if (score == null) return { label: 'UNKNOWN', color: 'var(--text-faint)' }
  if (score > 0.8) return { label: 'CRITICAL', color: 'var(--risk-critical)' }
  if (score > 0.6) return { label: 'HIGH',     color: 'var(--risk-high)' }
  if (score > 0.4) return { label: 'MODERATE', color: 'var(--risk-moderate)' }
  return               { label: 'LOW',      color: 'var(--risk-low)' }
}

export default function MarketIndicators({ market }: MarketIndicatorsProps) {
  const stress = stressLabel(market?.market_stress_score ?? null)
  const stressPct = (market?.market_stress_score ?? 0) * 100

  return (
    <div className="surface" style={{ overflow: 'hidden' }}>
      {/* Header */}
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid var(--border)',
        background: 'var(--bg-subtle)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <span style={{ fontFamily: 'var(--font-sans)', fontWeight: 600, fontSize: 14, color: 'var(--text-primary)' }}>
          Market Indicators
        </span>
        {market?.captured_at && (
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)' }}>
            Updated {new Date(market.captured_at).toLocaleTimeString()}
          </span>
        )}
      </div>

      {/* Market Cards Grid */}
      <div style={{ 
        padding: '20px',
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: 16,
      }}>
        <MarketCard 
          label="VIX — Fear Index" 
          value={market?.vix ?? null}
          description="Volatility index measuring market fear and uncertainty"
        />
        <MarketCard 
          label="S&P 500" 
          value={market?.sp500 ?? null} 
          change={market?.sp500_change_pct ?? null}
          description="US stock market benchmark index"
        />
        <MarketCard 
          label="WTI Crude Oil" 
          value={market?.crude_oil ?? null} 
          prefix="$"
          description="West Texas Intermediate crude oil price per barrel"
        />
        <MarketCard 
          label="Gold (Spot)" 
          value={market?.gold ?? null} 
          prefix="$"
          description="Gold spot price per troy ounce"
        />
        {market?.dxy != null && (
          <MarketCard 
            label="USD Index (DXY)" 
            value={market.dxy}
            description="US Dollar strength against major currencies"
          />
        )}
      </div>

      {/* Market Stress Index */}
      {market && (
        <div style={{
          padding: '20px',
          borderTop: '1px solid var(--border)',
          background: 'var(--bg-subtle)',
        }}>
          <div style={{ marginBottom: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <div>
                <span style={{ 
                  fontFamily: 'var(--font-sans)', 
                  fontSize: 13, 
                  fontWeight: 600,
                  color: 'var(--text-primary)',
                }}>
                  Market Stress Index
                </span>
                <p style={{ 
                  fontFamily: 'var(--font-sans)', 
                  fontSize: 11, 
                  color: 'var(--text-muted)',
                  margin: '4px 0 0 0',
                }}>
                  Composite indicator of market volatility and risk sentiment
                </p>
              </div>
              <span style={{ 
                fontFamily: 'var(--font-mono)', 
                fontSize: 12, 
                fontWeight: 700, 
                color: stress.color, 
                letterSpacing: '0.06em',
                background: `${stress.color}15`,
                border: `1px solid ${stress.color}40`,
                borderRadius: 4,
                padding: '4px 12px',
              }}>
                {stress.label}
              </span>
            </div>
          </div>
          
          {/* Progress bar */}
          <div style={{
            height: 8,
            background: 'var(--bg-surface)',
            borderRadius: 4,
            overflow: 'hidden',
            border: '1px solid var(--border)',
          }}>
            <div style={{ 
              width: `${stressPct}%`, 
              height: '100%',
              background: stress.color,
              transition: 'width 0.5s ease',
            }} />
          </div>
          
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6 }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)' }}>
              0% Low
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 600, color: stress.color }}>
              {stressPct.toFixed(1)}%
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)' }}>
              100% Critical
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
