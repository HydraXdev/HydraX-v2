"use client"

type EventCallback = (data: any) => void
type UnsubscribeFn = () => void

class EventBus {
  private events: Map<string, Set<EventCallback>> = new Map()
  private static instance: EventBus

  private constructor() {}

  static getInstance(): EventBus {
    if (!EventBus.instance) {
      EventBus.instance = new EventBus()
    }
    return EventBus.instance
  }

  emit(event: string, data?: any): void {
    const callbacks = this.events.get(event)
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data)
        } catch (error) {
          console.error(`Error in event handler for ${event}:`, error)
        }
      })
    }
  }

  on(event: string, callback: EventCallback): UnsubscribeFn {
    if (!this.events.has(event)) {
      this.events.set(event, new Set())
    }

    const callbacks = this.events.get(event)!
    callbacks.add(callback)

    // Return unsubscribe function
    return () => {
      callbacks.delete(callback)
      if (callbacks.size === 0) {
        this.events.delete(event)
      }
    }
  }

  once(event: string, callback: EventCallback): UnsubscribeFn {
    const wrappedCallback = (data: any) => {
      callback(data)
      this.off(event, wrappedCallback)
    }
    return this.on(event, wrappedCallback)
  }

  off(event: string, callback?: EventCallback): void {
    if (!callback) {
      // Remove all handlers for this event
      this.events.delete(event)
    } else {
      const callbacks = this.events.get(event)
      if (callbacks) {
        callbacks.delete(callback)
        if (callbacks.size === 0) {
          this.events.delete(event)
        }
      }
    }
  }

  clear(): void {
    this.events.clear()
  }
}

export const eventBus = EventBus.getInstance()

// Event types for type safety
export const EVENTS = {
  // Mission events
  MISSION_CREATED: 'mission.created',
  MISSION_UPDATED: 'mission.updated',
  MISSION_SNAPSHOT: 'mission.snapshot',
  MISSION_ACCEPTED: 'mission.accepted',
  MISSION_EXECUTED: 'mission.executed',
  MISSION_CLOSED: 'mission.closed',

  // Order events
  ORDER_EXECUTED: 'order.executed',
  ORDER_CLOSED: 'order.closed',
  ORDER_FAILED: 'order.failed',

  // Price events
  PRICE_UPDATE: 'price.update',
  PRICE_CONNECTED: 'price.connected',
  PRICE_DISCONNECTED: 'price.disconnected',

  // System events
  WS_CONNECTED: 'ws.connected',
  WS_DISCONNECTED: 'ws.disconnected',
  WS_ERROR: 'ws.error',

  // XP events
  XP_EARNED: 'xp.earned',
  LEVEL_UP: 'level.up',
  ACHIEVEMENT_UNLOCKED: 'achievement.unlocked',
} as const

export type EventType = typeof EVENTS[keyof typeof EVENTS]