'use client'
import { AlertTriangle, X } from 'lucide-react'
import { Alert } from '@/lib/types'
import { timeAgo } from '@/lib/utils'
import { useState } from 'react'

export default function AlertBanner({ alerts }: { alerts: Alert[] }) {
  const [dismissed, setDismissed] = useState<number[]>([])
  const visible = alerts.filter(a => !dismissed.includes(a.id)).slice(0, 3)
  if (!visible.length) return null

  return (
    <div className="space-y-2 mb-4 fade-in">
      {visible.map(alert => (
        <div key={alert.id}
          className="flex items-center justify-between px-4 py-2.5 rounded-lg"
          style={{
            background: alert.severity === 'CRITICAL'
              ? 'rgba(239,68,68,0.08)' : 'rgba(249,115,22,0.08)',
            border: `1px solid ${alert.severity === 'CRITICAL'
              ? 'rgba(239,68,68,0.3)' : 'rgba(249,115,22,0.3)'}`,
          }}>
          <div className="flex items-center gap-2">
            <AlertTriangle size={14}
              style={{ color: alert.severity === 'CRITICAL' ? '#ef4444' : '#f97316' }} />
            <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
              {alert.title}
            </span>
            <span className="text-xs mono" style={{ color: 'var(--text-muted)' }}>
              {timeAgo(alert.triggered_at)}
            </span>
          </div>
          <button onClick={() => setDismissed(d => [...d, alert.id])}
            style={{ color: 'var(--text-muted)' }} className="hover:text-white transition-colors">
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  )
}

