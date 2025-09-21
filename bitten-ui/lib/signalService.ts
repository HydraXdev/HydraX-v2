"use client"

import { eventBus, EVENTS } from './eventBus'
import type { SignalUpdateData } from './types'
import { Mission } from './store'
import io, { Socket } from 'socket.io-client'

interface SignalData {
  signal_id: string
  symbol: string
  direction: 'BUY' | 'SELL'
  entry_price?: number
  stop_pips?: number
  target_pips?: number
  confidence?: number
  pattern_type?: string
  signal_mode?: 'RAPID' | 'SNIPER'
  risk_reward?: number
  can_fire?: boolean
  created_at?: number
  expires_at?: number
}

class SignalService {
  private socket: Socket | null = null
  private apiUrl: string
  private wsUrl: string
  private pollInterval: NodeJS.Timeout | null = null
  private isConnected: boolean = false

  constructor() {
    this.apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8888'
    this.wsUrl = process.env.NEXT_PUBLIC_WS_BASE_URL || 'http://localhost:8888'
  }

  // Connect to backend services
  async connect() {
    // 1. Connect to Socket.IO for real-time updates
    this.connectWebSocket()
    
    // 2. Fetch initial signals
    await this.fetchSignals()
    
    // 3. Start polling for updates (backup for WebSocket)
    this.startPolling()
  }

  private connectWebSocket() {
    try {
      this.socket = io(this.wsUrl, {
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionAttempts: 5
      })

      this.socket.on('connect', () => {
        console.log('[SignalService] WebSocket connected')
        this.isConnected = true
        eventBus.emit(EVENTS.WS_CONNECTED, { service: 'signals' })
        
        // Subscribe to signal updates
        this.socket?.emit('get_signals')
      })

      this.socket.on('signals_update', (data: SignalUpdateData) => {
        console.log('[SignalService] Signals update received:', data)
        this.processSignals(data.signals || [])
      })

      this.socket.on('new_signal', (signal: SignalData) => {
        console.log('[SignalService] New signal:', signal)
        this.processSingleSignal(signal)
      })

      this.socket.on('disconnect', () => {
        console.log('[SignalService] WebSocket disconnected')
        this.isConnected = false
        eventBus.emit(EVENTS.WS_DISCONNECTED, { service: 'signals' })
      })

      this.socket.on('error', (error: Error) => {
        console.error('[SignalService] WebSocket error:', error)
        eventBus.emit(EVENTS.WS_ERROR, { service: 'signals', error })
      })
    } catch (error) {
      console.error('[SignalService] Failed to connect WebSocket:', error)
    }
  }

  // Fetch signals via REST API
  async fetchSignals() {
    try {
      const response = await fetch(`${this.apiUrl}/api/signals`)
      if (!response.ok) {
        throw new Error(`Failed to fetch signals: ${response.statusText}`)
      }

      const data = await response.json()
      console.log('[SignalService] Fetched signals:', data)
      
      if (data.signals && Array.isArray(data.signals)) {
        this.processSignals(data.signals)
      }
    } catch (error) {
      console.error('[SignalService] Failed to fetch signals:', error)
    }
  }

  // Process multiple signals
  private processSignals(signals: SignalData[]) {
    signals.forEach(signal => this.processSingleSignal(signal))
  }

  // Process a single signal and convert to Mission format
  private processSingleSignal(signal: SignalData) {
    // Convert signal to Mission format
    const mission: Mission = {
      id: signal.signal_id,
      symbol: signal.symbol,
      direction: signal.direction,
      timeframe: 'M15', // Default timeframe
      entry: signal.entry_price || this.calculateEntryPrice(signal),
      sl: this.calculateStopLoss(signal),
      tp: this.calculateTakeProfit(signal),
      pattern: this.mapPatternType(signal.pattern_type),
      type: signal.signal_mode || 'RAPID',
      confidence: signal.confidence || 75,
      status: 'NEW',
      expiresIn: this.calculateExpiryMinutes(signal),
      openedAt: signal.created_at || Date.now(),
      snapshotUrl: undefined // Will be populated later
    }

    // Emit as new mission
    eventBus.emit(EVENTS.MISSION_CREATED, mission)
  }

  // Helper functions for signal conversion
  private calculateEntryPrice(signal: SignalData): number {
    // Mock entry price for demo (will use real market price in production)
    const mockPrices: Record<string, number> = {
      'EURUSD': 1.08456,
      'GBPUSD': 1.27234,
      'GBPJPY': 189.234,
      'XAUUSD': 2024.50,
      'USDJPY': 147.234,
      'EURJPY': 159.567
    }
    return mockPrices[signal.symbol] || 1.0
  }

  private calculateStopLoss(signal: SignalData): number {
    const entry = signal.entry_price || this.calculateEntryPrice(signal)
    const pips = signal.stop_pips || 25
    const pipSize = this.getPipSize(signal.symbol)
    return signal.direction === 'BUY' 
      ? entry - (pips * pipSize)
      : entry + (pips * pipSize)
  }

  private calculateTakeProfit(signal: SignalData): number {
    const entry = signal.entry_price || this.calculateEntryPrice(signal)
    const pips = signal.target_pips || 50
    const pipSize = this.getPipSize(signal.symbol)
    return signal.direction === 'BUY'
      ? entry + (pips * pipSize)
      : entry - (pips * pipSize)
  }

  private getPipSize(symbol: string): number {
    if (symbol.includes('JPY')) return 0.01
    if (symbol === 'XAUUSD') return 0.1
    return 0.0001
  }

  private mapPatternType(pattern?: string): Mission['pattern'] {
    const patternMap: Record<string, Mission['pattern']> = {
      'LIQUIDITY_SWEEP_REVERSAL': 'LIQUIDITY_SWEEP_REVERSAL',
      'ORDER_BLOCK_BOUNCE': 'ORDER_BLOCK_BOUNCE',
      'VCB_BREAKOUT': 'VCB_BREAKOUT',
      'FAIR_VALUE_GAP_FILL': 'DIRECTION_BANDS',
      'MOMENTUM_BURST': 'DIRECTION_BANDS',
      'KALMAN_QUICKFIRE': 'VCB_BREAKOUT'
    }
    return patternMap[pattern || ''] || 'DIRECTION_BANDS'
  }

  private calculateExpiryMinutes(signal: SignalData): number {
    if (signal.expires_at && signal.created_at) {
      const expiryMs = signal.expires_at - signal.created_at
      return Math.floor(expiryMs / 60000)
    }
    return signal.signal_mode === 'SNIPER' ? 20 : 10
  }

  // Start polling for updates (backup for WebSocket)
  private startPolling() {
    // Poll every 10 seconds if WebSocket is not connected
    this.pollInterval = setInterval(async () => {
      if (!this.isConnected) {
        await this.fetchSignals()
      }
    }, 10000)
  }

  // Clean up connections
  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }

    if (this.pollInterval) {
      clearInterval(this.pollInterval)
      this.pollInterval = null
    }

    this.isConnected = false
  }

  // Check connection status
  getConnectionStatus(): boolean {
    return this.isConnected
  }

  // Request snapshot for a mission
  async requestSnapshot(missionId: string) {
    if (this.socket && this.isConnected) {
      this.socket.emit('request_snapshot', { mission_id: missionId })
    }
  }
}

// Export singleton instance
export const signalService = new SignalService()

// Auto-connect when module is imported (in browser only)
if (typeof window !== 'undefined') {
  signalService.connect()
}