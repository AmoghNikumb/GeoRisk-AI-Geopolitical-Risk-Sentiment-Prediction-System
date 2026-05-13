'use client'

import { Alert as AlertType } from '@/lib/types'
import { getCountryFlag } from '@/lib/utils'
import { formatDistance } from 'date-fns'
import { X } from 'lucide-react'

interface AlertsWidgetProps {
  alerts: AlertType[]
  unreadCount: number
  onMarkRead: (id: number) => void
  onMarkAllRead: () => void
}

function severityStyle(severity: string): { color: string; bg: string; border: string; label: string } {
  switch (severity) {
    case 'CRITICAL': return { color: 'var(--risk-critical)', bg: 'var(--risk-critical-bg)', border: 'var(--risk-critical-border)', label: 'CRITICAL' }
    case 'WARNING':  return { color: 'var(--risk-high)',     bg: 'var(--risk-high-bg)',     border: 'var(--risk-high-border)',     label: 'WARNING' }
    default:         return { color: 'var(--navy-mid)',      bg: '#eef2f7',                 border: '#c0cfe0',                     label: 'INFO' }
  }
}

export default function AlertsWidget({ alerts, unreadCount, onMarkRead, onMarkAllRead }: AlertsWidgetProps) {
  return (
    <div className="surface" style={{ overflow: 'hidden' }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '16px 20px',
        borderBottom: '1px solid var(--border)',
        background: 'var(--bg-subtle)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontFamily: 'var(--font-sans)', fontWeight: 600, fontSize: 13, color: 'var(--text-primary)' }}>
            Active Alerts
          </span>
          {unreadCount > 0 && (
            <span style={{
              fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 600,
              background: 'var(--risk-critical-bg)', color: 'var(--risk-critical)',
              border: '1px solid var(--risk-critical-border)',
              borderRadius: 2, padding: '1px 6px',
            }}>
              {unreadCount} UNREAD
            </span>
          )}
        </div>
        {unreadCount > 0 && (
          <button onClick={onMarkAllRead} className="btn btn-ghost" style={{ fontSize: 11 }}>
            Mark all read
          </button>
        )}
      </div>

      {/* Alert list */}
      <div style={{ maxHeight: 420, overflowY: 'auto' }}>
        {alerts.length === 0 ? (
          <div style={{ padding: '40px 20px', textAlign: 'center' }}>
            <p style={{ fontFamily: 'var(--font-sans)', fontSize: 13, color: 'var(--text-faint)' }}>
              No active alerts
            </p>
          </div>
        ) : (
          alerts.map((alert, i) => {
            const s = severityStyle(alert.severity)
            const countryA = alert.country_a ?? alert.pair_key?.split('-')[0] ?? ''
            const countryB = alert.country_b ?? alert.pair_key?.split('-')[1] ?? ''

            return (
              <div
                key={alert.id}
                style={{
                  display: 'flex', alignItems: 'flex-start', gap: 12,
                  padding: '14px 20px',
                  borderBottom: i < alerts.length - 1 ? '1px solid var(--bg-subtle)' : 'none',
                  borderLeft: `3px solid ${s.border}`,
                  background: alert.is_read ? 'transparent' : s.bg,
                  opacity: alert.is_read ? 0.65 : 1,
                  transition: 'background 0.12s',
                }}
              >
                {/* Severity badge */}
                <span className="risk-badge" style={{ color: s.color, background: 'transparent', borderColor: s.border, flexShrink: 0, marginTop: 1 }}>
                  {s.label}
                </span>

                {/* Content */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                    {countryA && <span style={{ fontSize: 14 }}>{getCountryFlag(countryA)}</span>}
                    {countryB && <span style={{ fontSize: 14 }}>{getCountryFlag(countryB)}</span>}
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)', letterSpacing: '0.04em' }}>
                      {alert.pair_key}
                    </span>
                  </div>
                  <p style={{ fontFamily: 'var(--font-sans)', fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 4, lineHeight: 1.4 }}>
                    {alert.title}
                  </p>
                  <span style={{ fontFamily: 'var(--font-sans)', fontSize: 11, color: 'var(--text-faint)' }}>
                    {formatDistance(new Date(alert.triggered_at), new Date(), { addSuffix: true })}
                  </span>
                </div>

                {/* Dismiss */}
                {!alert.is_read && (
                  <button
                    onClick={() => onMarkRead(alert.id)}
                    className="btn btn-ghost"
                    style={{ padding: '2px 4px', flexShrink: 0 }}
                    title="Mark as read"
                  >
                    <X size={13} />
                  </button>
                )}
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
