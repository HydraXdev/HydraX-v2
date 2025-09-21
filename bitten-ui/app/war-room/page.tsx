"use client"

import React from 'react'
import { motion } from 'framer-motion'
import { MissionCard } from '@/components/cards/MissionCard'
import { StatCard } from '@/components/cards/StatCard'
import { useUI } from '@/lib/store'
import {
  Activity,
  TrendingUp,
  Shield,
  Target,
  AlertTriangle,
  Zap,
  DollarSign,
  Clock,
  RefreshCw
} from 'lucide-react'

export default function WarRoomPage() {
  const { missions, balance, winRate, xp, seedDemo } = useUI()

  // Filter missions by status
  const newMissions = missions.filter(m => m.status === 'NEW' || m.status === 'ACCEPTED')
  const liveMissions = missions.filter(m => m.status === 'LIVE')
  const closedMissions = missions.filter(m => m.status === 'CLOSED')

  // Calculate active risk
  const activeRisk = liveMissions.length * 2 // 2% per position
  const maxRisk = 6 // 6% daily max

  // Mock live feed with real mission data
  const mockLiveFeed = [
    ...(liveMissions.length > 0
      ? liveMissions.map(m => ({
          time: new Date().toLocaleTimeString('en-US', { hour12: false }),
          message: `${m.symbol} position LIVE (${m.confidence}% confidence)`,
          type: 'trade' as const
        }))
      : []),
    { time: '14:32:15', message: 'EURUSD signal generated (82% confidence)', type: 'signal' as const },
    { time: '14:30:21', message: 'London session started', type: 'info' as const },
    { time: '14:28:55', message: 'Take profit hit on USDJPY +45 pips', type: 'win' as const },
    { time: '14:27:12', message: 'High volatility detected on XAUUSD', type: 'alert' as const }
  ].slice(0, 5)

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-primary">War Room</h1>
          <p className="text-sm text-secondary mt-1">Tactical command center</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={seedDemo}
            className="px-4 py-2 bg-secondary text-primary font-medium rounded-lg hover:bg-overlay transition-colors flex items-center gap-2"
          >
            <RefreshCw size={16} />
            Reset Demo
          </button>
          <button className="px-4 py-2 bg-mint text-black font-semibold rounded-lg hover:bg-mint/90 transition-colors">
            Deploy Capital
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          title="Balance"
          value={`$${balance.toLocaleString()}`}
          change={balance > 12450 ? ((balance - 12450) / 12450) * 100 : 0}
          icon={DollarSign}
          accent="success"
        />
        <StatCard
          title="Win Rate"
          value={`${winRate.toFixed(1)}%`}
          change={winRate > 68.5 ? winRate - 68.5 : winRate - 68.5}
          changeLabel="session"
          icon={TrendingUp}
          accent="mint"
        />
        <StatCard
          title="Active Trades"
          value={`${liveMissions.length}/3`}
          icon={Activity}
          accent="cyan"
        />
        <StatCard
          title="Total XP"
          value={xp.toLocaleString()}
          change={12}
          icon={Shield}
          accent="warning"
        />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Mission Queue */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-primary flex items-center gap-2">
              <Target size={20} className="text-mint" />
              Mission Queue
            </h2>
            <span className="text-xs text-tertiary">
              {newMissions.length} available | {liveMissions.length} active | {closedMissions.length} closed
            </span>
          </div>

          <div className="space-y-3">
            {newMissions.length === 0 && liveMissions.length === 0 ? (
              <div className="panel p-8 text-center">
                <p className="text-secondary mb-2">No missions available</p>
                <button
                  onClick={seedDemo}
                  className="text-mint text-sm hover:text-mint/80 transition-colors"
                >
                  Generate demo missions
                </button>
              </div>
            ) : (
              <>
                {liveMissions.map((mission) => (
                  <MissionCard key={mission.id} mission={mission} />
                ))}
                {newMissions.map((mission) => (
                  <MissionCard key={mission.id} mission={mission} />
                ))}
              </>
            )}
          </div>
        </div>

        {/* Side Panels */}
        <div className="space-y-6">
          {/* Risk Meter */}
          <div className="panel p-4">
            <h3 className="text-sm font-semibold text-primary mb-3 flex items-center gap-2">
              <AlertTriangle size={16} className="text-warning" />
              Risk Meter
            </h3>
            <div className="space-y-3">
              <div>
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="text-tertiary">Daily Risk</span>
                  <span className="text-primary font-medium">{activeRisk}% / {maxRisk}%</span>
                </div>
                <div className="h-2 bg-overlay rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${(activeRisk / maxRisk) * 100}%` }}
                    transition={{ duration: 1, ease: 'easeOut' }}
                    className={`h-full ${
                      activeRisk > maxRisk * 0.8
                        ? 'bg-danger'
                        : activeRisk > maxRisk * 0.5
                        ? 'bg-warning'
                        : 'bg-gradient-to-r from-mint to-cyan'
                    }`}
                  />
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="text-tertiary">Positions</span>
                  <span className="text-primary font-medium">{liveMissions.length} / 3</span>
                </div>
                <div className="h-2 bg-overlay rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${(liveMissions.length / 3) * 100}%` }}
                    transition={{ duration: 1, ease: 'easeOut' }}
                    className="h-full bg-cyan"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Live Feed */}
          <div className="panel p-4">
            <h3 className="text-sm font-semibold text-primary mb-3 flex items-center gap-2">
              <Zap size={16} className="text-cyan" />
              Live Feed
            </h3>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {mockLiveFeed.map((item, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-start gap-2 text-xs"
                >
                  <Clock size={10} className="text-tertiary mt-0.5" />
                  <div className="flex-1">
                    <span className="text-tertiary">{item.time}</span>
                    <p className={`
                      ${item.type === 'signal' && 'text-cyan'}
                      ${item.type === 'trade' && 'text-primary'}
                      ${item.type === 'win' && 'text-success'}
                      ${item.type === 'alert' && 'text-warning'}
                      ${item.type === 'info' && 'text-secondary'}
                    `}>
                      {item.message}
                    </p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Performance Snapshot */}
          <div className="panel p-4">
            <h3 className="text-sm font-semibold text-primary mb-3">
              Performance Snapshot
            </h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-tertiary">Best Pattern</span>
                <span className="text-mint font-medium">LIQUIDITY_SWEEP (78%)</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-tertiary">Best Pair</span>
                <span className="text-cyan font-medium">EURUSD (+234 pips)</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-tertiary">Session P&L</span>
                <span className={`font-medium ${balance > 12450 ? 'text-success' : 'text-danger'}`}>
                  ${Math.abs(balance - 12450).toFixed(0)}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-tertiary">Total Missions</span>
                <span className="text-primary font-medium">{missions.length}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}