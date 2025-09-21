"use client"

import { eventBus, EVENTS } from './eventBus'
import type { Mission } from './store'

interface ApiConfig {
  baseUrl?: string
  headers?: Record<string, string>
  timeout?: number
}

interface ExecuteOrderRequest {
  user_id: string
  mission_id: string
  symbol: string
  entry: number
  sl: number
  tp: number
  mode?: 'MARKET' | 'LIMIT'
}

interface ExecuteOrderResponse {
  status: 'ok' | 'error'
  ticket?: string
  filled?: number
  sl?: number
  tp?: number
  broker?: string
  at?: string
  sig?: string
  error?: string
}

interface CloseOrderRequest {
  user_id: string
  ticket: string
}

interface CloseOrderResponse {
  status: 'ok' | 'error'
  ticket?: string
  closed?: number
  pl?: number
  at?: string
  sig?: string
  error?: string
}

interface RenderMissionRequest {
  mission_id: string
  symbol: string
  timeframe: string
  entry: number
  sl: number
  tp: number
  pattern: string
  tags?: string[]
  template?: string
  deadline_ms?: number
}

interface RenderMissionResponse {
  mission_id: string
  status: 'ok' | 'error'
  image_url?: string
  sha256?: string
  rendered_at?: string
  renderer_id?: string
  error?: string
}

class BittenAPI {
  private config: ApiConfig

  constructor(config: ApiConfig = {}) {
    this.config = {
      baseUrl: config.baseUrl || process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8888',
      headers: {
        'Content-Type': 'application/json',
        ...config.headers
      },
      timeout: config.timeout || 10000
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), this.config.timeout!)

    try {
      const response = await fetch(`${this.config.baseUrl}${endpoint}`, {
        ...options,
        headers: {
          ...this.config.headers,
          ...options.headers
        },
        signal: controller.signal
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      clearTimeout(timeoutId)

      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Request timeout')
      }

      throw error
    }
  }

  // Mission snapshot rendering
  async renderMission(request: RenderMissionRequest): Promise<RenderMissionResponse> {
    try {
      const response = await this.request<RenderMissionResponse>('/render-mission', {
        method: 'POST',
        body: JSON.stringify(request)
      })

      if (response.status === 'ok' && response.image_url) {
        eventBus.emit(EVENTS.MISSION_SNAPSHOT, {
          id: request.mission_id,
          snapshot_url: response.image_url,
          sha256: response.sha256
        })
      }

      return response
    } catch (error) {
      console.error('Failed to render mission:', error)
      return {
        mission_id: request.mission_id,
        status: 'error',
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    }
  }

  // Execute order - using real /api/fire endpoint
  async executeOrder(request: ExecuteOrderRequest): Promise<ExecuteOrderResponse> {
    try {
      // Map to actual backend /api/fire format
      const fireRequest = {
        signal_id: request.mission_id,
        user_id: request.user_id
      }

      const response = await this.request<{success: boolean, ticket?: string, fire_id?: string, filled?: number, broker?: string, error?: string}>('/api/fire', {
        method: 'POST',
        body: JSON.stringify(fireRequest)
      })

      // Map response to expected format
      if (response.success) {
        return {
          status: 'ok',
          ticket: response.ticket || response.fire_id,
          filled: response.filled || request.entry,
          sl: request.sl,
          tp: request.tp,
          broker: response.broker || 'Demo',
          at: new Date().toISOString()
        }
      } else {
        return {
          status: 'error',
          error: response.error || 'Fire command failed'
        }
      }

      if (response.status === 'ok' && response.ticket) {
        eventBus.emit(EVENTS.ORDER_EXECUTED, {
          ticket: response.ticket,
          mission_id: request.mission_id,
          filled: response.filled,
          sl: response.sl,
          tp: response.tp,
          broker: response.broker
        })
      }

      return response
    } catch (error) {
      console.error('Failed to execute order:', error)
      eventBus.emit(EVENTS.ORDER_FAILED, {
        mission_id: request.mission_id,
        error: error instanceof Error ? error.message : 'Unknown error'
      })
      return {
        status: 'error',
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    }
  }

  // Close order
  async closeOrder(request: CloseOrderRequest): Promise<CloseOrderResponse> {
    try {
      const response = await this.request<CloseOrderResponse>('/orders/close', {
        method: 'POST',
        body: JSON.stringify(request)
      })

      if (response.status === 'ok' && response.ticket) {
        eventBus.emit(EVENTS.ORDER_CLOSED, {
          ticket: response.ticket,
          pl: response.pl,
          closed: response.closed
        })

        if (response.pl !== undefined) {
          const xp = response.pl > 0 ? 100 : 0
          eventBus.emit(EVENTS.XP_EARNED, {
            amount: xp,
            reason: response.pl > 0 ? 'Trade Win' : 'Trade Loss',
            pl: response.pl
          })
        }
      }

      return response
    } catch (error) {
      console.error('Failed to close order:', error)
      return {
        status: 'error',
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    }
  }

  // Get pattern templates
  async getPatternTemplates() {
    return this.request('/patterns')
  }

  // Set auth token
  setAuthToken(token: string) {
    this.config.headers = {
      ...this.config.headers,
      'Authorization': `Bearer ${token}`
    }
  }
}

// Export singleton instance
export const bittenAPI = new BittenAPI()

// Convenience functions
export async function executeMission(
  mission: Mission,
  userId: string
): Promise<ExecuteOrderResponse> {
  return bittenAPI.executeOrder({
    user_id: userId,
    mission_id: mission.id,
    symbol: mission.symbol,
    entry: mission.entry,
    sl: mission.sl,
    tp: mission.tp,
    mode: 'MARKET'
  })
}

export async function closePosition(
  ticket: string,
  userId: string
): Promise<CloseOrderResponse> {
  return bittenAPI.closeOrder({
    user_id: userId,
    ticket
  })
}

export async function requestSnapshot(mission: Mission): Promise<RenderMissionResponse> {
  return bittenAPI.renderMission({
    mission_id: mission.id,
    symbol: mission.symbol,
    timeframe: mission.timeframe || 'M15',
    entry: mission.entry,
    sl: mission.sl,
    tp: mission.tp,
    pattern: mission.pattern,
    tags: mission.type ? [mission.type] : [],
    template: mission.pattern.toLowerCase().replace(/_/g, '_'),
    deadline_ms: 5000
  })
}