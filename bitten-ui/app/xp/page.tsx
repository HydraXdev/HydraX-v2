"use client"

import React from 'react'
import { motion } from 'framer-motion'
import { useUI } from '@/lib/store'
import {
  Trophy,
  TrendingUp,
  Target,
  Zap,
  Award,
  Star,
  ChevronRight,
  Lock,
  Unlock,
  Gift,
  Flame,
  Shield,
  Clock
} from 'lucide-react'

const badges = [
  { id: 1, name: 'First Blood', description: 'Complete your first trade', icon: Target, unlocked: true, rarity: 'common' },
  { id: 2, name: 'Sharpshooter', description: '10 winning trades in a row', icon: Trophy, unlocked: true, rarity: 'rare' },
  { id: 3, name: 'Speed Demon', description: 'Execute 5 trades in one hour', icon: Zap, unlocked: false, rarity: 'epic' },
  { id: 4, name: 'Risk Master', description: 'Maintain 70% win rate for 30 days', icon: Shield, unlocked: false, rarity: 'legendary' }
]

const shopItems = [
  { id: 1, name: 'Sniper Shot', description: '90% confidence bypass', cost: 500, icon: Target, available: true },
  { id: 2, name: 'Double Down', description: '4% risk on next trade', cost: 1000, icon: TrendingUp, available: true },
  { id: 3, name: 'Rapid Fire', description: 'No cooldown for 1 hour', cost: 750, icon: Zap, available: false },
  { id: 4, name: 'XP Boost', description: '2x XP for 10 trades', cost: 1000, icon: Star, available: true }
]

