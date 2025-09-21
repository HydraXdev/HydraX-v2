"use client"

import React from 'react'
import { motion } from 'framer-motion'
import {
  Bell,
  User,
  DollarSign,
  TrendingUp,
  AlertCircle,
  Battery,
  Activity
} from 'lucide-react'

export function HUDHeader() {
  return (
    <header className="bg-secondary border-b border-default">
      <div className="px-4 md:px-6 py-3">
        <div className="flex items-center justify-between">
          {/* Left Section - Stats */}
          <div className="flex items-center gap-4 md:gap-6">
            {/* Balance */}
            <div className="flex items-center gap-2">
              <DollarSign size={16} className="text-success" />
              <div className="flex flex-col">
                <span className="text-xs text-tertiary">Balance</span>
                <span className="text-sm font-semibold mono text-primary">$12,450</span>
              </div>
            </div>

            {/* Win Rate */}
            <div className="hidden sm:flex items-center gap-2">
              <TrendingUp size={16} className="text-mint" />
              <div className="flex flex-col">
                <span className="text-xs text-tertiary">Win Rate</span>
                <span className="text-sm font-semibold mono text-primary">68.5%</span>
              </div>
            </div>

            {/* Active Positions */}
            <div className="hidden md:flex items-center gap-2">
              <Activity size={16} className="text-cyan" />
              <div className="flex flex-col">
                <span className="text-xs text-tertiary">Positions</span>
                <span className="text-sm font-semibold mono text-primary">2/3</span>
              </div>
            </div>
          </div>

          {/* Center Section - Status Bar */}
          <div className="hidden lg:flex items-center gap-2 px-4 py-1.5 bg-overlay/50 rounded-full">
            <Battery size={14} className="text-success" />
            <span className="text-xs text-secondary">System Optimal</span>
            <div className="w-px h-4 bg-border-default mx-2" />
            <span className="text-xs text-mint mono">LONDON SESSION</span>
          </div>

          {/* Right Section - Actions */}
          <div className="flex items-center gap-2">
            {/* Risk Alert */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="relative p-2 rounded-lg hover:bg-overlay/50 transition-colors"
            >
              <AlertCircle size={20} className="text-warning" />
              <span className="absolute -top-1 -right-1 w-2 h-2 bg-danger rounded-full animate-pulse" />
            </motion.button>

            {/* Notifications */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="relative p-2 rounded-lg hover:bg-overlay/50 transition-colors"
            >
              <Bell size={20} className="text-tertiary" />
              <span className="absolute -top-1 -right-1 w-5 h-5 bg-mint rounded-full flex items-center justify-center">
                <span className="text-xs text-black font-bold">3</span>
              </span>
            </motion.button>

            {/* User Profile */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="p-2 rounded-lg hover:bg-overlay/50 transition-colors"
            >
              <User size={20} className="text-tertiary" />
            </motion.button>
          </div>
        </div>

        {/* Mobile Stats Row */}
        <div className="flex md:hidden items-center gap-4 mt-3 pt-3 border-t border-default">
          <div className="flex items-center gap-1.5">
            <TrendingUp size={14} className="text-mint" />
            <span className="text-xs text-tertiary">Win:</span>
            <span className="text-xs font-semibold text-primary">68.5%</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Activity size={14} className="text-cyan" />
            <span className="text-xs text-tertiary">Active:</span>
            <span className="text-xs font-semibold text-primary">2/3</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-mint">LONDON</span>
          </div>
        </div>
      </div>
    </header>
  )
}