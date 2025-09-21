"use client"

import React from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import {
  TrendingUp,
  TrendingDown,
  Clock,
  Shield,
  Zap,
  Check
} from 'lucide-react'
import { type Mission, useUI } from '@/lib/store'

interface MissionCardProps {
  mission: Mission
}

export function MissionCard({ mission }: MissionCardProps) {
  const { acceptMission, selectMission } = useUI()

  const {
    id,
    symbol,
    direction,
    entry,
    sl,
    tp,
    confidence,
    pattern,
    type,
    expiresIn,
    status
  } = mission
  const isLong = direction === 'BUY'
  const riskReward = Math.abs((tp - entry) / (entry - sl)).toFixed(2)

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={`
        panel p-4 cursor-pointer transition-all
        ${status === 'CLOSED' ? 'opacity-50' : ''}
        ${status === 'LIVE' ? 'border-mint glow-mint' : ''}
        ${status === 'ACCEPTED' ? 'border-cyan' : ''}
      `}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className={`
            w-8 h-8 rounded-lg flex items-center justify-center
            ${isLong ? 'bg-success/20' : 'bg-danger/20'}
          `}>
            {isLong ? (
              <TrendingUp size={16} className="text-success" />
            ) : (
              <TrendingDown size={16} className="text-danger" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-primary">{symbol}</span>
              <span className={`
                px-2 py-0.5 rounded text-xs font-medium
                ${type === 'SNIPER'
                  ? 'bg-cyan/20 text-cyan'
                  : 'bg-warning/20 text-warning'}
              `}>
                {type === 'SNIPER' ? '🎯' : '⚡'} {type}
              </span>
            </div>
            <span className="text-xs text-tertiary">{pattern}</span>
          </div>
        </div>

        {/* Confidence Badge */}
        <div className="flex flex-col items-end">
          <div className="flex items-center gap-1">
            <Shield size={14} className="text-mint" />
            <span className="text-sm font-bold text-mint">{confidence}%</span>
          </div>
          <span className="text-xs text-tertiary">R:R {riskReward}</span>
        </div>
      </div>

      {/* Price Levels */}
      <div className="space-y-2 mb-3">
        <div className="flex items-center justify-between text-xs">
          <span className="text-tertiary">Entry</span>
          <span className="mono font-medium text-primary">{entry.toFixed(5)}</span>
        </div>
        <div className="flex items-center justify-between text-xs">
          <span className="text-tertiary">Stop Loss</span>
          <span className="mono font-medium text-danger">{sl.toFixed(5)}</span>
        </div>
        <div className="flex items-center justify-between text-xs">
          <span className="text-tertiary">Take Profit</span>
          <span className="mono font-medium text-success">{tp.toFixed(5)}</span>
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-default">
        <div className="flex items-center gap-1">
          <Clock size={12} className={`
            ${expiresIn < 5 ? 'text-danger' : 'text-tertiary'}
          `} />
          <span className={`
            text-xs ${expiresIn < 5 ? 'text-danger font-medium' : 'text-tertiary'}
          `}>
            {expiresIn}m remaining
          </span>
        </div>

        {status === 'NEW' && (
          <div className="flex gap-2">
            <button
              onClick={() => {
                acceptMission(id)
              }}
              className="px-2 py-1 bg-mint/20 text-mint text-xs font-semibold rounded hover:bg-mint/30 transition-colors flex items-center gap-1"
            >
              <Check size={12} />
              Accept
            </button>
            <Link
              href={`/mission-brief?id=${id}`}
              onClick={() => selectMission(id)}
              className="px-2 py-1 bg-cyan/20 text-cyan text-xs font-semibold rounded hover:bg-cyan/30 transition-colors"
            >
              Brief
            </Link>
          </div>
        )}
        {status === 'ACCEPTED' && (
          <Link
            href={`/mission-brief?id=${id}`}
            onClick={() => selectMission(id)}
            className="px-3 py-1 bg-mint text-black text-xs font-semibold rounded-lg hover:bg-mint/90 transition-colors"
          >
            EXECUTE
          </Link>
        )}
        {status === 'LIVE' && (
          <div className="flex items-center gap-1">
            <Zap size={12} className="text-mint animate-pulse" />
            <span className="text-xs font-medium text-mint">LIVE</span>
          </div>
        )}
        {status === 'CLOSED' && (
          <span className="text-xs text-tertiary">CLOSED</span>
        )}
      </div>
    </motion.div>
  )
}