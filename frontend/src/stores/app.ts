import { create } from 'zustand'
import { api, type HealthResponse } from '@/lib/api'

interface AppState {
  sidebarCollapsed: boolean
  toggleSidebar: () => void
  health: HealthResponse | null
  fetchHealth: () => Promise<void>
}

export const useAppStore = create<AppState>((set) => ({
  sidebarCollapsed: false,
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  health: null,
  fetchHealth: async () => {
    try {
      const health = await api.health()
      set({ health })
    } catch {
      set({ health: { status: 'error', version: '0', checks: {}, latency_ms: 0 } })
    }
  },
}))
