"use client"

import React, { useState, useEffect } from 'react'
import { eventBus, EVENTS } from '@/lib/eventBus'
import { useUI } from '@/lib/store'
import { motion } from 'framer-motion'
import {
  Zap,
  Activity,
  CheckCircle,
  XCircle,
  RefreshCw,
  Terminal
} from 'lucide-react'

// Make eventBus available globally for console testing
if (typeof window !== 'undefined') {
  (window as any).eventBus = eventBus;
  (window as any).EVENTS = EVENTS;
}

export default function TestPage() {
  const store = useUI()
  const [logs, setLogs] = useState<string[]>([])
  const [priceData, setPriceData] = useState({ bid: 0, ask: 0 })
  const [testResults, setTestResults] = useState<Record<string, boolean>>({})

  const log = (message: string) => {
    const timestamp = new Date().toLocaleTimeString()
    setLogs(prev => [`[${timestamp}] ${message}`, ...prev].slice(0, 20))
    console.log(`[TEST] ${message}`)
  }

  useEffect(() => {
    // Subscribe to all events for logging
    const events = Object.values(EVENTS)
    const unsubscribers: (() => void)[] = []

    events.forEach(event => {
      const unsub = eventBus.on(event, (data) => {
        log(`📨 Event: ${event} - ${JSON.stringify(data).slice(0, 100)}`)
      })
      unsubscribers.push(unsub)
    })

    // Price update subscription
    const priceUnsub = eventBus.on(EVENTS.PRICE_UPDATE, (data) => {
      setPriceData(data)
    })
    unsubscribers.push(priceUnsub)

    log('✅ Test page initialized - Event listeners attached')

    return () => {
      unsubscribers.forEach(unsub => unsub())
    }
  }, [])

  // Test Functions
  const testMissionCreate = () => {
    log('🚀 Testing: Mission Create')
    const mission = {
      id: `TEST_${Date.now()}`,
      symbol: 'EURUSD',
      direction: 'BUY' as const,
      timeframe: 'M15',
      entry: 1.08456,
      sl: 1.08256,
      tp: 1.08856,
      pattern: 'LIQUIDITY_SWEEP_REVERSAL' as const,
      type: 'SNIPER' as const,
      confidence: 85,
      status: 'NEW' as const,
      expiresIn: 15,
      openedAt: Date.now()
    }

    // Add to store directly (simulating WebSocket event)
    const currentMissions = [...store.missions]
    currentMissions.push(mission)
    store.missions = currentMissions

    eventBus.emit(EVENTS.MISSION_CREATED, mission)
    setTestResults(prev => ({ ...prev, missionCreate: true }))
    log(`✅ Mission created: ${mission.id}`)
  }

  const testSnapshotAttach = () => {
    log('🚀 Testing: Snapshot Attachment')
    const lastMission = store.missions[store.missions.length - 1]
    if (!lastMission) {
      log('❌ No mission to attach snapshot to')
      return
    }

    const snapshotData = {
      id: lastMission.id,
      snapshot_url: 'https://cdn.bitten/snapshot-demo.png',
      sha256: 'abc123'
    }

    eventBus.emit(EVENTS.MISSION_SNAPSHOT, snapshotData)

    // Update store
    const index = store.missions.findIndex(m => m.id === lastMission.id)
    if (index >= 0) {
      store.missions[index].snapshotUrl = snapshotData.snapshot_url
    }

    setTestResults(prev => ({ ...prev, snapshot: true }))
    log(`✅ Snapshot attached to mission: ${lastMission.id}`)
  }

  const testAcceptMission = () => {
    log('🚀 Testing: Accept Mission')
    const mission = store.missions.find(m => m.status === 'NEW')
    if (!mission) {
      log('❌ No NEW mission to accept')
      return
    }

    store.acceptMission(mission.id)
    eventBus.emit(EVENTS.MISSION_ACCEPTED, { id: mission.id })
    setTestResults(prev => ({ ...prev, accept: true }))
    log(`✅ Mission accepted: ${mission.id}`)
  }

  const testExecuteTrade = () => {
    log('🚀 Testing: Execute Trade')
    const mission = store.missions.find(m => m.status === 'ACCEPTED')
    if (!mission) {
      log('❌ No ACCEPTED mission to execute')
      return
    }

    store.executeMission(mission.id)

    // Simulate order execution response
    const orderData = {
      ticket: `TKT_${Date.now()}`,
      mission_id: mission.id,
      filled: mission.entry + 0.0002,
      sl: mission.sl,
      tp: mission.tp,
      broker: 'Demo-Broker'
    }

    eventBus.emit(EVENTS.ORDER_EXECUTED, orderData)
    setTestResults(prev => ({ ...prev, execute: true }))
    log(`✅ Trade executed: ${orderData.ticket}`)

    // Start price simulation
    simulatePriceStream(mission.symbol, mission.entry)
  }

  const simulatePriceStream = (symbol: string, basePrice: number) => {
    log(`📊 Starting price stream for ${symbol}`)
    let price = basePrice

    const interval = setInterval(() => {
      price += (Math.random() - 0.5) * 0.0005
      const priceUpdate = {
        symbol,
        t: Date.now(),
        bid: price - 0.0001,
        ask: price + 0.0001
      }
      eventBus.emit(EVENTS.PRICE_UPDATE, priceUpdate)
    }, 1000)

    // Stop after 10 seconds
    setTimeout(() => {
      clearInterval(interval)
      log('📊 Price stream stopped')
    }, 10000)
  }

  const testCloseTrade = () => {
    log('🚀 Testing: Close Trade')
    const mission = store.missions.find(m => m.status === 'LIVE')
    if (!mission) {
      log('❌ No LIVE mission to close')
      return
    }

    const pl = Math.random() > 0.5 ? 25.5 : -15.2
    const outcome = pl > 0 ? 'WIN' : 'LOSS'

    // Close in store
    store.closeMission(mission.id, outcome)

    // Emit close event
    eventBus.emit(EVENTS.ORDER_CLOSED, {
      ticket: `TKT_${mission.id}`,
      mission_id: mission.id,
      pl,
      closed: mission.entry + (pl > 0 ? 0.002 : -0.001)
    })

    // Award XP
    const xp = pl > 0 ? 100 : 0
    eventBus.emit(EVENTS.XP_EARNED, {
      amount: xp,
      reason: pl > 0 ? 'Trade Win' : 'Trade Loss',
      pl
    })

    setTestResults(prev => ({ ...prev, close: true }))
    log(`✅ Trade closed: ${outcome} P/L: ${pl}`)
  }

  const runFullCycle = async () => {
    log('🎯 Running full mission lifecycle test...')
    setTestResults({})

    // Reset demo data first
    store.seedDemo()
    await new Promise(r => setTimeout(r, 500))

    // Run test sequence
    testMissionCreate()
    await new Promise(r => setTimeout(r, 1000))

    testSnapshotAttach()
    await new Promise(r => setTimeout(r, 1000))

    testAcceptMission()
    await new Promise(r => setTimeout(r, 1000))

    testExecuteTrade()
    await new Promise(r => setTimeout(r, 2000))

    testCloseTrade()

    log('✅ Full cycle test complete!')
  }

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="panel p-6">
        <h1 className="text-2xl font-bold text-primary mb-2">BITTEN Event Bus Test Suite</h1>
        <p className="text-secondary">Test the complete mission lifecycle and event flow</p>
      </div>

      {/* Controls */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="panel p-6 space-y-4">
          <h2 className="text-lg font-semibold text-primary">Test Actions</h2>

          <div className="space-y-2">
            <button
              onClick={runFullCycle}
              className="w-full py-2 bg-mint text-black font-semibold rounded hover:bg-mint/90 transition-colors flex items-center justify-center gap-2"
            >
              <Zap size={16} />
              Run Full Cycle Test
            </button>

            <button
              onClick={testMissionCreate}
              className="w-full py-2 bg-secondary text-primary rounded hover:bg-overlay transition-colors"
            >
              1. Create Mission
            </button>

            <button
              onClick={testSnapshotAttach}
              className="w-full py-2 bg-secondary text-primary rounded hover:bg-overlay transition-colors"
            >
              2. Attach Snapshot
            </button>

            <button
              onClick={testAcceptMission}
              className="w-full py-2 bg-secondary text-primary rounded hover:bg-overlay transition-colors"
            >
              3. Accept Mission
            </button>

            <button
              onClick={testExecuteTrade}
              className="w-full py-2 bg-secondary text-primary rounded hover:bg-overlay transition-colors"
            >
              4. Execute Trade
            </button>

            <button
              onClick={testCloseTrade}
              className="w-full py-2 bg-secondary text-primary rounded hover:bg-overlay transition-colors"
            >
              5. Close Trade
            </button>

            <button
              onClick={() => store.seedDemo()}
              className="w-full py-2 bg-warning/20 text-warning rounded hover:bg-warning/30 transition-colors flex items-center justify-center gap-2"
            >
              <RefreshCw size={16} />
              Reset Demo Data
            </button>
          </div>
        </div>

        {/* Status */}
        <div className="panel p-6 space-y-4">
          <h2 className="text-lg font-semibold text-primary">System Status</h2>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-secondary">Missions</span>
              <span className="text-primary font-medium">{store.missions.length}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-secondary">Active</span>
              <span className="text-mint font-medium">
                {store.missions.filter(m => m.status === 'LIVE').length}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-secondary">Total XP</span>
              <span className="text-warning font-medium">{store.xp}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-secondary">Balance</span>
              <span className="text-success font-medium">${store.balance.toFixed(2)}</span>
            </div>
          </div>

          {priceData.bid > 0 && (
            <div className="pt-4 border-t border-default">
              <h3 className="text-sm font-semibold text-primary mb-2">Live Price</h3>
              <div className="flex items-center gap-2">
                <Activity size={14} className="text-mint animate-pulse" />
                <span className="text-sm mono text-primary">
                  {((priceData.bid + priceData.ask) / 2).toFixed(5)}
                </span>
              </div>
            </div>
          )}

          <div className="pt-4 border-t border-default">
            <h3 className="text-sm font-semibold text-primary mb-2">Test Results</h3>
            <div className="space-y-1">
              {Object.entries(testResults).map(([test, passed]) => (
                <div key={test} className="flex items-center gap-2 text-sm">
                  {passed ? (
                    <CheckCircle size={14} className="text-success" />
                  ) : (
                    <XCircle size={14} className="text-danger" />
                  )}
                  <span className="text-secondary capitalize">{test}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Event Log */}
      <div className="panel p-6">
        <h2 className="text-lg font-semibold text-primary mb-4 flex items-center gap-2">
          <Terminal size={20} />
          Event Log
        </h2>
        <div className="bg-overlay rounded p-4 h-64 overflow-y-auto">
          <div className="space-y-1 font-mono text-xs">
            {logs.length === 0 ? (
              <div className="text-tertiary">No events yet...</div>
            ) : (
              logs.map((log, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="text-secondary"
                >
                  {log}
                </motion.div>
              ))
            )}
          </div>
        </div>
        <div className="mt-2 text-xs text-tertiary">
          💡 Tip: Open console and use window.eventBus.emit() to test custom events
        </div>
      </div>

      {/* Instructions */}
      <div className="panel p-6">
        <h2 className="text-lg font-semibold text-primary mb-2">Console Testing</h2>
        <div className="text-sm text-secondary space-y-2">
          <p>Open browser console (F12) and try these commands:</p>
          <pre className="bg-overlay rounded p-3 text-xs mono text-primary overflow-x-auto">
{`// Emit a mission created event
eventBus.emit(EVENTS.MISSION_CREATED, {
  id: 'CONSOLE_TEST',
  symbol: 'GBPUSD',
  entry: 1.2500,
  sl: 1.2450,
  tp: 1.2550
})

// Simulate price update
eventBus.emit(EVENTS.PRICE_UPDATE, {
  symbol: 'EURUSD',
  bid: 1.0845,
  ask: 1.0847
})

// Award XP
eventBus.emit(EVENTS.XP_EARNED, {
  amount: 250,
  reason: 'Console Test Bonus'
})`}
          </pre>
        </div>
      </div>
    </div>
  )
}