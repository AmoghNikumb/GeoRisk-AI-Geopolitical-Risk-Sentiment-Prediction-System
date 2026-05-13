import { create } from 'zustand'
import { DashboardData, BilateralData } from '@/lib/types'

interface GeoRiskStore {
  dashboard: DashboardData | null
  setDashboard: (d: DashboardData) => void
  selectedPair: [string, string]
  setSelectedPair: (pair: [string, string]) => void
  bilateral: BilateralData | null
  setBilateral: (d: BilateralData) => void
  unreadAlerts: number
  setUnreadAlerts: (n: number) => void
}

export const useStore = create<GeoRiskStore>((set) => ({
  dashboard: null,
  setDashboard: (d) => set({ dashboard: d }),
  selectedPair: ['US', 'CN'],
  setSelectedPair: (pair) => set({ selectedPair: pair }),
  bilateral: null,
  setBilateral: (d) => set({ bilateral: d }),
  unreadAlerts: 0,
  setUnreadAlerts: (n) => set({ unreadAlerts: n }),
}))

