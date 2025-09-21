"use client"

import React from 'react'
import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, Minus, LucideIcon } from 'lucide-react'

interface StatCardProps {
  title: string
  value: string | number
  change?: number
  changeLabel?: string
  icon?: LucideIcon
  accent?: 'mint' | 'cyan' | 'warning' | 'danger' | 'success'
  size?: 'sm' | 'md' | 'lg'
}

export function StatCard({
  title,
  value,
  change,
  changeLabel,
  icon: Icon,
  accent = 'mint',
  size = 'md'
}: StatCardProps) {
  const sizeClasses = {
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6'
  }

  const valueSizeClasses = {
    sm: 'text-lg',
    md: 'text-2xl',
    lg: 'text-3xl'
  }

  const accentClasses = {
    mint: 'text-mint',
    cyan: 'text-cyan',
    warning: 'text-warning',
    danger: 'text-danger',
    success: 'text-success'
  }

  const renderTrend = () => {
    if (change === undefined) return null

    const TrendIcon = change > 0 ? TrendingUp : change < 0 ? TrendingDown : Minus
    const trendColor = change > 0 ? 'text-success' : change < 0 ? 'text-danger' : 'text-tertiary'

    return (
      <div className={`flex items-center gap-1 ${trendColor}`}>
        <TrendIcon size={14} />
        <span className="text-xs font-medium">
          {change > 0 && '+'}{change}%
        </span>
        {changeLabel && (
          <span className="text-xs text-tertiary ml-1">{changeLabel}</span>
        )}
      </div>
    )
  }

  return (
    <motion.div
      whileHover={{ y: -2 }}
      className={`panel ${sizeClasses[size]} transition-all`}
    >
      <div className="flex items-start justify-between mb-2">
        <span className="text-xs text-tertiary uppercase tracking-wide">{title}</span>
        {Icon && (
          <Icon size={20} className={`${accentClasses[accent]} opacity-50`} />
        )}
      </div>

      <div className={`${valueSizeClasses[size]} font-bold text-primary mono mb-2`}>
        {value}
      </div>

      {renderTrend()}
    </motion.div>
  )
}