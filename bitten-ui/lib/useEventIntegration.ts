"use client"

import { useEffect, useRef } from 'react'
import { eventBus, EVENTS } from './eventBus'
import { getPriceStream, disconnectAllStreams } from './websocket'
import { signalService } from './signalService'
import { useUI } from './store'
import type { MissionEventData, PriceData, OrderData, XPEventData } from './types'

interface EventIntegrationOptions {
  enableMissionStream?: boolean
  enablePriceStream?: boolean
  symbols?: string[]
  userId?: string
}

export function useEventIntegration(options: EventIntegrationOptions = {}) {
  const {
    enableMissionStream = true,
    enablePriceStream = false,
    symbols = [],
    userId = '7176191872' // Default demo user
  } = options

  const store = useUI()
  const unsubscribers = useRef<(() => void)[]>([])

  useEffect(() => {
    // Clear previous subscriptions
    unsubscribers.current.forEach(unsub => unsub())
    unsubscribers.current = []

    // Mission event handlers
    const handleMissionCreated = (data: any) => {
      console.log('Mission created:', data)
      // Add new mission to store
      const mission = {
        ...data,
        status: data.status || 'NEW',
        openedAt: Date.now()
      }
      store.addMission(mission)
    }

    const handleMissionUpdated = (data: any) => {
      console.log('Mission updated:', data)
      // Update mission in store
      store.updateMission(data.id, data)
    }

    const handleMissionSnapshot = (data: { id: string, snapshot_url: string }) => {
      console.log('Mission snapshot:', data)
      // Update mission snapshot URL
      store.updateMission(data.id, { snapshotUrl: data.snapshot_url })
    }

    const handleOrderExecuted = (data: any) => {
      console.log('Order executed:', data)
      // Update mission status to LIVE
      const index = store.missions.findIndex(m => m.id === data.mission_id)
      if (index >= 0) {
        store.missions[index].status = 'LIVE'
        // Store actual fill prices
        if (data.filled) store.missions[index].entry = data.filled
        if (data.sl) store.missions[index].sl = data.sl
        if (data.tp) store.missions[index].tp = data.tp
      }
    }

    const handleOrderClosed = (data: any) => {
      console.log('Order closed:', data)
      // Find and close mission
      const mission = store.missions.find(m =>
        m.status === 'LIVE' && m.id === data.mission_id
      )
      if (mission) {
        const outcome = data.pl > 0 ? 'WIN' : 'LOSS'
        store.closeMission(mission.id, outcome)
      }
    }

    const handlePriceUpdate = (data: PriceData) => {
      // Price updates can be handled by individual components
      // or stored in a separate price store
      eventBus.emit(`price.${data.symbol}`, data)
    }

    const handleXPEarned = (data: any) => {
      console.log('XP earned:', data)
      store.xp += data.amount
      store.xpEvents.unshift({
        id: crypto.randomUUID(),
        type: data.pl > 0 ? 'WIN' : 'CLOSE',
        at: Date.now(),
        details: data.reason,
        delta: data.amount
      })
    }

    // Subscribe to events
    unsubscribers.current.push(
      eventBus.on(EVENTS.MISSION_CREATED, handleMissionCreated),
      eventBus.on(EVENTS.MISSION_UPDATED, handleMissionUpdated),
      eventBus.on(EVENTS.MISSION_SNAPSHOT, handleMissionSnapshot),
      eventBus.on(EVENTS.ORDER_EXECUTED, handleOrderExecuted),
      eventBus.on(EVENTS.ORDER_CLOSED, handleOrderClosed),
      eventBus.on(EVENTS.PRICE_UPDATE, handlePriceUpdate),
      eventBus.on(EVENTS.XP_EARNED, handleXPEarned)
    )

    // Connect to real backend signal service
    if (enableMissionStream) {
      // Use the real signal service instead of mock WebSocket
      signalService.connect()
    }

    if (enablePriceStream && symbols.length > 0) {
      symbols.forEach(symbol => {
        const priceStream = getPriceStream(symbol)
        priceStream.connect()
      })
    }

    // Cleanup
    return () => {
      unsubscribers.current.forEach(unsub => unsub())
      if (enableMissionStream || enablePriceStream) {
        disconnectAllStreams()
      }
    }
  }, [enableMissionStream, enablePriceStream, symbols.join(','), userId])

  return {
    eventBus,
    userId
  }
}

// Hook for price subscriptions in components
export function usePriceSubscription(symbol: string, callback: (price: PriceData) => void) {
  useEffect(() => {
    const eventName = `price.${symbol}`
    const unsubscribe = eventBus.on(eventName, callback)

    // Connect price stream if not already connected
    const stream = getPriceStream(symbol)
    if (stream.getState() !== WebSocket.OPEN) {
      stream.connect()
    }

    return () => {
      unsubscribe()
    }
  }, [symbol, callback])
}

// Hook for mission lifecycle
export function useMissionLifecycle(missionId: string) {
  const store = useUI()

  const acceptMission = () => {
    store.acceptMission(missionId)
    eventBus.emit(EVENTS.MISSION_ACCEPTED, { id: missionId })
  }

  const executeMission = async () => {
    const mission = store.missions.find(m => m.id === missionId)
    if (!mission) return

    // In production, would call API
    // const response = await executeMissionAPI(mission, userId)
    // For now, just update store
    store.executeMission(missionId)
    eventBus.emit(EVENTS.MISSION_EXECUTED, { id: missionId })
  }

  const closeMission = async (outcome?: 'WIN' | 'LOSS') => {
    // In production, would call API
    // const response = await closePositionAPI(ticket, userId)
    // For now, just update store
    store.closeMission(missionId, outcome)
  }

  return {
    acceptMission,
    executeMission,
    closeMission
  }
}