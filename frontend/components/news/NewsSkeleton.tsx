export default function NewsSkeleton() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
      {/* Top story skeleton */}
      <div className="surface" style={{ marginBottom: 24, overflow: 'hidden' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', minHeight: 260 }}>
          <div style={{ padding: '32px 32px 32px 32px' }}>
            <div style={{ width: 80, height: 10, background: 'var(--bg-muted)', borderRadius: 2, marginBottom: 16 }} />
            <div style={{ width: '90%', height: 22, background: 'var(--bg-muted)', borderRadius: 2, marginBottom: 10 }} />
            <div style={{ width: '70%', height: 22, background: 'var(--bg-muted)', borderRadius: 2, marginBottom: 20 }} />
            <div style={{ width: '100%', height: 12, background: 'var(--bg-subtle)', borderRadius: 2, marginBottom: 8 }} />
            <div style={{ width: '85%', height: 12, background: 'var(--bg-subtle)', borderRadius: 2, marginBottom: 8 }} />
            <div style={{ width: '60%', height: 12, background: 'var(--bg-subtle)', borderRadius: 2 }} />
          </div>
          <div style={{ background: 'var(--bg-muted)' }} />
        </div>
      </div>

      {/* Card skeletons */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 24 }}>
        {[1, 2, 3].map(i => (
          <div key={i} className="surface" style={{ padding: 20 }}>
            <div style={{ width: '100%', height: 140, background: 'var(--bg-muted)', borderRadius: 4, marginBottom: 14 }} />
            <div style={{ width: 60, height: 10, background: 'var(--bg-muted)', borderRadius: 2, marginBottom: 10 }} />
            <div style={{ width: '95%', height: 14, background: 'var(--bg-muted)', borderRadius: 2, marginBottom: 6 }} />
            <div style={{ width: '75%', height: 14, background: 'var(--bg-muted)', borderRadius: 2, marginBottom: 12 }} />
            <div style={{ width: '100%', height: 11, background: 'var(--bg-subtle)', borderRadius: 2, marginBottom: 5 }} />
            <div style={{ width: '80%', height: 11, background: 'var(--bg-subtle)', borderRadius: 2 }} />
          </div>
        ))}
      </div>

      {/* Row skeletons */}
      {[1, 2, 3, 4, 5].map(i => (
        <div key={i} style={{ padding: '14px 0', borderBottom: '1px solid var(--border)', display: 'flex', gap: 16, alignItems: 'flex-start' }}>
          <div style={{ width: 48, height: 10, background: 'var(--bg-muted)', borderRadius: 2, flexShrink: 0, marginTop: 2 }} />
          <div style={{ flex: 1 }}>
            <div style={{ width: '80%', height: 13, background: 'var(--bg-muted)', borderRadius: 2, marginBottom: 6 }} />
            <div style={{ width: '50%', height: 10, background: 'var(--bg-subtle)', borderRadius: 2 }} />
          </div>
          <div style={{ width: 64, height: 10, background: 'var(--bg-subtle)', borderRadius: 2, flexShrink: 0 }} />
        </div>
      ))}
    </div>
  )
}
