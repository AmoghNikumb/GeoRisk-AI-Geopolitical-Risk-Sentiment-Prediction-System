export type RiskLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL' | 'UNKNOWN'

export interface RiskScore {
  pair_key: string
  country_a: string
  country_b: string
  score: number
  classification: RiskLevel
  score_change: number | null
  prev_score?: number | null
  trend?: string
  computed_at: string
  headline_factors?: string[]
  contributing_factors?: Array<{ factor: string; impact: number }>
  component_breakdown?: {
    negative_sentiment: number
    sentiment_deterioration: number
    politician_hostility: number
    gdelt_conflict: number
    vix_spike: number
    market_stress: number
  }
  data_quality?: {
    posts_analyzed: number
    gdelt_events: number
    confidence: number
  }
}

export interface MarketData {
  vix: number | null
  sp500: number | null
  sp500_change_pct: number | null
  crude_oil: number | null
  gold: number | null
  dxy?: number | null
  market_stress_score: number | null
  captured_at: string | null
  stress_level?: string
}

export interface Alert {
  id: number
  pair_key: string
  country_a?: string
  country_b?: string
  title: string
  message?: string
  severity: 'INFO' | 'WARNING' | 'CRITICAL'
  triggered_at: string
  is_read?: boolean
  score_delta?: number
  alert_type?: string
}

export interface DashboardData {
  summary: {
    total_monitored_pairs: number
    critical_risk_pairs: number
    high_risk_pairs: number
    moderate_risk_pairs: number
    low_risk_pairs: number
    unread_alerts: number
    last_update: string
  }
  risk_scores: RiskScore[]
  top_risks: RiskScore[]
  market: MarketData | null
  alerts: Alert[]
  generated_at: string
}

export interface SentimentPoint {
  time: string
  avg: number | null
  politician: number | null
  public: number | null
  count: number
}

export interface RiskBreakdown {
  negative_sentiment: number | null
  sentiment_deterioration: number | null
  politician_hostility: number | null
  gdelt_conflict: number | null
  vix_spike: number | null
  market_stress: number | null
}

export interface IntelBrief {
  headline: string | null
  risk_level: RiskLevel | null
  summary: string | null
  key_drivers: string[]
  market_implications: string | null
  outlook_72hr: string | null
  confidence: number | null
  generated_at: string | null
  is_generating: boolean
}

export interface Post {
  source: string
  author: string
  text: string
  sentiment_score: number | null
  sentiment_label: string | null
  posted_at: string | null
  is_politician: boolean
}

export interface GdeltEvent {
  actor1: string
  actor2: string
  event_code: string
  goldstein_scale: number
  num_articles: number
  event_date: string | null
  geo: string | null
}

export interface BilateralData {
  pair_key: string
  country_a: string
  country_b: string
  risk_score: {
    score: number | null
    classification: RiskLevel
    score_change: number | null
    contributing_factors: Array<{ factor: string; impact: number; category: string }>
    breakdown: RiskBreakdown
    computed_at: string | null
  }
  sentiment_timeline?: {
    country_a: SentimentPoint[]
    country_b: SentimentPoint[]
  }
  top_posts?: Post[]
  intelligence_brief?: IntelBrief
  gdelt_events?: GdeltEvent[]
}

export interface Politician {
  id: number
  name: string
  twitter_handle: string
  title: string
  influence_weight: number
  avg_sentiment_72h: number | null
  recent_posts: Post[]
}

export interface EntitiesData {
  country: string
  politicians: Politician[]
  inflammatory_posts: Post[]
}

// ── News ──────────────────────────────────────────────────────────────────────

export interface NewsItem {
  id: string
  title: string
  summary: string
  url: string
  source: string
  source_id: string
  publishedAt: string | null
  image: string | null
  region: string
  topics: string[]
  countries: string[]
  flags: string[]
  featured: boolean
}

export interface NewsResponse {
  items: NewsItem[]
  total: number
  fetched_at: string
  sources: string[]
  cached: boolean
  filters: {
    region: string | null
    topic: string | null
    source: string | null
  }
}