export default function XPDashboardPage() {
  const { xp, xpEvents } = useUI()

  // Calculate level based on XP
  const calculateLevel = (totalXP: number) => {
    if (totalXP < 500) return 1
    if (totalXP < 1500) return Math.floor(totalXP / 500) + 1
    if (totalXP < 3500) return Math.floor((totalXP - 500) / 1000) + 2
    if (totalXP < 7000) return Math.floor((totalXP - 1500) / 2000) + 3
    return Math.floor((totalXP - 3500) / 3500) + 5
  }

  const currentLevel = calculateLevel(xp)
  const levelThresholds = [0, 500, 1000, 1500, 2500, 3500, 5500, 7500, 10000, 13000, 16000]
  const currentLevelXP = levelThresholds[currentLevel - 1] || 0
  const nextLevelXP = levelThresholds[currentLevel] || currentLevelXP + 3500
  const progressXP = xp - currentLevelXP
  const neededXP = nextLevelXP - currentLevelXP
  const progressPercentage = (progressXP / neededXP) * 100

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-primary">XP Dashboard</h1>
          <p className="text-sm text-secondary mt-1">Level up your trading game</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-xs text-tertiary">Total XP</p>
            <p className="text-2xl font-bold text-warning">{xp.toLocaleString()}</p>
          </div>
          <button className="px-4 py-2 bg-warning text-black font-semibold rounded-lg hover:bg-warning/90 transition-colors">
            XP Shop
          </button>
        </div>
      </div>

      {/* Level Progress */}
      <div className="panel p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-gradient-to-br from-warning to-mint rounded-xl flex items-center justify-center">
              <span className="text-2xl font-bold text-black">{currentLevel}</span>
            </div>
            <div>
              <h2 className="text-xl font-semibold text-primary">Level {currentLevel}</h2>
              <p className="text-sm text-secondary">
                {currentLevel < 10 ? 'Novice Trader' :
                 currentLevel < 20 ? 'Competent Trader' :
                 currentLevel < 30 ? 'Expert Trader' : 'Master Trader'}
              </p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-xs text-tertiary">Next Level</p>
            <p className="text-lg font-semibold text-primary">Level {currentLevel + 1}</p>
          </div>
        </div>

        {/* XP Progress Bar */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-secondary">{progressXP.toLocaleString()} XP</span>
            <span className="text-tertiary">{neededXP.toLocaleString()} XP</span>
          </div>
          <div className="h-3 bg-overlay rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(100, progressPercentage)}%` }}
              transition={{ duration: 1, ease: 'easeOut' }}
              className="h-full bg-gradient-to-r from-warning to-mint"
            />
          </div>
          <p className="text-xs text-tertiary text-center">
            {(nextLevelXP - xp).toLocaleString()} XP to next level
          </p>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Badges */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-lg font-semibold text-primary flex items-center gap-2">
            <Award size={20} className="text-warning" />
            Achievements
          </h3>

          <div className="grid grid-cols-2 gap-4">
            {badges.map((badge) => {
              const Icon = badge.icon
              const rarityColors = {
                common: 'from-gray-500 to-gray-600',
                rare: 'from-blue-500 to-blue-600',
                epic: 'from-purple-500 to-purple-600',
                legendary: 'from-yellow-500 to-orange-500'
              }

              return (
                <motion.div
                  key={badge.id}
                  whileHover={badge.unlocked ? { scale: 1.02 } : {}}
                  className={`
                    panel p-4 transition-all
                    ${!badge.unlocked && 'opacity-50 grayscale'}
                  `}
                >
                  <div className="flex items-start gap-3">
                    <div className={`
                      w-12 h-12 rounded-lg flex items-center justify-center
                      ${badge.unlocked
                        ? `bg-gradient-to-br ${rarityColors[badge.rarity as keyof typeof rarityColors]}`
                        : 'bg-overlay'}
                    `}>
                      <Icon size={24} className={badge.unlocked ? 'text-white' : 'text-tertiary'} />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="text-sm font-semibold text-primary">{badge.name}</h4>
                        {badge.unlocked ? (
                          <Unlock size={12} className="text-success" />
                        ) : (
                          <Lock size={12} className="text-tertiary" />
                        )}
                      </div>
                      <p className="text-xs text-secondary mt-1">{badge.description}</p>
                    </div>
                  </div>
                </motion.div>
              )
            })}
          </div>
        </div>

        {/* Recent XP Events */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-primary flex items-center gap-2">
            <Flame size={20} className="text-danger" />
            Recent Activity
          </h3>

          <div className="panel p-4 space-y-3 max-h-96 overflow-y-auto">
            {xpEvents.length === 0 ? (
              <p className="text-sm text-secondary text-center py-4">No XP events yet</p>
            ) : (
              xpEvents.slice(0, 10).map((event, index) => (
                <motion.div
                  key={event.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="flex items-center justify-between border-b border-default pb-2 last:border-0"
                >
                  <div className="flex-1">
                    <p className="text-sm text-primary">{event.details}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <Clock size={10} className="text-tertiary" />
                      <p className="text-xs text-tertiary">
                        {new Date(event.at).toLocaleTimeString('en-US', {
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </p>
                    </div>
                  </div>
                  <div className={`
                    px-2 py-1 rounded text-xs font-bold
                    ${event.type === 'WIN' && 'bg-success/20 text-success'}
                    ${event.type === 'LOSS' && 'bg-danger/20 text-danger'}
                    ${event.type === 'BONUS' && 'bg-warning/20 text-warning'}
                    ${event.type === 'ACCEPT' && 'bg-cyan/20 text-cyan'}
                    ${event.type === 'CLOSE' && 'bg-mint/20 text-mint'}
                  `}>
                    {event.delta > 0 ? '+' : ''}{event.delta} XP
                  </div>
                </motion.div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* XP Shop Preview */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-primary flex items-center gap-2">
            <Gift size={20} className="text-mint" />
            XP Shop
          </h3>
          <button className="text-sm text-mint hover:text-mint/80 transition-colors flex items-center gap-1">
            View All
            <ChevronRight size={16} />
          </button>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
          {shopItems.map((item) => {
            const Icon = item.icon
            const canAfford = xp >= item.cost

            return (
              <motion.div
                key={item.id}
                whileHover={{ y: -2 }}
                className={`
                  panel p-4 transition-all
                  ${!item.available && 'opacity-50'}
                  ${!canAfford && 'opacity-75'}
                `}
              >
                <div className="flex items-center justify-center w-12 h-12 bg-mint/20 rounded-lg mb-3">
                  <Icon size={24} className="text-mint" />
                </div>
                <h4 className="text-sm font-semibold text-primary">{item.name}</h4>
                <p className="text-xs text-secondary mt-1 mb-3">{item.description}</p>
                <div className="flex items-center justify-between">
                  <span className={`text-sm font-bold ${canAfford ? 'text-warning' : 'text-tertiary'}`}>
                    {item.cost} XP
                  </span>
                  {item.available && canAfford ? (
                    <button className="px-3 py-1 bg-mint/20 text-mint text-xs font-semibold rounded hover:bg-mint/30 transition-colors">
                      Buy
                    </button>
                  ) : !item.available ? (
                    <span className="text-xs text-tertiary">Locked</span>
                  ) : (
                    <span className="text-xs text-tertiary">Need XP</span>
                  )}
                </div>
              </motion.div>
            )
          })}
        </div>
      </div>
    </div>
  )
}