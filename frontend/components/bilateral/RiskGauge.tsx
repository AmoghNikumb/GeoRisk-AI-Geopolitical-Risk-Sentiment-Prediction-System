'use client'
import { RiskLevel } from '@/lib/types'

function getRiskStyle(level: RiskLevel): { color: string; label: string } {
  switch (level) {
    case 'LOW':      return { color: 'var(--risk-low)',      label: 'LOW RISK' }
    case 'MODERATE': return { color: 'var(--risk-moderate)', label: 'MODERATE' }
    case 'HIGH':     return { color: 'var(--risk-high)',     label: 'HIGH RISK' }
    case 'CRITICAL': return { color: 'var(--risk-critical)', label: 'CRITICAL' }
    default:         return { color: 'var(--text-faint)',    label: 'UNKNOWN' }
  }
}

export default function RiskGauge({ score, level }: { score: number | null; level: RiskLevel }) {
  const s = score ?? 0
  const { color, label } = getRiskStyle(level)
  const circumference = 2 * Math.PI * 52
  const offset = circumference - (s / 100) * circumference

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '8px 0' }}>
      <div style={{ position: 'relative', width: 140, height: 140 }}>
        <svg width="140" height="140" viewBox="0 0 120 120" style={{ transform: 'rotate(-90deg)' }}>
          {/* Track */}
          <circle cx="60" cy="60" r="52" fill="none" stroke="var(--bg-muted)" strokeWidth="6" />
          {/* Progress */}
          <circle
            cx="60" cy="60" r="52"
            fill="none"
            stroke={color}
            strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ transition: 'stroke-dashoffset 1s cubic-bezier(0.4,0,0.2,1)' }}
          />
        </svg>
        <div style={{
          position: 'absolute', inset: 0,
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, fontSize: 30, color: 'var(--text-primary)', lineHeight: 1 }}>
            {s.toFixed(0)}
          </span>
          <span style={{ fontFamily: 'var(--font-sans)', fontSize: 10, color: 'var(--text-faint)', marginTop: 2 }}>/ 100</span>
        </div>
      </div>

      <span className="risk-badge" style={{
        marginTop: 12,
        color,
        background: 'transparent',
        borderColor: color,
        fontSize: 10,
        letterSpacing: '0.1em',
      }}>
        {label}
      </span>
    </div>
  )
}
