"use client"

import React, { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { motion } from 'framer-motion'
import {
  Target,
  FileText,
  Trophy,
  Settings,
  Menu,
  X,
  TrendingUp,
  Shield,
  Zap
} from 'lucide-react'

const navItems = [
  {
    path: '/war-room',
    label: 'War Room',
    icon: Target,
    accent: 'mint'
  },
  {
    path: '/mission-brief',
    label: 'Mission Brief',
    icon: FileText,
    accent: 'cyan'
  },
  {
    path: '/xp',
    label: 'XP Dashboard',
    icon: Trophy,
    accent: 'warning'
  },
  {
    path: '/settings',
    label: 'Settings',
    icon: Settings,
    accent: 'secondary'
  }
]

export function SideNav() {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [isMobileOpen, setIsMobileOpen] = useState(false)
  const pathname = usePathname()

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsMobileOpen(!isMobileOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-secondary rounded-lg"
      >
        {isMobileOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* Mobile Backdrop */}
      {isMobileOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Navigation Sidebar */}
      <motion.nav
        initial={false}
        animate={{
          width: isCollapsed ? '80px' : '240px',
          x: isMobileOpen ? 0 : -240
        }}
        className={`
          fixed lg:relative h-screen bg-secondary border-r border-default
          flex flex-col z-40 transition-all duration-300
          ${isMobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        {/* Logo/Brand */}
        <div className="p-4 border-b border-default">
          <motion.div
            className="flex items-center gap-3"
            animate={{ justifyContent: isCollapsed ? 'center' : 'flex-start' }}
          >
            <div className="w-10 h-10 bg-mint rounded-lg flex items-center justify-center">
              <Shield className="w-6 h-6 text-black" />
            </div>
            {!isCollapsed && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex flex-col"
              >
                <span className="text-sm font-semibold text-primary">BITTEN</span>
                <span className="text-xs text-secondary">Tactical Trading</span>
              </motion.div>
            )}
          </motion.div>
        </div>

        {/* Navigation Items */}
        <div className="flex-1 py-4">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.path
            const accentClass = `text-${item.accent}`

            return (
              <Link
                key={item.path}
                href={item.path}
                className={`
                  flex items-center gap-3 px-4 py-3 mx-2 rounded-lg
                  transition-all duration-200 group
                  ${isActive ? 'bg-overlay border border-active' : 'hover:bg-overlay/50'}
                `}
              >
                <Icon
                  size={20}
                  className={`
                    transition-colors
                    ${isActive ? accentClass : 'text-tertiary group-hover:text-primary'}
                  `}
                />
                {!isCollapsed && (
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className={`
                      text-sm font-medium
                      ${isActive ? 'text-primary' : 'text-secondary group-hover:text-primary'}
                    `}
                  >
                    {item.label}
                  </motion.span>
                )}
              </Link>
            )
          })}
        </div>

        {/* Status Indicators */}
        <div className="p-4 border-t border-default">
          <div className="space-y-2">
            {/* Connection Status */}
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-success rounded-full animate-pulse" />
              {!isCollapsed && (
                <span className="text-xs text-secondary">Connected</span>
              )}
            </div>

            {/* Active Signals */}
            <div className="flex items-center gap-2">
              <Zap size={14} className="text-warning" />
              {!isCollapsed && (
                <span className="text-xs text-secondary">3 Active</span>
              )}
            </div>
          </div>
        </div>

        {/* Collapse Toggle (Desktop Only) */}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="hidden lg:flex items-center justify-center p-3 border-t border-default hover:bg-overlay/50 transition-colors"
        >
          <motion.div
            animate={{ rotate: isCollapsed ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <TrendingUp size={16} className="text-tertiary" />
          </motion.div>
        </button>
      </motion.nav>
    </>
  )
}