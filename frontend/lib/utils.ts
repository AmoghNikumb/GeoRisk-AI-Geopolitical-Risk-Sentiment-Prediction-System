import { RiskLevel } from './types'

export function getRiskColor(level: RiskLevel): string {
  switch (level) {
    case 'LOW':      return 'var(--risk-low)'
    case 'MODERATE': return 'var(--risk-moderate)'
    case 'HIGH':     return 'var(--risk-high)'
    case 'CRITICAL': return 'var(--risk-critical)'
    default:         return 'var(--text-faint)'
  }
}

export function getRiskBg(level: RiskLevel): string {
  // Returns inline style object keys for use with style prop
  switch (level) {
    case 'LOW':      return 'risk-badge risk-badge-low'
    case 'MODERATE': return 'risk-badge risk-badge-moderate'
    case 'HIGH':     return 'risk-badge risk-badge-high'
    case 'CRITICAL': return 'risk-badge risk-badge-critical'
    default:         return 'risk-badge'
  }
}

export function getSentimentColor(score: number | null): string {
  if (score === null) return 'var(--text-faint)'
  if (score < -0.5) return 'var(--risk-critical)'
  if (score < -0.2) return 'var(--risk-high)'
  if (score < 0.2)  return 'var(--risk-moderate)'
  if (score < 0.5)  return 'var(--risk-low)'
  return 'var(--risk-low)'
}

export function formatScore(score: number | null): string {
  if (score === null) return 'N/A'
  return score.toFixed(1)
}

export function formatSentiment(score: number | null): string {
  if (score === null) return 'N/A'
  return (score > 0 ? '+' : '') + score.toFixed(2)
}

export function timeAgo(dateStr: string | null): string {
  if (!dateStr) return 'Unknown'
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

export function getCountryFlag(code: string): string {
  return code.toUpperCase().replace(/./g, c =>
    String.fromCodePoint(127397 + c.charCodeAt(0))
  )
}

export const COUNTRY_NAMES: Record<string, string> = {
  US: 'United States', CN: 'China', RU: 'Russia', IN: 'India',
  PK: 'Pakistan', GB: 'United Kingdom', DE: 'Germany', FR: 'France',
  JP: 'Japan', KR: 'South Korea', KP: 'North Korea', IR: 'Iran',
  IL: 'Israel', SA: 'Saudi Arabia', TR: 'Turkey', UA: 'Ukraine',
  BR: 'Brazil', AU: 'Australia', CA: 'Canada', MX: 'Mexico',
  PS: 'Palestine', TW: 'Taiwan', GR: 'Greece',
}

export const TRACKED_PAIRS = [
  // CRITICAL
  ['IL', 'IR'], ['US', 'IR'], ['RU', 'UA'], ['IL', 'PS'],
  // HIGH
  ['US', 'CN'], ['RU', 'US'], ['KP', 'KR'], ['IN', 'PK'],
  // MODERATE
  ['GB', 'US'], ['CN', 'TW'], ['CN', 'IN'], ['CN', 'JP'],
]

