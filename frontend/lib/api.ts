const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function fetchAPI<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`)
  return res.json()
}

export const api = {
  dashboard: () => fetchAPI<any>('/api/dashboard'),
  bilateral: (a: string, b: string) => fetchAPI<any>(`/api/bilateral?a=${a}&b=${b}`),
  entities: (country: string) => fetchAPI<any>(`/api/entities?country=${country}`),
  alerts: () => fetchAPI<any>('/api/alerts'),
  generateBrief: (a: string, b: string) =>
    fetch(`${API_BASE}/api/briefs/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ country_a: a, country_b: b }),
    }).then(r => r.json()),
  markAlertRead: (id: number) =>
    fetch(`${API_BASE}/api/alerts/${id}/read`, { method: 'PATCH' }),
  markAllAlertsRead: () =>
    fetch(`${API_BASE}/api/alerts/read-all`, { method: 'PATCH' }),
  news: (params?: { region?: string; topic?: string; source?: string; limit?: number; force_refresh?: boolean }) => {
    const qs = new URLSearchParams()
    if (params?.region) qs.set('region', params.region)
    if (params?.topic) qs.set('topic', params.topic)
    if (params?.source) qs.set('source', params.source)
    if (params?.limit) qs.set('limit', String(params.limit))
    if (params?.force_refresh) qs.set('force_refresh', 'true')
    const query = qs.toString() ? `?${qs.toString()}` : ''
    return fetchAPI<any>(`/api/geopolitical-news${query}`)
  },
  // ── Model inference endpoints ──────────────────────────────────────────────
  modelStatus: () => fetchAPI<any>('/api/model/status'),
  modelDemo: () => fetchAPI<any>('/api/model/demo'),
  modelDemoTweets: () => fetchAPI<any>('/api/model/demo-tweets'),
  modelDemoTweetsPair: (pair: string) => fetchAPI<any>(`/api/model/demo-tweets/${pair}`),
  modelInfer: (texts: string[], country?: string) =>
    fetch(`${API_BASE}/api/model/infer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ texts, country: country ?? 'GLOBAL' }),
    }).then(r => r.json()),
  politicalStatements: (limit = 20, forceReload = false) =>
    fetchAPI<any>(`/api/model/political-statements?limit=${limit}&force_reload=${forceReload}`),
}

