"use client"

import React, { useState, useEffect } from 'react'
import { eventBus, EVENTS } from '@/lib/eventBus'
import { useUI } from '@/lib/store'
import { signalService } from '@/lib/signalService'
import type { BackendSignal, Mission } from '@/lib/types'
import { motion } from 'framer-motion'
import {
  Wifi,
  WifiOff,
  Server,
  RefreshCw
} from 'lucide-react'

export default function LiveIntegrationPage() {
  const store = useUI()
  const [connectionStatus, setConnectionStatus] = useState(false)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [logs, setLogs] = useState<string[]>([])
  const [backendSignals, setBackendSignals] = useState<BackendSignal[]>([])

  const log = (message: string, type: 'info' | 'success' | 'error' = 'info') => {
    const timestamp = new Date().toLocaleTimeString()
    const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : '📌'
    setLogs(prev => [`[${timestamp}] ${icon} ${message}`, ...prev].slice(0, 50))
  }

  useEffect(() => {
    // Check WebSocket connection status
    const checkConnection = () => {
      const isConnected = signalService.getConnectionStatus()
      setConnectionStatus(isConnected)
      if (isConnected) {
        log('WebSocket connected to backend', 'success')
      }
    }

    // Subscribe to connection events
    const handleConnect = () => {
      setConnectionStatus(true)
      setLastUpdate(new Date())
      log('Connected to BITTEN backend', 'success')
    }

    const handleDisconnect = () => {
      setConnectionStatus(false)
      log('Disconnected from backend', 'error')
    }

    const handleMissionCreated = (mission: Mission) => {
      log(`New mission: ${mission.symbol} ${mission.direction} @ ${mission.confidence}%`, 'success')
      setLastUpdate(new Date())
    }

    eventBus.on(EVENTS.WS_CONNECTED, handleConnect)
    eventBus.on(EVENTS.WS_DISCONNECTED, handleDisconnect)
    eventBus.on(EVENTS.MISSION_CREATED, handleMissionCreated)

    // Initial check
    checkConnection()

    // Fetch backend signals directly
    fetchBackendSignals()

    return () => {
      eventBus.off(EVENTS.WS_CONNECTED, handleConnect)
      eventBus.off(EVENTS.WS_DISCONNECTED, handleDisconnect)
      eventBus.off(EVENTS.MISSION_CREATED, handleMissionCreated)
    }
  }, [])

  const fetchBackendSignals = async () => {
    try {
      log('Fetching signals from backend...')
      const response = await fetch('http://localhost:8888/api/signals')
      const data = await response.json()
      
      if (data.signals && Array.isArray(data.signals)) {
        setBackendSignals(data.signals)
        log(`Fetched ${data.signals.length} signals from backend`, 'success')
      }
    } catch (error) {
      log(`Failed to fetch signals: ${error}`, 'error')
    }
  }

  const testFireCommand = async (signalId: string) => {
    try {
      log(`Testing fire command for ${signalId}...`)
      const response = await fetch('http://localhost:8888/api/fire', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          signal_id: signalId,
          user_id: '7176191872'
        })
      })
      const result = await response.json()
      
      if (result.success) {
        log(`Fire command successful: ${JSON.stringify(result)}`, 'success')
      } else {
        log(`Fire command failed: ${result.error || 'Unknown error'}`, 'error')
      }
    } catch (error) {
      log(`Fire test error: ${error}`, 'error')
    }
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="panel p-6">
        <h1 className="text-2xl font-bold text-primary mb-2">
          BITTEN Live Integration 🔌
        </h1>
        <p className="text-secondary">
          Real-time connection to backend services on port 8888
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Connection Status */}
        <div className="panel p-6 space-y-4">
          <h2 className="text-lg font-semibold text-primary flex items-center gap-2">
            <Server size={20} />
            Backend Connection
          </h2>

          <div className="space-y-3">
            {/* WebSocket Status */}
            <div className="flex items-center justify-between">
              <span className="text-secondary">WebSocket</span>
              <div className="flex items-center gap-2">
                {connectionStatus ? (
                  <>
                    <Wifi className="text-success" size={16} />
                    <span className="text-success text-sm">Connected</span>
                  </>
                ) : (
                  <>
                    <WifiOff className="text-danger" size={16} />
                    <span className="text-danger text-sm">Disconnected</span>
                  </>
                )}
              </div>
            </div>

            {/* API Endpoint */}
            <div className="flex items-center justify-between">
              <span className="text-secondary">API Base</span>
              <span className="text-primary text-sm mono">localhost:8888</span>
            </div>

            {/* Last Update */}
            <div className="flex items-center justify-between">
              <span className="text-secondary">Last Update</span>
              <span className="text-primary text-sm">
                {lastUpdate ? lastUpdate.toLocaleTimeString() : 'Never'}
              </span>
            </div>

            {/* Mission Count */}
            <div className="flex items-center justify-between">
              <span className="text-secondary">Active Missions</span>
              <span className="text-mint font-medium">{store.missions.length}</span>
            </div>

            {/* Backend Signals */}
            <div className="flex items-center justify-between">
              <span className="text-secondary">Backend Signals</span>
              <span className="text-warning font-medium">{backendSignals.length}</span>
            </div>
          </div>

          <button
            onClick={fetchBackendSignals}
            className="w-full py-2 bg-secondary text-primary rounded hover:bg-overlay transition-colors flex items-center justify-center gap-2"
          >
            <RefreshCw size={16} />
            Refresh Signals
          </button>
        </div>

        {/* Backend Signals */}
        <div className="panel p-6 space-y-4">
          <h2 className="text-lg font-semibold text-primary">
            Live Signals from Backend
          </h2>

          <div className="space-y-2 max-h-80 overflow-y-auto">
            {backendSignals.length === 0 ? (
              <div className="text-tertiary text-sm">No signals available</div>
            ) : (
              backendSignals.map((signal, i) => (
                <motion.div
                  key={signal.signal_id || i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="bg-overlay rounded p-3 space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs px-2 py-0.5 rounded bg-warning/20 text-warning">
                        {signal.signal_mode || 'RAPID'}
                      </span>
                      <span className="text-sm font-medium text-primary">
                        {signal.symbol}
                      </span>
                      <span className={`text-xs font-semibold ${
                        signal.direction === 'BUY' ? 'text-success' : 'text-danger'
                      }`}>
                        {signal.direction}
                      </span>
                    </div>
                    <span className="text-xs text-mint">
                      {signal.confidence?.toFixed(1)}%
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-tertiary">
                      {signal.pattern_type || 'UNKNOWN'}
                    </span>
                    <button
                      onClick={() => testFireCommand(signal.signal_id)}
                      className="px-2 py-0.5 bg-mint/20 text-mint rounded hover:bg-mint/30 transition-colors"
                      disabled={!signal.can_fire}
                    >
                      Test Fire
                    </button>
                  </div>
                </motion.div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Event Log */}
      <div className="panel p-6">
        <h2 className="text-lg font-semibold text-primary mb-4">
          Integration Log
        </h2>
        <div className="bg-overlay rounded p-4 h-64 overflow-y-auto">
          <div className="space-y-1 font-mono text-xs">
            {logs.length === 0 ? (
              <div className="text-tertiary">Waiting for events...</div>
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
      </div>

      {/* Instructions */}
      <div className="panel p-6">
        <h2 className="text-lg font-semibold text-primary mb-2">Integration Details</h2>
        <div className="text-sm text-secondary space-y-2">
          <p>🔗 Connected to real BITTEN backend on <code className="text-mint">localhost:8888</code></p>
          <p>📡 WebSocket using Socket.IO for real-time updates</p>
          <p>🎯 REST API endpoints: <code className="text-mint">/api/signals</code>, <code className="text-mint">/api/fire</code></p>
          <p>⚠️ Market is closed until tomorrow night - using cached demo signals</p>
          <p>✅ When market opens, real signals will flow automatically</p>
        </div>
      </div>
    </div>
  )
}