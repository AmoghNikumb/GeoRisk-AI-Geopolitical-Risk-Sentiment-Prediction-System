import type { Metadata } from 'next'
import './globals.css'
import Navbar from '@/components/layout/Navbar'

export const metadata: Metadata = {
  title: 'GeoRisk Intelligence — Geopolitical Risk Analysis',
  description: 'Institutional-grade geopolitical risk intelligence and monitoring platform',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ background: 'var(--bg-page)', minHeight: '100vh' }}>
        <Navbar />
        <main style={{ maxWidth: 1440, margin: '0 auto', padding: '32px 24px 64px' }}>
          {children}
        </main>
        <footer style={{
          background: 'var(--bg-navy)',
          borderTop: '1px solid var(--border-navy)',
          padding: '32px 24px',
          marginTop: 'auto',
        }}>
          <div style={{ maxWidth: 1440, margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 24 }}>
            <div>
              <div style={{ fontFamily: 'var(--font-sans)', fontWeight: 700, fontSize: 13, color: '#ffffff', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 6 }}>
                GeoRisk Intelligence
              </div>
              <p style={{ fontFamily: 'var(--font-sans)', fontSize: 12, color: '#9aacbe', maxWidth: 280, lineHeight: 1.6 }}>
                Real-time geopolitical risk monitoring and analysis for institutional decision-makers.
              </p>
            </div>
            <div style={{ display: 'flex', gap: 48 }}>
              <div>
                <div style={{ fontFamily: 'var(--font-sans)', fontSize: 10, fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#9aacbe', marginBottom: 10 }}>
                  Platform
                </div>
                {['Dashboard', 'Bilateral Analysis', 'Entities', 'Alerts'].map(l => (
                  <div key={l} style={{ fontFamily: 'var(--font-sans)', fontSize: 12, color: '#6a8099', marginBottom: 6 }}>{l}</div>
                ))}
              </div>
              <div>
                <div style={{ fontFamily: 'var(--font-sans)', fontSize: 10, fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#9aacbe', marginBottom: 10 }}>
                  Data Sources
                </div>
                {['GDELT Events', 'Market Data', 'Social Signals', 'NLP Analysis'].map(l => (
                  <div key={l} style={{ fontFamily: 'var(--font-sans)', fontSize: 12, color: '#6a8099', marginBottom: 6 }}>{l}</div>
                ))}
              </div>
            </div>
            <div style={{ fontFamily: 'var(--font-sans)', fontSize: 11, color: '#4a6080', alignSelf: 'flex-end' }}>
              For analytical purposes only. Not investment advice.
            </div>
          </div>
        </footer>
      </body>
    </html>
  )
}
