"use client"

import React, { useState, useEffect, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { useUI } from '@/lib/store'
import { usePriceSubscription } from '@/lib/useEventIntegration'
import {
  Activity,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Target,
  Clock,
  BarChart3,
  Volume2,
  VolumeX,
  ArrowLeft,
  StopCircle,
  AlertTriangle,
  Zap,
  Eye,
  MonitorSpeaker
} from 'lucide-react'

interface PriceData {
  symbol: string
  bid: number
  ask: number
  change: number
  changePercent: number
  timestamp: number
}

function LiveTradeContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const ticket = searchParams.get('ticket')

  const { missions, closeMission } = useUI()
  const trade = missions.find(m => m.id === ticket && m.status === 'LIVE')

  // State management
  const [currentPrice, setCurrentPrice] = useState<PriceData | null>(null)
  const [pnl, setPnl] = useState(0)
  const [runningPnl, setRunningPnl] = useState(0)
  const [maxFavorable, setMaxFavorable] = useState(0)
  const [maxAdverse, setMaxAdverse] = useState(0)
  const [tickData, setTickData] = useState<Array<{ price: number, time: number }>>([])
  const [soundEnabled, setSoundEnabled] = useState(true)
  const [balance] = useState(10000) // Mock balance
  const [equity, setEquity] = useState(10000)

  // Live price simulation
  useEffect(() => {
    if (!trade) return

    let price = trade.entry
    const interval = setInterval(() => {
      const volatility = 0.0002 // 2 pips
      const drift = trade.direction === 'BUY' ? 0.00001 : -0.00001
      price = price + (Math.random() - 0.5) * volatility + drift

      const change = price - trade.entry
      const changePercent = (change / trade.entry) * 100

      setCurrentPrice({
        symbol: trade.symbol,
        bid: price - 0.00001,
        ask: price + 0.00001,
        change,
        changePercent,
        timestamp: Date.now()
      })

      // Calculate P&L
      const pips = trade.direction === 'BUY'
        ? (price - trade.entry) * 10000
        : (trade.entry - price) * 10000

      const currentPnl = pips * 10 // $10 per pip
      setPnl(currentPnl)
      setRunningPnl(currentPnl)
      setEquity(balance + currentPnl)

      // Track max favorable/adverse
      setMaxFavorable(prev => Math.max(prev, currentPnl))
      setMaxAdverse(prev => Math.min(prev, currentPnl))

      // Add to tick data for chart
      setTickData(prev => [
        ...prev.slice(-50), // Keep last 50 ticks
        { price, time: Date.now() }
      ])

    }, 1000)

    return () => clearInterval(interval)
  }, [trade, balance])

  const handleClose = () => {
    if (trade) {
      const outcome = pnl > 0 ? 'WIN' : 'LOSS'
      closeMission(trade.id, outcome)
      router.push('/war-room')
    }
  }

  // Error state
  if (!trade) {
    return (
      <div className="min-h-screen bg-primary flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <AlertTriangle className="w-16 h-16 mx-auto text-danger mb-4" />
          <h1 className="text-2xl font-tactical text-danger mb-2">Trade Not Found</h1>
          <p className="text-secondary mb-6">No active trade found with this ticket ID.</p>
          <button onClick={() => router.push('/war-room')} className="btn-primary">
            Return to War Room
          </button>
        </motion.div>
      </div>
    )
  }

  const getDistanceToSL = () => {
    if (!currentPrice) return 0
    const price = trade.direction === 'BUY' ? currentPrice.bid : currentPrice.ask
    return Math.abs(price - trade.sl) * 10000 // in pips
  }

  const getDistanceToTP = () => {
    if (!currentPrice) return 0
    const price = trade.direction === 'BUY' ? currentPrice.bid : currentPrice.ask
    return Math.abs(price - trade.tp) * 10000 // in pips
  }

  return (
    <div className="min-h-screen bg-primary text-primary">
      {/* Military HUD Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="border-b border-active backdrop-blur-sm bg-overlay/30 sticky top-0 z-50"
      >
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/war-room')}
                className="p-2 hover:bg-overlay/50 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-6 h-6 text-secondary" />
              </button>
              <MonitorSpeaker className="w-8 h-8 text-mint pulse-glow" />
              <div>
                <h1 className="text-2xl font-tactical text-mint neon-glow">Live Monitor</h1>
                <p className="text-sm text-secondary font-code">Ticket: {trade.id}</p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <button
                onClick={() => setSoundEnabled(!soundEnabled)}
                className={`p-2 rounded-lg transition-colors ${
                  soundEnabled ? 'text-mint bg-mint/10' : 'text-secondary bg-secondary/10'
                }`}
              >
                {soundEnabled ? <Volume2 className="w-5 h-5" /> : <VolumeX className="w-5 h-5" />}
              </button>

              <div className="text-right">
                <div className="flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-mint animate-pulse" />
                  <span className="text-mint font-tactical text-sm">LIVE</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Chart Area */}
          <div className="lg:col-span-2 space-y-6">
            {/* Live Price Display */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="hud-panel-accent p-6"
            >
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-4">
                  <div className="text-3xl font-tactical text-mint neon-glow">{trade.symbol}</div>
                  <div className={`px-3 py-1 rounded font-tactical text-lg ${
                    trade.direction === 'BUY'
                      ? 'bg-mint/20 text-mint border border-mint/30'
                      : 'bg-danger/20 text-danger border border-danger/30'
                  }`}>
                    {trade.direction === 'BUY' ? (
                      <TrendingUp className="w-5 h-5 inline mr-2" />
                    ) : (
                      <TrendingDown className="w-5 h-5 inline mr-2" />
                    )}
                    {trade.direction}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-secondary">PATTERN</div>
                  <div className="text-lg font-tactical text-cyan">{trade.pattern.replace(/_/g, ' ')}</div>
                </div>
              </div>

              {/* Current Price */}
              <div className="text-center mb-8">
                <div className="text-6xl font-code text-mint mb-2 neon-glow">
                  {currentPrice?.ask.toFixed(5) || trade.entry.toFixed(5)}
                </div>
                <div className={`text-2xl font-code ${
                  (currentPrice?.change || 0) >= 0 ? 'text-mint' : 'text-danger'
                }`}>
                  {(currentPrice?.change || 0) >= 0 ? '+' : ''}{((currentPrice?.change || 0) * 10000).toFixed(1)} pips
                </div>
              </div>

              {/* P&L Display */}
              <div className="grid grid-cols-3 gap-6 mb-6">
                <div className="text-center">
                  <div className="text-sm text-secondary mb-1">CURRENT P&L</div>
                  <div className={`text-3xl font-code neon-glow ${pnl >= 0 ? 'text-mint' : 'text-danger'}`}>
                    {pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}
                  </div>
                  <div className="text-sm text-secondary">
                    {pnl >= 0 ? '+' : ''}{(pnl / 10).toFixed(1)} pips
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-sm text-secondary mb-1">MAX FAVORABLE</div>
                  <div className="text-2xl font-code text-mint neon-glow">
                    +${maxFavorable.toFixed(2)}
                  </div>
                  <div className="text-sm text-secondary">
                    +{(maxFavorable / 10).toFixed(1)} pips
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-sm text-secondary mb-1">MAX ADVERSE</div>
                  <div className="text-2xl font-code text-danger neon-glow">
                    ${maxAdverse.toFixed(2)}
                  </div>
                  <div className="text-sm text-secondary">
                    {(maxAdverse / 10).toFixed(1)} pips
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-4">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleClose}
                  className="btn-danger flex-1 text-lg py-4"
                >
                  <StopCircle className="w-5 h-5 mr-2" />
                  Close Position
                </motion.button>

                <button
                  onClick={() => router.push(`/mission-brief?id=${trade.id}`)}
                  className="btn-secondary px-8"
                >
                  <Eye className="w-5 h-5 mr-2" />
                  View Brief
                </button>
              </div>
            </motion.div>

            {/* Price Levels Chart */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="chart-container p-6"
            >
              <h3 className="text-lg font-tactical text-mint mb-4">Price Levels</h3>
              <div className="relative h-32 bg-secondary/30 rounded-lg p-4">
                {/* TP Line */}
                <div className="absolute top-2 left-4 right-4 border-t-2 border-mint border-dashed">
                  <div className="absolute -top-6 left-0 text-xs text-mint font-code">
                    TP: {trade.tp.toFixed(5)} ({getDistanceToTP().toFixed(1)} pips away)
                  </div>
                </div>

                {/* Current Price Line */}
                <div className="absolute top-1/2 left-4 right-4 border-t-2 border-cyan">
                  <div className="absolute -top-6 left-0 text-xs text-cyan font-code">
                    Current: {currentPrice?.ask.toFixed(5) || trade.entry.toFixed(5)}
                  </div>
                  <div className="w-2 h-2 bg-cyan rounded-full absolute -top-1 left-1/2 -translate-x-1/2 animate-pulse" />
                </div>

                {/* Entry Line */}
                <div className="absolute top-2/3 left-4 right-4 border-t border-warning border-dotted">
                  <div className="absolute -bottom-5 left-0 text-xs text-warning font-code">
                    Entry: {trade.entry.toFixed(5)}
                  </div>
                </div>

                {/* SL Line */}
                <div className="absolute bottom-2 left-4 right-4 border-t-2 border-danger border-dashed">
                  <div className="absolute -bottom-6 left-0 text-xs text-danger font-code">
                    SL: {trade.sl.toFixed(5)} ({getDistanceToSL().toFixed(1)} pips away)
                  </div>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Sidebar - Account Info & Controls */}
          <div className="space-y-6">
            {/* Account Summary */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="hud-panel p-4"
            >
              <div className="flex items-center space-x-2 mb-4">
                <DollarSign className="w-5 h-5 text-mint" />
                <span className="font-tactical text-mint">Account Status</span>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-secondary">Balance:</span>
                  <span className="font-code text-primary">${balance.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-secondary">Equity:</span>
                  <span className={`font-code ${equity >= balance ? 'text-mint' : 'text-danger'}`}>
                    ${equity.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-secondary">Margin:</span>
                  <span className="font-code text-primary">$85.50</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-secondary">Free Margin:</span>
                  <span className="font-code text-mint">${(equity - 85.50).toLocaleString()}</span>
                </div>
              </div>
            </motion.div>

            {/* Trade Details */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
              className="hud-panel p-4"
            >
              <div className="flex items-center space-x-2 mb-4">
                <Target className="w-5 h-5 text-cyan" />
                <span className="font-tactical text-cyan">Trade Details</span>
              </div>

              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-secondary">Symbol:</span>
                  <span className="font-code text-primary">{trade.symbol}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-secondary">Direction:</span>
                  <span className={`font-code ${trade.direction === 'BUY' ? 'text-mint' : 'text-danger'}`}>
                    {trade.direction}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-secondary">Volume:</span>
                  <span className="font-code text-primary">0.50 lots</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-secondary">Entry:</span>
                  <span className="font-code text-warning">{trade.entry.toFixed(5)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-secondary">Stop Loss:</span>
                  <span className="font-code text-danger">{trade.sl.toFixed(5)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-secondary">Take Profit:</span>
                  <span className="font-code text-mint">{trade.tp.toFixed(5)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-secondary">Confidence:</span>
                  <span className="font-code text-mint">{trade.confidence}%</span>
                </div>
              </div>
            </motion.div>

            {/* Trade Timer */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4 }}
              className="hud-panel p-4"
            >
              <div className="flex items-center space-x-2 mb-4">
                <Clock className="w-5 h-5 text-warning" />
                <span className="font-tactical text-warning">Trade Duration</span>
              </div>

              <div className="text-center">
                <div className="text-2xl font-code text-mint neon-glow">
                  00:42:15
                </div>
                <div className="text-sm text-secondary mt-1">
                  Since execution
                </div>
              </div>
            </motion.div>

            {/* Quick Actions */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.5 }}
              className="hud-panel p-4"
            >
              <div className="flex items-center space-x-2 mb-4">
                <Zap className="w-5 h-5 text-warning" />
                <span className="font-tactical text-warning">Quick Actions</span>
              </div>

              <div className="space-y-3">
                <button className="btn-secondary w-full text-sm py-2">
                  Modify SL/TP
                </button>
                <button className="btn-secondary w-full text-sm py-2">
                  Break Even
                </button>
                <button className="btn-secondary w-full text-sm py-2">
                  Trail Stop
                </button>
              </div>
            </motion.div>

            {/* Market Info */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.6 }}
              className="hud-panel p-4"
            >
              <div className="flex items-center space-x-2 mb-4">
                <BarChart3 className="w-5 h-5 text-cyan" />
                <span className="font-tactical text-cyan">Market Info</span>
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-secondary">Spread:</span>
                  <span className="font-code text-primary">1.2 pips</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-secondary">Session:</span>
                  <span className="text-primary">London</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-secondary">Volatility:</span>
                  <span className="text-primary">Medium</span>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function LiveTradePage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-primary" />}>
      <LiveTradeContent />
    </Suspense>
  )
}