'use client'
import { useEffect, useState, useRef } from 'react'

interface TickerItem {
  symbol: string
  label: string
  prefix: string
  value: number | null
  change_percent: number | null
  direction: 'up' | 'down' | 'flat'
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Fallback placeholder items shown while loading
const PLACEHOLDERS: TickerItem[] = [
  { symbol: 'SPX',    label: 'S&P 500',    prefix: '',  value: null, change_percent: null, direction: 'flat' },
  { symbol: 'NDX',    label: 'Nasdaq',     prefix: '',  value: null, change_percent: null, direction: 'flat' },
  { symbol: 'DJIA',   label: 'Dow Jones',  prefix: '',  value: null, change_percent: null, direction: 'flat' },
  { symbol: 'VIX',    label: 'VIX',        prefix: '',  value: null, change_percent: null, direction: 'flat' },
  { symbol: 'GOLD',   label: 'Gold',       prefix: '$', value: null, change_percent: null, direction: 'flat' },
  { symbol: 'WTI',    label: 'WTI Crude',  prefix: '$', value: null, change_percent: null, direction: 'flat' },
  { symbol: 'NIFTY',  label: 'Nifty 50',   prefix: '₹', value: null, change_percent: null, direction: 'flat' },
  { symbol: 'SENSEX', label: 'Sensex',     prefix: '₹', value: null, change_percent: null, direction: 'flat' },
  { symbol: 'NIKKEI', label: 'Nikkei 225', prefix: '¥', value: null, change_percent: null, direction: 'flat' },
  { symbol: 'DAX',    label: 'DAX',        prefix: '€', value: null, change_percent: null, direction: 'flat' },
  { symbol: 'FTSE',   label: 'FTSE 100',   prefix: '£', value: null, change_percent: null, direction: 'flat' },
  { symbol: 'SSE',    label: 'Shanghai',   prefix: '¥', value: null, change_percent: null, direction: 'flat' },
  { symbol: 'BTC',    label: 'Bitcoin',    prefix: '$', value: null, change_percent: null, direction: 'flat' },
  { symbol: 'DXY',    label: 'USD Index',  prefix: '',  value: null, change_percent: null, direction: 'flat' },
]

function formatValue(prefix: string, value: number | null, symbol: string): string {
  if (value === null) return '—'
  if (symbol === 'BTC') return `${prefix}${value.toLocaleString('en-US', { maximumFractionDigits: 0 })}`
  if (['NIFTY', 'SENSEX', 'NIKKEI', 'DAX', 'SSE', 'DJIA', 'SPX', 'NDX'].includes(symbol))
    return `${prefix}${value.toLocaleString('en-US', { maximumFractionDigits: 0 })}`
  return `${prefix}${value.toFixed(2)}`
}

function TickerItem({ item }: { item: TickerItem }) {
  const upColor   = '#4ade80'
  const downColor = '#f87171'
  const flatColor = '#9aacbe'

  const changeColor = item.change_percent === null
    ? flatColor
    : item.change_percent > 0 ? upColor : downColor

  const arrow = item.change_percent === null ? '' : item.change_percent > 0 ? '▲' : '▼'

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 7,
        padding: '0 18px',
        borderRight: '1px solid rgba(255,255,255,0.07)',
        height: '100%',
        flexShrink: 0,
      }}
    >
      {/* Symbol */}
      <span style={{
        color: '#6a8099',
        fontSize: 9,
        fontWeight: 700,
        letterSpacing: '0.12em',
        textTransform: 'uppercase',
        fontFamily: 'var(--font-mono)',
      }}>
        {item.symbol}
      </span>

      {/* Value */}
      <span style={{
        color: '#e2e8f0',
        fontSize: 11,
        fontFamily: 'var(--font-mono)',
        fontWeight: 500,
        letterSpacing: '0.02em',
      }}>
        {formatValue(item.prefix, item.value, item.symbol)}
      </span>

      {/* Change */}
      {item.change_percent !== null && (
        <span style={{
          color: changeColor,
          fontSize: 10,
          fontFamily: 'var(--font-mono)',
          fontWeight: 500,
          display: 'inline-flex',
          alignItems: 'center',
          gap: 2,
        }}>
          <span style={{ fontSize: 8 }}>{arrow}</span>
          {Math.abs(item.change_percent).toFixed(2)}%
        </span>
      )}
    </span>
  )
}

export default function MarketTicker({ market }: { market: any }) {
  const [items, setItems] = useState<TickerItem[]>(PLACEHOLDERS)
  const [capturedAt, setCapturedAt] = useState<string | null>(null)
  const fetchedRef = useRef(false)

  // Fetch from /api/markets/ticker on mount, then refresh every 15 min
  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/markets/ticker`, { cache: 'no-store' })
        if (!res.ok) return
        const data = await res.json()
        if (data.ticker?.length) {
          setItems(data.ticker)
          setCapturedAt(data.captured_at)
        }
      } catch {
        // silently keep placeholders
      }
    }

    load()
    const interval = setInterval(load, 15 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div style={{
      background: '#080f18',
      borderBottom: '1px solid rgba(255,255,255,0.05)',
      height: 30,
      overflow: 'hidden',
      position: 'relative',
      userSelect: 'none',
    }}>
      {/* MARKETS label */}
      <div style={{
        position: 'absolute',
        left: 0, top: 0, bottom: 0,
        zIndex: 10,
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        padding: '0 12px',
        background: '#080f18',
        borderRight: '1px solid rgba(255,255,255,0.07)',
      }}>
        <span style={{
          width: 5, height: 5, borderRadius: '50%',
          background: '#4ade80',
          display: 'inline-block', flexShrink: 0,
          boxShadow: '0 0 4px #4ade80',
        }} />
        <span style={{
          color: '#9aacbe', fontSize: 9, fontWeight: 700,
          letterSpacing: '0.14em', textTransform: 'uppercase',
          fontFamily: 'var(--font-mono)', whiteSpace: 'nowrap',
        }}>
          LIVE
        </span>
      </div>

      {/* Scrolling track */}
      <div style={{ paddingLeft: 80, height: '100%', overflow: 'hidden' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            height: '100%',
            animation: 'ticker-scroll 35s linear infinite',
            whiteSpace: 'nowrap',
          }}
          onMouseEnter={e => (e.currentTarget.style.animationPlayState = 'paused')}
          onMouseLeave={e => (e.currentTarget.style.animationPlayState = 'running')}
        >
          {/* Render twice for seamless loop */}
          {items.map((item, i) => <TickerItem key={`a-${i}`} item={item} />)}
          {items.map((item, i) => <TickerItem key={`b-${i}`} item={item} />)}
        </div>
      </div>

      {/* Right fade */}
      <div style={{
        position: 'absolute', right: 0, top: 0, bottom: 0, width: 48,
        background: 'linear-gradient(to right, transparent, #080f18)',
        pointerEvents: 'none',
      }} />

      {/* Timestamp */}
      {capturedAt && (
        <div style={{
          position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)',
          fontFamily: 'var(--font-mono)', fontSize: 8, color: '#2a3f5a',
          letterSpacing: '0.06em', zIndex: 10,
        }}>
          {new Date(capturedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      )}
    </div>
  )
}
