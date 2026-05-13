'use client'

import { useEffect, useState, useCallback } from 'react'
import { DashboardData, BilateralData } from '@/lib/types'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface UseDashboardReturn {
  data: DashboardData | null
  loading: boolean
  error: string | null
  lastUpdated: Date | null
  refetch: () => Promise<void>
}

export function useDashboard(refreshInterval: number = 30000): UseDashboardReturn {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const fetchDashboard = useCallback(async () => {
    try {
      setError(null)
      const res = await fetch(`${API_BASE}/api/dashboard`, { cache: 'no-store' })
      if (!res.ok) throw new Error(`API error: ${res.status}`)
      const result = await res.json()
      setData(result)
      setLastUpdated(new Date())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch dashboard')
      console.error('Dashboard fetch error:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchDashboard()
    const interval = setInterval(fetchDashboard, refreshInterval)
    return () => clearInterval(interval)
  }, [fetchDashboard, refreshInterval])

  return { data, loading, error, lastUpdated, refetch: fetchDashboard }
}

interface UseBilateralReturn {
  data: BilateralData | null
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
}

export function useBilateral(countryA: string, countryB: string): UseBilateralReturn {
  const [data, setData] = useState<BilateralData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchBilateral = useCallback(async () => {
    if (!countryA || !countryB) return
    
    try {
      setError(null)
      const res = await fetch(`${API_BASE}/api/bilateral?a=${countryA}&b=${countryB}`, {
        cache: 'no-store'
      })
      if (!res.ok) throw new Error(`API error: ${res.status}`)
      const result = await res.json()
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch bilateral data')
    } finally {
      setLoading(false)
    }
  }, [countryA, countryB])

  useEffect(() => {
    fetchBilateral()
  }, [fetchBilateral])

  return { data, loading, error, refetch: fetchBilateral }
}

/**
 * ML/NLP Prediction Hook (Ready for Integration)
 * Currently returns mock predictions - integrate with actual model endpoint
 */
interface RiskPrediction {
  predicted_score: number
  prediction_confidence: number
  horizon_hours: number
  factors: string[]
}

export function useRiskPrediction(countryA: string, countryB: string) {
  const [prediction, setPrediction] = useState<RiskPrediction | null>(null)
  const [predicting, setPredicting] = useState(false)
  const [predError, setPredError] = useState<string | null>(null)

  const fetchPrediction = useCallback(async () => {
    setPredicting(true)
    try {
      // TODO: Replace with actual ML endpoint
      // const res = await fetch(`${API_BASE}/api/predict?a=${countryA}&b=${countryB}`)
      
      // Mock prediction (remove when backend ready)
      setTimeout(() => {
        setPrediction({
          predicted_score: Math.random() * 100,
          prediction_confidence: 0.75 + Math.random() * 0.25,
          horizon_hours: 72,
          factors: ['Sentiment trend', 'GDELT activity', 'Market volatility']
        })
      }, 500)
    } catch (err) {
      setPredError(err instanceof Error ? err.message : 'Prediction failed')
    } finally {
      setPredicting(false)
    }
  }, [countryA, countryB])

  return { prediction, predicting, predError, fetch: fetchPrediction }
}

/**
 * Sentiment Trend Hook - Provides enhanced sentiment data with ML features
 */
interface SentimentTrend {
  raw_score: number
  adjusted_score: number  // With ML weighting
  trend_direction: 'up' | 'down' | 'stable'
  volatility: number
  ml_confidence: number
}

export function useSentimentTrend(country: string) {
  const [trend, setTrend] = useState<SentimentTrend | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // TODO: Integrate with ML sentiment analysis endpoint
    // For now, fetch from existing sentiment_scores
    const fetchTrend = async () => {
      try {
        // const res = await fetch(`${API_BASE}/api/sentiment/${country}`)
        // const data = await res.json()
        // Process with ML confidence scoring
      } catch (err) {
        console.error('Sentiment fetch failed:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchTrend()
  }, [country])

  return { trend, loading }
}

/**
 * Anomaly Detection Hook - Flag unusual patterns
 */
interface AnomalyAlert {
  type: 'sentiment_spike' | 'gdelt_cluster' | 'coordination' | 'trend_reversal'
  severity: 'low' | 'medium' | 'high'
  confidence: number
  description: string
  affected_pairs: string[]
}

export function useAnomalyDetection() {
  const [anomalies, setAnomalies] = useState<AnomalyAlert[]>([])
  const [scanning, setScanning] = useState(false)

  const scan = useCallback(async () => {
    setScanning(true)
    try {
      // TODO: Call ML anomaly detection endpoint
      // const res = await fetch(`${API_BASE}/api/anomalies/scan`)
      // setAnomalies(await res.json())
    } finally {
      setScanning(false)
    }
  }, [])

  return { anomalies, scanning, scan }
}

/**
 * Intelligence Brief Generation Hook - with LLM integration
 */
interface BriefGenerationState {
  status: 'idle' | 'generating' | 'completed' | 'error'
  progress: number  // 0-100
  enriched_text?: string  // Final LLM output
  error?: string
}

export function useGenerateBrief(countryA: string, countryB: string) {
  const [state, setState] = useState<BriefGenerationState>({ status: 'idle', progress: 0 })

  const generate = useCallback(async (forceRegenerate: boolean = false) => {
    setState({ status: 'generating', progress: 10 })
    
    try {
      // API call to backend brief generator
      const res = await fetch(`${API_BASE}/api/briefs/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ country_a: countryA, country_b: countryB, force: forceRegenerate })
      })

      if (!res.ok) throw new Error(`Generation failed: ${res.status}`)

      setState({ status: 'generating', progress: 50 })
      const brief = await res.json()

      // TODO: Post-process with ML refinement if enabled
      // const refined = await refineWithLLM(brief)

      setState({ status: 'completed', progress: 100, enriched_text: brief.summary })
    } catch (err) {
      setState({
        status: 'error',
        progress: 0,
        error: err instanceof Error ? err.message : 'Generation failed'
      })
    }
  }, [countryA, countryB])

  return { state, generate }
}

/**
 * Market Sentiment Integration - combines market data with sentiment
 */
interface MarketSentimentCorrelation {
  market_stress_level: 'low' | 'moderate' | 'high' | 'critical'
  sentiment_alignment: number  // -1 to 1 (how well sentiment predicts market)
  predicted_market_impact: number  // -100 to 100
  confidence: number
}

export function useMarketSentimentIntegration() {
  const [correlation, setCorrelation] = useState<MarketSentimentCorrelation | null>(null)

  // TODO: Implement correlation calculation
  // useEffect(() => { ... }, [])

  return { correlation }
}
