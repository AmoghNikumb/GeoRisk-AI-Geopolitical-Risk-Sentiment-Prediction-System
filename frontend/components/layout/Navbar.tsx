'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

const links = [
  { href: '/',       label: 'Dashboard' },
  { href: '/bilateral', label: 'Bilateral Analysis' },
  { href: '/entities',  label: 'Entities' },
  { href: '/news',      label: 'Daily Geopolitical News' },
]

export default function Navbar() {
  const path = usePathname()

  return (
    <header style={{ background: 'var(--bg-navy)', borderBottom: '1px solid var(--border-navy)' }}>
      <div style={{ maxWidth: 1440, margin: '0 auto', padding: '0 24px', height: 56, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>

        {/* Logo */}
        <Link href="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 28, height: 28, background: 'rgba(255,255,255,0.08)',
            border: '1px solid rgba(255,255,255,0.12)', borderRadius: 4,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <circle cx="7" cy="7" r="6" stroke="#9aacbe" strokeWidth="1.2" />
              <path d="M1 7h12M7 1c-2 2-2 8 0 12M7 1c2 2 2 8 0 12" stroke="#9aacbe" strokeWidth="1.2" />
            </svg>
          </div>
          <div>
            <span style={{ fontFamily: 'var(--font-sans)', fontWeight: 700, fontSize: 14, color: '#ffffff', letterSpacing: '0.02em' }}>
              GEORISK
            </span>
            <span style={{ fontFamily: 'var(--font-sans)', fontWeight: 300, fontSize: 14, color: '#9aacbe', letterSpacing: '0.02em', marginLeft: 2 }}>
              INTELLIGENCE
            </span>
          </div>
        </Link>

        {/* Nav */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {links.map(({ href, label }) => {
            const active = path === href
            return (
              <Link
                key={href}
                href={href}
                className={`nav-link${active ? ' active' : ''}`}
              >
                {label}
              </Link>
            )
          })}
        </nav>

        {/* Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#4ade80', display: 'inline-block' }} />
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: '#9aacbe', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
            Live Feed
          </span>
        </div>
      </div>
    </header>
  )
}
