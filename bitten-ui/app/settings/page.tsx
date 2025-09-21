"use client"

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import {
  User,
  Bell,
  Shield,
  Palette,
  Moon,
  Sun,
  Monitor,
  ChevronRight,
  AlertTriangle,
  Save
} from 'lucide-react'

export default function SettingsPage() {
  const [theme, setTheme] = useState<'dark' | 'light' | 'auto'>('dark')
  const [notifications, setNotifications] = useState({
    signals: true,
    trades: true,
    wins: true,
    losses: false,
    system: true
  })
  const [riskSettings, setRiskSettings] = useState({
    maxDailyRisk: 6,
    maxPositions: 3,
    autoStop: true,
    trailingStop: false
  })

  const handleSave = () => {
    // In real app, would save to backend
    console.log('Settings saved')
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-primary">Settings</h1>
          <p className="text-sm text-secondary mt-1">Customize your trading experience</p>
        </div>
        <button
          onClick={handleSave}
          className="px-4 py-2 bg-mint text-black font-semibold rounded-lg hover:bg-mint/90 transition-colors flex items-center gap-2"
        >
          <Save size={16} />
          Save Changes
        </button>
      </div>

      {/* Profile Section */}
      <div className="panel p-6">
        <h2 className="text-lg font-semibold text-primary mb-4 flex items-center gap-2">
          <User size={20} className="text-mint" />
          Profile
        </h2>
        <div className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-tertiary">Callsign</label>
              <input
                type="text"
                defaultValue="COMMANDER"
                className="w-full mt-1 px-3 py-2 bg-overlay border border-default rounded-lg text-primary focus:border-mint focus:outline-none"
              />
            </div>
            <div>
              <label className="text-xs text-tertiary">Email</label>
              <input
                type="email"
                defaultValue="commander@bitten.ai"
                className="w-full mt-1 px-3 py-2 bg-overlay border border-default rounded-lg text-primary focus:border-mint focus:outline-none"
              />
            </div>
          </div>
          <div>
            <label className="text-xs text-tertiary">Tier</label>
            <div className="mt-1 px-3 py-2 bg-overlay border border-default rounded-lg flex items-center justify-between">
              <span className="text-primary">COMMANDER</span>
              <button className="text-xs text-mint hover:text-mint/80 transition-colors flex items-center gap-1">
                Upgrade
                <ChevronRight size={14} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Appearance Section */}
      <div className="panel p-6">
        <h2 className="text-lg font-semibold text-primary mb-4 flex items-center gap-2">
          <Palette size={20} className="text-cyan" />
          Appearance
        </h2>
        <div className="space-y-4">
          <div>
            <label className="text-xs text-tertiary mb-2 block">Theme</label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { value: 'dark', icon: Moon, label: 'Dark' },
                { value: 'light', icon: Sun, label: 'Light' },
                { value: 'auto', icon: Monitor, label: 'Auto' }
              ].map((option) => {
                const Icon = option.icon
                return (
                  <button
                    key={option.value}
                    onClick={() => setTheme(option.value as typeof theme)}
                    className={`
                      p-3 rounded-lg border transition-all flex items-center justify-center gap-2
                      ${theme === option.value
                        ? 'bg-mint/20 border-mint text-mint'
                        : 'bg-overlay border-default text-secondary hover:border-active'}
                    `}
                  >
                    <Icon size={16} />
                    <span className="text-sm font-medium">{option.label}</span>
                  </button>
                )
              })}
            </div>
          </div>
          <div>
            <label className="text-xs text-tertiary mb-2 block">Language</label>
            <select className="w-full px-3 py-2 bg-overlay border border-default rounded-lg text-primary focus:border-mint focus:outline-none">
              <option>English</option>
              <option>Español</option>
              <option>Français</option>
              <option>日本語</option>
            </select>
          </div>
        </div>
      </div>

      {/* Notifications Section */}
      <div className="panel p-6">
        <h2 className="text-lg font-semibold text-primary mb-4 flex items-center gap-2">
          <Bell size={20} className="text-warning" />
          Notifications
        </h2>
        <div className="space-y-3">
          {Object.entries(notifications).map(([key, value]) => (
            <div key={key} className="flex items-center justify-between">
              <div>
                <p className="text-sm text-primary capitalize">{key.replace(/([A-Z])/g, ' $1').trim()}</p>
                <p className="text-xs text-tertiary">
                  {key === 'signals' && 'Alert when new signals are generated'}
                  {key === 'trades' && 'Alert when trades are executed'}
                  {key === 'wins' && 'Celebrate winning trades'}
                  {key === 'losses' && 'Alert on losing trades'}
                  {key === 'system' && 'Important system notifications'}
                </p>
              </div>
              <button
                onClick={() => setNotifications({ ...notifications, [key]: !value })}
                className={`
                  relative w-12 h-6 rounded-full transition-colors
                  ${value ? 'bg-mint' : 'bg-overlay'}
                `}
              >
                <motion.div
                  animate={{ x: value ? 24 : 2 }}
                  transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                  className="absolute top-1 w-4 h-4 bg-white rounded-full"
                />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Risk & Safety Section */}
      <div className="panel p-6">
        <h2 className="text-lg font-semibold text-primary mb-4 flex items-center gap-2">
          <Shield size={20} className="text-danger" />
          Risk & Safety Controls
        </h2>
        <div className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs text-tertiary">Max Daily Risk</label>
              <span className="text-sm font-medium text-primary">{riskSettings.maxDailyRisk}%</span>
            </div>
            <input
              type="range"
              min="1"
              max="10"
              value={riskSettings.maxDailyRisk}
              onChange={(e) => setRiskSettings({ ...riskSettings, maxDailyRisk: parseInt(e.target.value) })}
              className="w-full accent-mint"
            />
          </div>
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs text-tertiary">Max Concurrent Positions</label>
              <span className="text-sm font-medium text-primary">{riskSettings.maxPositions}</span>
            </div>
            <input
              type="range"
              min="1"
              max="5"
              value={riskSettings.maxPositions}
              onChange={(e) => setRiskSettings({ ...riskSettings, maxPositions: parseInt(e.target.value) })}
              className="w-full accent-mint"
            />
          </div>
          <div className="space-y-3 pt-3 border-t border-default">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-primary">Auto Stop-Loss</p>
                <p className="text-xs text-tertiary">Automatically set stop-loss on all trades</p>
              </div>
              <button
                onClick={() => setRiskSettings({ ...riskSettings, autoStop: !riskSettings.autoStop })}
                className={`
                  relative w-12 h-6 rounded-full transition-colors
                  ${riskSettings.autoStop ? 'bg-mint' : 'bg-overlay'}
                `}
              >
                <motion.div
                  animate={{ x: riskSettings.autoStop ? 24 : 2 }}
                  transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                  className="absolute top-1 w-4 h-4 bg-white rounded-full"
                />
              </button>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-primary">Trailing Stop</p>
                <p className="text-xs text-tertiary">Move stop-loss to protect profits</p>
              </div>
              <button
                onClick={() => setRiskSettings({ ...riskSettings, trailingStop: !riskSettings.trailingStop })}
                className={`
                  relative w-12 h-6 rounded-full transition-colors
                  ${riskSettings.trailingStop ? 'bg-mint' : 'bg-overlay'}
                `}
              >
                <motion.div
                  animate={{ x: riskSettings.trailingStop ? 24 : 2 }}
                  transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                  className="absolute top-1 w-4 h-4 bg-white rounded-full"
                />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Danger Zone */}
      <div className="panel border-danger/50 p-6">
        <h2 className="text-lg font-semibold text-danger mb-4 flex items-center gap-2">
          <AlertTriangle size={20} />
          Danger Zone
        </h2>
        <div className="space-y-3">
          <button className="w-full py-2 bg-danger/20 text-danger font-medium rounded-lg hover:bg-danger/30 transition-colors">
            Reset All Settings
          </button>
          <button className="w-full py-2 bg-danger/20 text-danger font-medium rounded-lg hover:bg-danger/30 transition-colors">
            Clear Trading History
          </button>
        </div>
      </div>
    </div>
  )
}