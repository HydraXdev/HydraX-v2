"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MissionCard } from "@/components/cards/MissionCard";
import { StatCard } from "@/components/cards/StatCard";
import { useUI } from "@/lib/store";
import { useEventIntegration } from "@/lib/useEventIntegration";
import {
  Activity,
  TrendingUp,
  Shield,
  Target,
  AlertTriangle,
  Zap,
  DollarSign,
  Clock,
  RefreshCw,
  Award,
  Crosshair,
  Settings,
  Trophy,
  Users,
  ExternalLink,
  ToggleLeft,
  ToggleRight,
  Star,
  ChevronRight,
  Crown,
  BadgeCheck,
  Flame,
} from "lucide-react";

export default function WarRoomPage() {
  const { missions, balance, winRate, xp, seedDemo } = useUI();

  // Initialize event bus integration for real-time updates
  useEventIntegration({
    enableMissionStream: true,
    enablePriceStream: false,
    userId: "7176191872",
  });

  // State management
  const [activeTab, setActiveTab] = useState<"warroom" | "account">("warroom");
  const [autoFireEnabled, setAutoFireEnabled] = useState(true);
  const [riskAdjuster, setRiskAdjuster] = useState(2); // 2% default risk

  // Filter missions by status
  const newMissions = missions.filter(
    (m) => m.status === "NEW" || m.status === "ACCEPTED",
  );
  const liveMissions = missions.filter((m) => m.status === "LIVE");
  const closedMissions = missions.filter((m) => m.status === "CLOSED");

  // Calculate active risk
  const activeRisk = liveMissions.length * riskAdjuster;
  const maxRisk = 6; // 6% daily max

  // Mock user data
  const user = {
    rank: "COMMANDER",
    level: 12,
    xpToNext: 450,
    totalWins: 47,
    totalLosses: 21,
    streakCurrent: 3,
    streakBest: 8,
    referralEarnings: 284.5,
    referralCount: 5,
  };

  // Mock kill cards (recent trade history)
  const killCards = [
    {
      id: "1",
      symbol: "EURUSD",
      outcome: "WIN",
      pips: 23.5,
      amount: 235,
      pattern: "VCB_BREAKOUT",
      timestamp: Date.now() - 3600000,
    },
    {
      id: "2",
      symbol: "GBPJPY",
      outcome: "WIN",
      pips: 41.2,
      amount: 412,
      pattern: "LIQUIDITY_SWEEP",
      timestamp: Date.now() - 7200000,
    },
    {
      id: "3",
      symbol: "USDJPY",
      outcome: "LOSS",
      pips: -18.0,
      amount: -180,
      pattern: "ORDER_BLOCK",
      timestamp: Date.now() - 10800000,
    },
    {
      id: "4",
      symbol: "XAUUSD",
      outcome: "WIN",
      pips: 15.3,
      amount: 153,
      pattern: "SWEEP_RETURN",
      timestamp: Date.now() - 14400000,
    },
  ];

  // Mock badges
  const badges = [
    {
      id: "1",
      name: "Streak Master",
      description: "5+ wins in a row",
      icon: Flame,
      earned: true,
    },
    {
      id: "2",
      name: "Pattern Expert",
      description: "Master all patterns",
      icon: Target,
      earned: true,
    },
    {
      id: "3",
      name: "Risk Manager",
      description: "Never exceed 6% daily risk",
      icon: Shield,
      earned: false,
    },
    {
      id: "4",
      name: "Elite Trader",
      description: "Reach COMMANDER rank",
      icon: Crown,
      earned: true,
    },
  ];

  const getXPProgress = () => (xp % 1000) / 10; // XP progress within current level

  // Mock live feed with real mission data
  const mockLiveFeed = [
    ...(liveMissions.length > 0
      ? liveMissions.map((m) => ({
          time: new Date().toLocaleTimeString("en-US", { hour12: false }),
          message: `${m.symbol} position LIVE (${m.confidence}% confidence)`,
          type: "trade" as const,
        }))
      : []),
    {
      time: "14:32:15",
      message: "EURUSD signal generated (82% confidence)",
      type: "signal" as const,
    },
    {
      time: "14:30:21",
      message: "London session started",
      type: "info" as const,
    },
    {
      time: "14:28:55",
      message: "Take profit hit on USDJPY +45 pips",
      type: "win" as const,
    },
    {
      time: "14:27:12",
      message: "High volatility detected on XAUUSD",
      type: "alert" as const,
    },
  ].slice(0, 5);

  return (
    <div className="min-h-screen bg-primary text-primary">
      {/* Military HUD Header */}
      <motion.div
        initial={{ opacity: 1, y: 0 }}
        animate={{ opacity: 1, y: 0 }}
        className="border-b border-active backdrop-blur-sm bg-overlay/30 sticky top-0 z-50"
      >
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Crosshair className="w-8 h-8 text-mint pulse-glow" />
              <div>
                <h1 className="text-2xl font-tactical text-mint neon-glow">
                  War Room
                </h1>
                <p className="text-sm text-secondary font-code">
                  Tactical HQ - {user.rank} Level {user.level}
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              {/* Tab Switcher */}
              <div className="flex bg-secondary/50 rounded-lg p-1">
                <button
                  onClick={() => setActiveTab("warroom")}
                  className={`px-4 py-2 rounded-md font-tactical text-sm transition-all ${
                    activeTab === "warroom"
                      ? "bg-mint text-black"
                      : "text-secondary hover:text-primary"
                  }`}
                >
                  War Room
                </button>
                <button
                  onClick={() => setActiveTab("account")}
                  className={`px-4 py-2 rounded-md font-tactical text-sm transition-all ${
                    activeTab === "account"
                      ? "bg-mint text-black"
                      : "text-secondary hover:text-primary"
                  }`}
                >
                  Account Control
                </button>
              </div>

              <button onClick={seedDemo} className="btn-secondary">
                <RefreshCw className="w-4 h-4 mr-2" />
                Reset Demo
              </button>
            </div>
          </div>
        </div>
      </motion.div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <AnimatePresence mode="wait">
          {activeTab === "warroom" ? (
            <motion.div
              key="warroom"
              initial={{ opacity: 1, x: 0 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="space-y-6"
            >
              {/* Rank & XP Progress */}
              <motion.div
                initial={{ opacity: 1, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="hud-panel-accent p-6"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-4">
                    <div className="w-16 h-16 bg-mint/20 rounded-lg flex items-center justify-center border border-mint/30">
                      <Crown className="w-8 h-8 text-mint" />
                    </div>
                    <div>
                      <div className="text-2xl font-tactical text-mint neon-glow">
                        {user.rank}
                      </div>
                      <div className="text-lg font-tactical text-cyan">
                        Level {user.level}
                      </div>
                    </div>
                  </div>

                  <div className="text-right">
                    <div className="text-sm text-secondary mb-1">
                      XP Progress
                    </div>
                    <div className="w-64 h-3 bg-secondary rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${getXPProgress()}%` }}
                        className="progress-fill h-full"
                      />
                    </div>
                    <div className="text-xs text-secondary mt-1">
                      {xp.toLocaleString()} XP • {user.xpToNext} to next level
                    </div>
                  </div>
                </div>

                {/* Quick Stats */}
                <div className="grid grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-code text-mint">
                      {user.totalWins}
                    </div>
                    <div className="text-xs text-secondary">WINS</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-code text-danger">
                      {user.totalLosses}
                    </div>
                    <div className="text-xs text-secondary">LOSSES</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-code text-warning">
                      {user.streakCurrent}
                    </div>
                    <div className="text-xs text-secondary">CURRENT STREAK</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-code text-cyan">
                      {user.streakBest}
                    </div>
                    <div className="text-xs text-secondary">BEST STREAK</div>
                  </div>
                </div>
              </motion.div>

              {/* Control Panel - Auto-Fire & Risk Controls */}
              <motion.div
                initial={{ opacity: 1, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="hud-panel p-6"
              >
                <h3 className="text-lg font-tactical text-mint mb-4">
                  Command Control
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* Auto-Fire Toggle */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-tactical text-cyan">Auto-Fire</span>
                      <button
                        onClick={() => setAutoFireEnabled(!autoFireEnabled)}
                        className={`transition-colors ${autoFireEnabled ? "text-mint" : "text-secondary"}`}
                      >
                        {autoFireEnabled ? (
                          <ToggleRight className="w-8 h-8" />
                        ) : (
                          <ToggleLeft className="w-8 h-8" />
                        )}
                      </button>
                    </div>
                    <div className="text-xs text-secondary">
                      {autoFireEnabled
                        ? "Enabled - High confidence signals fire automatically"
                        : "Disabled - Manual execution required"}
                    </div>
                  </div>

                  {/* Risk Adjuster */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-tactical text-warning">
                        Risk Level
                      </span>
                      <span className="text-lg font-code text-mint">
                        {riskAdjuster}%
                      </span>
                    </div>
                    <input
                      type="range"
                      min="1"
                      max="5"
                      step="0.5"
                      value={riskAdjuster}
                      onChange={(e) =>
                        setRiskAdjuster(parseFloat(e.target.value))
                      }
                      className="w-full h-2 bg-secondary rounded-lg appearance-none cursor-pointer"
                    />
                    <div className="text-xs text-secondary">
                      Risk per trade: $
                      {(balance * (riskAdjuster / 100)).toFixed(0)}
                    </div>
                  </div>

                  {/* Remaining Trades */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-tactical text-cyan">
                        Trades Available
                      </span>
                      <span className="text-lg font-code text-mint">
                        {3 - liveMissions.length}/3
                      </span>
                    </div>
                    <div className="w-full h-2 bg-secondary rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-mint to-cyan transition-all duration-300"
                        style={{
                          width: `${((3 - liveMissions.length) / 3) * 100}%`,
                        }}
                      />
                    </div>
                    <div className="text-xs text-secondary">
                      Daily limit resets at midnight UTC
                    </div>
                  </div>
                </div>
              </motion.div>

              {/* Kill Cards - Recent Trade History */}
              <motion.div
                initial={{ opacity: 1, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="space-y-4"
              >
                <h3 className="text-lg font-tactical text-cyan flex items-center">
                  <Trophy className="w-5 h-5 mr-2" />
                  Kill Cards
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {killCards.map((card, index) => (
                    <motion.div
                      key={card.id}
                      initial={{ opacity: 1, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 0.1 * index }}
                      className={`kill-card ${card.outcome.toLowerCase()}`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="font-tactical text-lg">
                          {card.symbol}
                        </div>
                        <div
                          className={`text-xs px-2 py-1 rounded ${
                            card.outcome === "WIN"
                              ? "bg-mint/20 text-mint"
                              : "bg-danger/20 text-danger"
                          }`}
                        >
                          {card.outcome}
                        </div>
                      </div>
                      <div className="mb-2">
                        <div
                          className={`text-2xl font-code ${
                            card.outcome === "WIN" ? "text-mint" : "text-danger"
                          }`}
                        >
                          {card.outcome === "WIN" ? "+" : ""}${card.amount}
                        </div>
                        <div className="text-sm text-secondary">
                          {card.outcome === "WIN" ? "+" : ""}
                          {card.pips} pips
                        </div>
                      </div>
                      <div className="text-xs text-secondary">
                        {card.pattern.replace(/_/g, " ")}
                      </div>
                      <div className="text-xs text-muted mt-1">
                        {new Date(card.timestamp).toLocaleTimeString()}
                      </div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>

              {/* Badges */}
              <motion.div
                initial={{ opacity: 1, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="space-y-4"
              >
                <h3 className="text-lg font-tactical text-warning flex items-center">
                  <Award className="w-5 h-5 mr-2" />
                  Achievements
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {badges.map((badge, index) => {
                    const IconComponent = badge.icon;
                    return (
                      <motion.div
                        key={badge.id}
                        initial={{ opacity: 1, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.1 * index }}
                        className={`hud-panel p-4 text-center ${
                          badge.earned ? "border-mint/50" : "opacity-50"
                        }`}
                      >
                        <div
                          className={`w-12 h-12 mx-auto mb-2 rounded-lg flex items-center justify-center ${
                            badge.earned
                              ? "bg-mint/20 border border-mint/30"
                              : "bg-secondary/50"
                          }`}
                        >
                          <IconComponent
                            className={`w-6 h-6 ${badge.earned ? "text-mint" : "text-secondary"}`}
                          />
                        </div>
                        <div
                          className={`font-tactical text-sm ${badge.earned ? "text-mint" : "text-secondary"}`}
                        >
                          {badge.name}
                        </div>
                        <div className="text-xs text-muted mt-1">
                          {badge.description}
                        </div>
                        {badge.earned && (
                          <BadgeCheck className="w-4 h-4 text-mint mx-auto mt-2" />
                        )}
                      </motion.div>
                    );
                  })}
                </div>
              </motion.div>
            </motion.div>
          ) : (
            /* Account Control Tab */
            <motion.div
              key="account"
              initial={{ opacity: 1, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-6"
            >
              {/* Account Status */}
              <motion.div
                initial={{ opacity: 1, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="hud-panel-accent p-6"
              >
                <h3 className="text-lg font-tactical text-mint mb-4">
                  Account Status
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                  <div className="text-center">
                    <div className="text-2xl font-code text-mint">
                      ${balance.toLocaleString()}
                    </div>
                    <div className="text-sm text-secondary">Balance</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-code text-cyan">
                      {winRate.toFixed(1)}%
                    </div>
                    <div className="text-sm text-secondary">Win Rate</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-code text-warning">
                      {liveMissions.length}
                    </div>
                    <div className="text-sm text-secondary">
                      Active Positions
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-code text-danger">
                      {activeRisk.toFixed(1)}%
                    </div>
                    <div className="text-sm text-secondary">Risk Exposure</div>
                  </div>
                </div>
              </motion.div>

              {/* Subscription & Referrals */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <motion.div
                  initial={{ opacity: 1, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                  className="hud-panel p-6"
                >
                  <h3 className="text-lg font-tactical text-cyan mb-4">
                    Subscription
                  </h3>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-secondary">Current Plan:</span>
                      <span className="font-tactical text-mint">COMMANDER</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-secondary">Auto-Fire Slots:</span>
                      <span className="text-primary">3/3</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-secondary">Next Billing:</span>
                      <span className="text-primary">Dec 15, 2024</span>
                    </div>
                    <button className="btn-secondary w-full">
                      <ExternalLink className="w-4 h-4 mr-2" />
                      Manage Subscription
                    </button>
                  </div>
                </motion.div>

                <motion.div
                  initial={{ opacity: 1, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className="hud-panel p-6"
                >
                  <h3 className="text-lg font-tactical text-warning mb-4">
                    Referral Program
                  </h3>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-secondary">Referrals:</span>
                      <span className="text-primary">{user.referralCount}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-secondary">Earnings:</span>
                      <span className="text-mint font-code">
                        ${user.referralEarnings}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-secondary">Commission:</span>
                      <span className="text-primary">30% lifetime</span>
                    </div>
                    <button className="btn-primary w-full">
                      <Users className="w-4 h-4 mr-2" />
                      Share Referral Link
                    </button>
                  </div>
                </motion.div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
