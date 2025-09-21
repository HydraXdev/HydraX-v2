"use client"

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type MissionStatus = 'NEW' | 'ACCEPTED' | 'LIVE' | 'CLOSED'
export type MissionPattern = 'LIQUIDITY_SWEEP_REVERSAL' | 'ORDER_BLOCK_BOUNCE' | 'VCB_BREAKOUT' | 'DIRECTION_BANDS'
export type MissionType = 'RAPID' | 'SNIPER'

export interface Mission {
  id: string
  symbol: string              // "EURUSD"
  direction: 'BUY' | 'SELL'
  timeframe: string           // "M15"
  entry: number
  sl: number
  tp: number
  pattern: MissionPattern
  type: MissionType
  confidence: number          // 0..100
  snapshotUrl?: string        // placeholder for now
  status: MissionStatus
  expiresIn: number          // minutes
  openedAt: number           // ms
}

export interface XPEvent {
  id: string
  type: 'WIN' | 'LOSS' | 'CLOSE' | 'ACCEPT' | 'BONUS'
  at: number     // ms
  details: string
  delta: number  // xp points
}

interface UIState {
  missions: Mission[]
  xp: number
  xpEvents: XPEvent[]
  selectedMissionId?: string
  balance: number
  winRate: number
  // actions
  selectMission: (id: string) => void
  acceptMission: (id: string) => void
  executeMission: (id: string) => void
  closeMission: (id: string, outcome?: 'WIN' | 'LOSS') => void
  seedDemo: () => void
  addMission: (mission: Mission) => void
  updateMission: (id: string, updates: Partial<Mission>) => void
  addXPEvent: (event: XPEvent) => void
}

const demoMissions: Mission[] = [
  {
    id: 'ELITE_GUARD_EURUSD_1756789',
    symbol: 'EURUSD',
    direction: 'BUY',
    timeframe: 'M15',
    entry: 1.08456,
    sl: 1.08256,
    tp: 1.08856,
    pattern: 'LIQUIDITY_SWEEP_REVERSAL',
    type: 'SNIPER',
    confidence: 82,
    snapshotUrl: '/textures/placeholder_bands.png',
    status: 'NEW',
    expiresIn: 12,
    openedAt: Date.now() - 60_000,
  },
  {
    id: 'ELITE_GUARD_GBPJPY_1756790',
    symbol: 'GBPJPY',
    direction: 'SELL',
    timeframe: 'M5',
    entry: 189.234,
    sl: 189.534,
    tp: 188.734,
    pattern: 'VCB_BREAKOUT',
    type: 'RAPID',
    confidence: 75,
    snapshotUrl: '/textures/placeholder_ob.png',
    status: 'NEW',
    expiresIn: 8,
    openedAt: Date.now() - 120_000,
  },
  {
    id: 'ELITE_GUARD_XAUUSD_1756791',
    symbol: 'XAUUSD',
    direction: 'BUY',
    timeframe: 'M15',
    entry: 2024.50,
    sl: 2019.50,
    tp: 2034.50,
    pattern: 'ORDER_BLOCK_BOUNCE',
    type: 'SNIPER',
    confidence: 88,
    snapshotUrl: '/textures/placeholder_bands.png',
    status: 'NEW',
    expiresIn: 15,
    openedAt: Date.now() - 30_000,
  },
]

export const useUI = create<UIState>()(
  persist(
    (set, get) => ({
      missions: demoMissions,
      xp: 1250,
      xpEvents: [],
      selectedMissionId: undefined,
      balance: 12450,
      winRate: 68.5,

      selectMission: (id) => set({ selectedMissionId: id }),

      acceptMission: (id) => {
        const missions = get().missions.map(m =>
          m.id === id ? { ...m, status: 'ACCEPTED' as MissionStatus } : m
        )
        const ev: XPEvent = {
          id: crypto.randomUUID(),
          type: 'ACCEPT',
          at: Date.now(),
          details: `Mission Accepted: ${missions.find(m => m.id === id)?.symbol}`,
          delta: 5,
        }
        set({
          missions,
          xpEvents: [ev, ...get().xpEvents],
          xp: get().xp + 5
        })
      },

      executeMission: (id) => {
        const missions = get().missions.map(m =>
          m.id === id ? { ...m, status: 'LIVE' as MissionStatus } : m
        )
        set({ missions })
      },

      closeMission: (id, outcome = 'WIN') => {
        const mission = get().missions.find(m => m.id === id)
        if (!mission) return

        const missions = get().missions.map(m =>
          m.id === id ? { ...m, status: 'CLOSED' as MissionStatus } : m
        )

        const gain = outcome === 'WIN' ? 100 : 0
        const bonus = outcome === 'WIN' && mission.confidence > 80 ? 20 : 0
        const totalXP = gain + bonus

        const events: XPEvent[] = []

        if (gain > 0) {
          events.push({
            id: crypto.randomUUID(),
            type: outcome,
            at: Date.now(),
            details: `Trade to TP - ${mission.symbol}`,
            delta: gain,
          })
        }

        if (bonus > 0) {
          events.push({
            id: crypto.randomUUID(),
            type: 'BONUS',
            at: Date.now() + 100,
            details: `High Confidence Bonus`,
            delta: bonus,
          })
        }

        // Update balance and win rate
        const pnl = outcome === 'WIN'
          ? Math.abs(mission.tp - mission.entry) * 10000 // simplified P&L
          : -Math.abs(mission.sl - mission.entry) * 10000

        set({
          missions,
          xp: get().xp + totalXP,
          xpEvents: [...events, ...get().xpEvents],
          balance: get().balance + pnl,
          winRate: outcome === 'WIN' ? Math.min(100, get().winRate + 0.5) : Math.max(0, get().winRate - 0.5)
        })
      },

      seedDemo: () => set({
        missions: demoMissions,
        xp: 1250,
        xpEvents: [],
        selectedMissionId: undefined,
        balance: 12450,
        winRate: 68.5
      }),

      addMission: (mission) => set((state) => ({
        missions: [...state.missions, mission]
      })),

      updateMission: (id, updates) => set((state) => ({
        missions: state.missions.map(m =>
          m.id === id ? { ...m, ...updates } : m
        )
      })),

      addXPEvent: (event) => set((state) => ({
        xpEvents: [event, ...state.xpEvents],
        xp: state.xp + event.delta
      })),
    }),
    {
      name: 'bitten-ui-demo',
      partialize: (state) => ({
        xp: state.xp,
        xpEvents: state.xpEvents,
        balance: state.balance,
        winRate: state.winRate,
      })
    }
  )
)