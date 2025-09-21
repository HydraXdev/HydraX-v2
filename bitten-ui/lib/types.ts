export type { Mission } from './store'

export interface BackendSignal {
  signal_id: string
  symbol: string
  direction: 'BUY' | 'SELL'
  entry_price: number
  stop_pips: number
  target_pips: number
  confidence: number
  pattern_type: string
  signal_type: string
  created_at: number
  expires_at: number
}

export interface SignalUpdateData {
  signals?: BackendSignal[]
  new_signal?: BackendSignal
  signal_update?: Partial<BackendSignal> & { signal_id: string }
}

export interface PriceData {
  symbol: string
  bid: number
  ask: number
  timestamp: number
}

export interface OrderData {
  orderId: string
  symbol: string
  type: 'BUY' | 'SELL'
  volume: number
  price: number
  timestamp: number
}

export interface XPEventData {
  type: 'WIN' | 'LOSS' | 'CLOSE' | 'ACCEPT' | 'BONUS'
  amount: number
  details: string
}

export interface MissionEventData {
  mission: {
    id: string
    symbol: string
    direction: 'BUY' | 'SELL'
    entry: number
    sl: number
    tp: number
    confidence: number
    pattern: string
    type: string
    status: string
  }
}

export interface FireResponse {
  success: boolean
  message: string
  fire_id?: string
  error_code?: string
}

export interface RenderMissionResponse {
  success: boolean
  snapshot_url?: string
  error?: string
}