import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { DashboardData } from '@/lib/types'

export function useDashboard(pollInterval = 300000) {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const fetch = async () => {
    try {
      const d = await api.dashboard()
      setData(d)
      setLastUpdated(new Date())
      setError(null)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetch()
    const interval = setInterval(fetch, pollInterval)
    return () => clearInterval(interval)
  }, [])

  return { data, loading, error, lastUpdated, refetch: fetch }
}

export function useBilateral(countryA: string, countryB: string) {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetch = async () => {
    setLoading(true)
    try {
      const d = await api.bilateral(countryA, countryB)
      setData(d)
      setError(null)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetch()
    const interval = setInterval(fetch, 300000)
    return () => clearInterval(interval)
  }, [countryA, countryB])

  return { data, loading, error, refetch: fetch }
}

export function useEntities(country: string) {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    api.entities(country)
      .then(d => { setData(d); setError(null) })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [country])

  return { data, loading, error }
}

