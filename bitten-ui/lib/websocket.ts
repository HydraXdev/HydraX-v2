"use client"

import { eventBus, EVENTS } from './eventBus'
import type { PriceData } from './types'

interface WSMessage {
  type: string
  data: unknown
}

interface ReconnectOptions {
  maxAttempts?: number
  delay?: number
  backoff?: number
}

class WebSocketService {
  private ws: WebSocket | null = null
  private url: string
  private reconnectTimer: NodeJS.Timeout | null = null
  private reconnectAttempts: number = 0
  private reconnectOptions: ReconnectOptions
  private isIntentionallyClosed: boolean = false
  private pingInterval: NodeJS.Timeout | null = null
  private messageQueue: WSMessage[] = []

  constructor(
    url: string,
    reconnectOptions: ReconnectOptions = {
      maxAttempts: 5,
      delay: 1000,
      backoff: 1.5
    }
  ) {
    this.url = url
    this.reconnectOptions = reconnectOptions
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return
    }

    this.isIntentionallyClosed = false

    try {
      this.ws = new WebSocket(this.url)

      this.ws.onopen = () => {
        console.log(`WebSocket connected to ${this.url}`)
        this.reconnectAttempts = 0
        eventBus.emit(EVENTS.WS_CONNECTED, { url: this.url })

        // Send queued messages
        this.flushMessageQueue()

        // Start ping interval
        this.startPing()
      }

      this.ws.onmessage = (event) => {
        try {
          const message: WSMessage = JSON.parse(event.data)
          this.handleMessage(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        eventBus.emit(EVENTS.WS_ERROR, { error, url: this.url })
      }

      this.ws.onclose = (event) => {
        console.log(`WebSocket disconnected from ${this.url}`)
        this.stopPing()
        eventBus.emit(EVENTS.WS_DISCONNECTED, { url: this.url })

        if (!this.isIntentionallyClosed) {
          this.attemptReconnect()
        }
      }
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
      this.attemptReconnect()
    }
  }

  private handleMessage(message: WSMessage): void {
    // Route messages to event bus based on type
    switch (message.type) {
      case 'mission.created':
        eventBus.emit(EVENTS.MISSION_CREATED, message.data)
        break
      case 'mission.updated':
        eventBus.emit(EVENTS.MISSION_UPDATED, message.data)
        break
      case 'mission.snapshot':
        eventBus.emit(EVENTS.MISSION_SNAPSHOT, message.data)
        break
      case 'order.executed':
        eventBus.emit(EVENTS.ORDER_EXECUTED, message.data)
        break
      case 'order.closed':
        eventBus.emit(EVENTS.ORDER_CLOSED, message.data)
        break
      default:
        // Generic event routing
        eventBus.emit(message.type, message.data)
    }
  }

  send(message: WSMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      // Queue message for when connection is restored
      this.messageQueue.push(message)
    }
  }

  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0 && this.ws?.readyState === WebSocket.OPEN) {
      const message = this.messageQueue.shift()
      if (message) {
        this.ws.send(JSON.stringify(message))
      }
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= (this.reconnectOptions.maxAttempts || 5)) {
      console.error('Max reconnection attempts reached')
      return
    }

    const delay = (this.reconnectOptions.delay || 1000) *
      Math.pow(this.reconnectOptions.backoff || 1.5, this.reconnectAttempts)

    this.reconnectAttempts++
    console.log(`Attempting reconnect #${this.reconnectAttempts} in ${delay}ms`)

    this.reconnectTimer = setTimeout(() => {
      this.connect()
    }, delay)
  }

  private startPing(): void {
    this.stopPing()
    this.pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping', data: null })
      }
    }, 30000) // Ping every 30 seconds
  }

  private stopPing(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval)
      this.pingInterval = null
    }
  }

  disconnect(): void {
    this.isIntentionallyClosed = true

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    this.stopPing()

    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  getState(): number {
    return this.ws?.readyState || WebSocket.CLOSED
  }
}

// Price stream WebSocket
export class PriceStreamService extends WebSocketService {
  private symbol: string

  constructor(symbol: string, baseUrl: string = 'wss://api.bitten') {
    super(`${baseUrl}/price?symbol=${symbol}`)
    this.symbol = symbol
  }

  protected handleMessage(message: PriceData): void {
    // Price updates are direct, not wrapped in type/data
    if (message.bid && message.ask) {
      eventBus.emit(EVENTS.PRICE_UPDATE, {
        symbol: this.symbol,
        ...message
      })
    }
  }
}

// Mission stream WebSocket
export class MissionStreamService extends WebSocketService {
  constructor(baseUrl: string = 'wss://api.bitten') {
    super(`${baseUrl}/missions/stream`)
  }
}

// Export singleton instances
let missionStream: MissionStreamService | null = null
const priceStreams: Map<string, PriceStreamService> = new Map()

export function getMissionStream(): MissionStreamService {
  if (!missionStream) {
    missionStream = new MissionStreamService()
  }
  return missionStream
}

export function getPriceStream(symbol: string): PriceStreamService {
  if (!priceStreams.has(symbol)) {
    const stream = new PriceStreamService(symbol)
    priceStreams.set(symbol, stream)
  }
  return priceStreams.get(symbol)!
}

export function disconnectAllStreams(): void {
  missionStream?.disconnect()
  missionStream = null

  priceStreams.forEach(stream => stream.disconnect())
  priceStreams.clear()
}