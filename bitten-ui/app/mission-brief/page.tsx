"use client"

import React, { useState, useEffect, useMemo } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { useUI } from '@/lib/store'
import {
  TrendingUp,
  TrendingDown,
  Shield,
  Clock,
  X,
  Check,
  Activity,
  BarChart3,
  Info,
  PlayCircle,
  StopCircle
} from 'lucide-react'

export default function MissionBriefPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const id = searchParams.get('id') || ''

  const { missions, acceptMission, executeMission, closeMission } = useUI()
  const mission = useMemo(() => missions.find(m => m.id === id), [missions, id])

  // Mock price ticker when LIVE
  const [currentPrice, setCurrentPrice] = useState(mission?.entry || 0)
  const [pnl, setPnl] = useState(0)

  useEffect(() => {
    if (!mission || mission.status !== 'LIVE') return

    let price = mission.entry
    const interval = setInterval(() => {
      // Simulate price movement
      const volatility = 0.0002 // 2 pips movement
      const drift = mission.direction === 'BUY' ? 0.00001 : -0.00001
      price = price + (Math.random() - 0.5) * volatility + drift

      setCurrentPrice(price)

      // Calculate P&L
      const pips = mission.direction === 'BUY'
        ? (price - mission.entry) * 10000
        : (mission.entry - price) * 10000

      setPnl(pips * 10) // $10 per pip for demo
    }, 1000)

    return () => clearInterval(interval)
  }, [mission])

  if (!mission) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-primary mb-2">Mission Not Found</h2>
          <p className="text-secondary mb-4">The requested mission could not be found.</p>
          <button
            onClick={() => router.push('/war-room')}
            className="px-4 py-2 bg-mint text-black font-semibold rounded-lg hover:bg-mint/90 transition-colors"
          >
            Return to War Room
          </button>
        </div>
      </div>
    )
  }

  const riskReward = Math.abs((mission.tp - mission.entry) / (mission.entry - mission.sl)).toFixed(2)
  const riskAmount = 100 // $100 risk per trade for demo
  const rewardAmount = riskAmount * parseFloat(riskReward)

  const handleAccept = () => {
    acceptMission(mission.id)
  }

  const handleExecute = () => {
    executeMission(mission.id)
  }

  const handleClose = () => {
    const outcome = pnl > 0 ? 'WIN' : 'LOSS'
    closeMission(mission.id, outcome)
    router.push('/war-room')
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-primary">Mission Brief</h1>
          <p className="text-sm text-secondary mt-1">ID: {mission.id}</p>
        </div>
        <div className="flex items-center gap-2">
          <div className={`px-3 py-1 rounded-lg text-sm font-medium ${
            mission.type === 'SNIPER'
              ? 'bg-cyan/20 text-cyan'
              : 'bg-warning/20 text-warning'
          }`}>
            {mission.type === 'SNIPER' ? '🎯' : '⚡'} {mission.type}
          </div>
          <div className="flex items-center gap-1">
            <Shield size={16} className="text-mint" />
            <span className="text-sm font-bold text-mint">{mission.confidence}%</span>
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Main Content - Chart Area */}
        <div className="lg:col-span-2 space-y-6">
          {/* Chart/Price Display */}
          <div className="panel aspect-[16/10] flex items-center justify-center relative overflow-hidden">
            {mission.status === 'LIVE' ? (
              <div className="w-full h-full p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-2xl font-bold text-primary">{mission.symbol}</span>
                      <div className={`
                        px-2 py-1 rounded text-xs font-medium
                        ${mission.direction === 'BUY'
                          ? 'bg-success/20 text-success'
                          : 'bg-danger/20 text-danger'}
                      `}>
                        {mission.direction === 'BUY' ? (
                          <TrendingUp size={14} className="inline mr-1" />
                        ) : (
                          <TrendingDown size={14} className="inline mr-1" />
                        )}
                        {mission.direction}
                      </div>
                    </div>
                    <span className="text-xs text-tertiary">{mission.pattern}</span>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center gap-2">
                      <Activity size={16} className="text-mint animate-pulse" />
                      <span className="text-xs text-mint font-medium">LIVE TRADE</span>
                    </div>
                  </div>
                </div>

                {/* Live Price Display */}
                <div className="flex items-center justify-center flex-col h-3/4">
                  <div className="text-5xl font-bold mono text-primary mb-2">
                    {currentPrice.toFixed(5)}
                  </div>
                  <div className={`text-2xl font-semibold ${pnl >= 0 ? 'text-success' : 'text-danger'}`}>
                    {pnl >= 0 ? '+' : ''}{pnl.toFixed(2)} USD
                  </div>
                  <div className="text-sm text-secondary mt-2">
                    {pnl >= 0 ? '+' : ''}{(pnl / 10).toFixed(1)} pips
                  </div>
                </div>

                {/* Price Levels */}
                <div className="grid grid-cols-3 gap-4 text-xs">
                  <div className="text-center">
                    <span className="text-danger">Stop Loss</span>
                    <p className="font-medium mono text-danger">{mission.sl.toFixed(5)}</p>
                    <p className="text-tertiary">
                      -{Math.abs((mission.entry - mission.sl) * 10000).toFixed(1)} pips
                    </p>
                  </div>
                  <div className="text-center">
                    <span className="text-primary">Entry</span>
                    <p className="font-medium mono text-primary">{mission.entry.toFixed(5)}</p>
                  </div>
                  <div className="text-center">
                    <span className="text-success">Take Profit</span>
                    <p className="font-medium mono text-success">{mission.tp.toFixed(5)}</p>
                    <p className="text-tertiary">
                      +{Math.abs((mission.tp - mission.entry) * 10000).toFixed(1)} pips
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="relative w-full h-full">
                <div className="absolute inset-0 bg-gradient-to-br from-mint/5 to-cyan/5" />

                {/* Static Chart Visualization */}
                <div className="relative w-full h-full p-6">
                  <div className="absolute top-6 left-6">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-2xl font-bold text-primary">{mission.symbol}</span>
                      <div className={`
                        px-2 py-1 rounded text-xs font-medium
                        ${mission.direction === 'BUY'
                          ? 'bg-success/20 text-success'
                          : 'bg-danger/20 text-danger'}
                      `}>
                        {mission.direction === 'BUY' ? (
                          <TrendingUp size={14} className="inline mr-1" />
                        ) : (
                          <TrendingDown size={14} className="inline mr-1" />
                        )}
                        {mission.direction}
                      </div>
                    </div>
                    <span className="text-xs text-tertiary">{mission.pattern}</span>
                  </div>

                  {/* Price levels visualization */}
                  <div className="absolute inset-x-6 top-1/4 space-y-8">
                    <div className="relative">
                      <div className="absolute -top-5 text-xs text-success font-medium">
                        TP: {mission.tp.toFixed(5)}
                      </div>
                      <div className="h-px bg-success/50 w-full" />
                    </div>

                    <div className="relative">
                      <div className="absolute -top-5 text-xs text-primary font-medium">
                        Entry: {mission.entry.toFixed(5)}
                      </div>
                      <div className="h-px bg-mint w-full" />
                      <div className="w-2 h-2 bg-mint rounded-full absolute -top-1 left-1/2 -translate-x-1/2" />
                    </div>

                    <div className="relative">
                      <div className="absolute -top-5 text-xs text-danger font-medium">
                        SL: {mission.sl.toFixed(5)}
                      </div>
                      <div className="h-px bg-danger/50 w-full" />
                    </div>
                  </div>

                  <div className="absolute bottom-6 left-6 flex items-center gap-4 text-xs text-tertiary">
                    <span>Chart snapshot coming soon</span>
                    <BarChart3 size={16} />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex gap-4">
            {mission.status === 'NEW' && (
              <>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleAccept}
                  className="flex-1 py-3 bg-mint text-black font-semibold rounded-lg hover:bg-mint/90 transition-colors flex items-center justify-center gap-2"
                >
                  <Check size={20} />
                  Accept Mission
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => router.push('/war-room')}
                  className="flex-1 py-3 bg-danger/20 text-danger font-semibold rounded-lg hover:bg-danger/30 transition-colors flex items-center justify-center gap-2"
                >
                  <X size={20} />
                  Decline
                </motion.button>
              </>
            )}

            {mission.status === 'ACCEPTED' && (
              <>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleExecute}
                  className="flex-1 py-3 bg-mint text-black font-semibold rounded-lg hover:bg-mint/90 transition-colors flex items-center justify-center gap-2"
                >
                  <PlayCircle size={20} />
                  Execute Trade
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => router.push('/war-room')}
                  className="py-3 px-6 bg-secondary text-primary font-semibold rounded-lg hover:bg-overlay transition-colors"
                >
                  Back
                </motion.button>
              </>
            )}

            {mission.status === 'LIVE' && (
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleClose}
                className="flex-1 py-3 bg-danger text-white font-semibold rounded-lg hover:bg-danger/90 transition-colors flex items-center justify-center gap-2"
              >
                <StopCircle size={20} />
                Close Position
              </motion.button>
            )}

            {mission.status === 'CLOSED' && (
              <div className="flex-1 panel p-4 text-center">
                <p className="text-secondary mb-2">Mission Completed</p>
                <button
                  onClick={() => router.push('/xp')}
                  className="text-mint text-sm hover:text-mint/80 transition-colors"
                >
                  View XP Rewards →
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Right Panel - Intel */}
        <div className="space-y-6">
          {/* Trade Parameters */}
          <div className="panel p-4">
            <h3 className="text-sm font-semibold text-primary mb-4">Trade Parameters</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-tertiary">Entry Price</span>
                <span className="text-sm font-medium mono text-primary">{mission.entry.toFixed(5)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-tertiary">Stop Loss</span>
                <span className="text-sm font-medium mono text-danger">{mission.sl.toFixed(5)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-tertiary">Take Profit</span>
                <span className="text-sm font-medium mono text-success">{mission.tp.toFixed(5)}</span>
              </div>
              <div className="border-t border-default pt-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-tertiary">Risk Amount</span>
                  <span className="text-sm font-medium text-danger">${riskAmount}</span>
                </div>
                <div className="flex items-center justify-between mt-2">
                  <span className="text-xs text-tertiary">Reward Target</span>
                  <span className="text-sm font-medium text-success">${rewardAmount.toFixed(0)}</span>
                </div>
                <div className="flex items-center justify-between mt-2">
                  <span className="text-xs text-tertiary">Risk:Reward</span>
                  <span className="text-sm font-medium text-mint">1:{riskReward}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Intel Panel */}
          <div className="panel p-4">
            <h3 className="text-sm font-semibold text-primary mb-4 flex items-center gap-2">
              <Info size={16} />
              Tactical Intel
            </h3>
            <div className="space-y-3 text-xs">
              <div>
                <span className="text-tertiary">Pattern Detected</span>
                <p className="text-primary font-medium mt-1">{mission.pattern.replace(/_/g, ' ')}</p>
              </div>
              <div>
                <span className="text-tertiary">Timeframe</span>
                <p className="text-primary font-medium mt-1">{mission.timeframe}</p>
              </div>
              <div>
                <span className="text-tertiary">Mission Type</span>
                <p className={`font-medium mt-1 ${
                  mission.type === 'SNIPER' ? 'text-cyan' : 'text-warning'
                }`}>
                  {mission.type}
                </p>
              </div>
              <div>
                <span className="text-tertiary">Position Size</span>
                <p className="text-primary font-medium mt-1">0.50 lots</p>
              </div>
              <div className="pt-3 border-t border-default">
                <span className="text-tertiary">Pattern Confidence</span>
                <div className="flex items-center justify-between mt-2">
                  <div className="flex-1 h-2 bg-overlay rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-mint to-cyan"
                      style={{ width: `${mission.confidence}%` }}
                    />
                  </div>
                  <span className="text-mint font-medium ml-2">{mission.confidence}%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Status/Timer */}
          <div className="panel p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock size={16} className={`
                  ${mission.status === 'LIVE' ? 'text-mint' : 'text-warning'}
                `} />
                <span className="text-xs text-tertiary">
                  {mission.status === 'LIVE' ? 'Trade Duration' : 'Mission Expires In'}
                </span>
              </div>
              <span className={`text-lg font-bold mono ${
                mission.status === 'LIVE' ? 'text-mint' : 'text-warning'
              }`}>
                {mission.status === 'LIVE' ? '00:42' : `${mission.expiresIn}:00`}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}