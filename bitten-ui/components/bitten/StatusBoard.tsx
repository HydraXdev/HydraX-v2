"use client";

import React, { useMemo } from "react";
import { motion } from "framer-motion";
import {
  TrendingUp,
  TrendingDown,
  ExternalLink,
  X,
  BarChart3,
  BookOpen,
  Target,
} from "lucide-react";
import { useReducedMotion } from "@/lib/ui/a11y";
import { fmtUSD, fmtPrice, fmtSigned, fmtRelative } from "@/lib/ui/format";
import type { LiveTrade } from "@/lib/eventBus/contracts";
import { HeaderOps } from "./HeaderOps";
import { HelpMenuButtons } from "./HelpMenuButtons";
import { FooterStatus } from "./FooterStatus";

export interface StatusBoardProps {
  trades: LiveTrade[];
  balance: number;
  slots: number;
  level: string;
  onAlerts: () => void;
  onWarRoom: () => void;
  onStats: () => void;
  onCloseAll: () => void;
  onNotebook: () => void;
  onOpenMenu: () => void;
  onOpenHelp: () => void;
}

/**
 * StatusBoard - Live positions monitor with triage
 *
 * Features:
 * - Account telemetry (balance, equity, P/L delta)
 * - Trade lanes with visual progress tracks
 * - Empty slot indicators
 * - Control panel (Alerts, War Room, Stats, Close All, Notebook)
 * - Hotkeys: A (alerts), W (war room), S (stats), X (close), N (notebook), ? (help)
 * - Mobile-first, stacked layout, 44px+ touch targets
 */
export function StatusBoard({
  trades,
  balance,
  slots,
  level,
  onAlerts,
  onWarRoom,
  onStats,
  onCloseAll,
  onNotebook,
  onOpenMenu,
  onOpenHelp,
}: StatusBoardProps) {
  const prefersReducedMotion = useReducedMotion();

  // Calculate equity and P/L
  const { equity, totalPnL } = useMemo(() => {
    const pnl = trades.reduce((sum, t) => sum + t.equity, 0);
    return {
      equity: balance + pnl,
      totalPnL: pnl,
    };
  }, [trades, balance]);

  const openSlots = trades.length;
  const availableSlots = slots - openSlots;

  return (
    <div className="min-h-screen bg-[#0a0e1a] text-[#cbd5e0] flex flex-col">
      {/* Header */}
      <HeaderOps pageTitle="STATUS BOARD" userLevel={level} />

      {/* Help & Menu Buttons */}
      <HelpMenuButtons onHelp={onOpenHelp} onMenu={onOpenMenu} />

      <div className="flex-1 max-w-6xl mx-auto w-full px-4 py-8 pb-32">
        {/* Account Telemetry Card */}
        <motion.div
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-[#1a1f2e] border border-[#34d399]/30 rounded-lg p-6 mb-6"
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Balance */}
            <div>
              <p className="text-xs text-[#4a5568] mb-1">BALANCE</p>
              <p className="text-2xl font-mono tabular-nums text-[#cbd5e0]">
                {fmtUSD(balance)}
              </p>
            </div>

            {/* Equity */}
            <div>
              <p className="text-xs text-[#4a5568] mb-1">EQUITY</p>
              <p className="text-2xl font-mono tabular-nums text-[#cbd5e0]">
                {fmtUSD(equity)}
              </p>
            </div>

            {/* P/L Delta */}
            <div>
              <p className="text-xs text-[#4a5568] mb-1">TOTAL P/L</p>
              <div className="flex items-center gap-2">
                <p
                  className={`text-2xl font-mono tabular-nums ${totalPnL >= 0 ? "text-[#34d399]" : "text-[#ef4444]"}`}
                >
                  {fmtSigned(totalPnL)}
                </p>
                {totalPnL >= 0 ? (
                  <TrendingUp
                    className="w-5 h-5 text-[#34d399]"
                    aria-hidden="true"
                  />
                ) : (
                  <TrendingDown
                    className="w-5 h-5 text-[#ef4444]"
                    aria-hidden="true"
                  />
                )}
              </div>
            </div>
          </div>

          {/* Capacity Bar */}
          <div className="mt-6 pt-4 border-t border-[#2d3748]">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-[#4a5568]">CAPACITY</span>
              <span className="text-sm font-mono tabular-nums text-[#cbd5e0]">
                {openSlots}/{slots} positions
              </span>
            </div>
            <div className="w-full bg-[#2d3748] rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all ${
                  openSlots / slots > 0.8
                    ? "bg-[#ef4444]"
                    : openSlots / slots > 0.5
                      ? "bg-[#fbbf24]"
                      : "bg-[#34d399]"
                }`}
                style={{ width: `${(openSlots / slots) * 100}%` }}
                aria-label={`${openSlots} of ${slots} position slots used`}
              />
            </div>
          </div>
        </motion.div>

        {/* Trade Lanes */}
        <div className="space-y-4 mb-6">
          {trades.map((trade, index) => (
            <TradeLane
              key={trade.id}
              trade={trade}
              index={index}
              prefersReducedMotion={prefersReducedMotion}
            />
          ))}

          {/* Empty Slots */}
          {availableSlots > 0 && (
            <div className="bg-[#1a1f2e] border border-[#2d3748] border-dashed rounded-lg p-6 text-center">
              <Target
                className="w-8 h-8 text-[#4a5568] mx-auto mb-2"
                aria-hidden="true"
              />
              <p className="text-sm text-[#4a5568]">
                {availableSlots} {availableSlots === 1 ? "slot" : "slots"}{" "}
                available
              </p>
            </div>
          )}
        </div>

        {/* Control Panel */}
        <div className="bg-[#1a1f2e] border border-[#cbd5e0]/30 rounded-lg p-6">
          <h2 className="text-lg font-tactical text-[#cbd5e0] mb-4">
            CONTROL PANEL
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button
              onClick={onAlerts}
              className="px-6 py-3 bg-[#06b6d4]/20 hover:bg-[#06b6d4]/30 border border-[#06b6d4]/30 text-[#06b6d4] rounded-lg font-tactical transition-colors text-left flex items-center gap-2"
              aria-label="Open alerts (hotkey: A)"
            >
              <ExternalLink className="w-4 h-4" aria-hidden="true" />
              Alerts [A]
            </button>

            <button
              onClick={onWarRoom}
              className="px-6 py-3 bg-[#34d399]/20 hover:bg-[#34d399]/30 border border-[#34d399]/30 text-[#34d399] rounded-lg font-tactical transition-colors text-left flex items-center gap-2"
              aria-label="Go to War Room (hotkey: W)"
            >
              <Target className="w-4 h-4" aria-hidden="true" />
              War Room [W]
            </button>

            <button
              onClick={onStats}
              className="px-6 py-3 bg-[#fbbf24]/20 hover:bg-[#fbbf24]/30 border border-[#fbbf24]/30 text-[#fbbf24] rounded-lg font-tactical transition-colors text-left flex items-center gap-2"
              aria-label="View statistics (hotkey: S)"
            >
              <BarChart3 className="w-4 h-4" aria-hidden="true" />
              Stats [S]
            </button>

            <button
              onClick={onCloseAll}
              disabled={trades.length === 0}
              className="px-6 py-3 bg-[#ef4444]/20 hover:bg-[#ef4444]/30 disabled:bg-[#2d3748] disabled:border-[#2d3748] disabled:text-[#4a5568] border border-[#ef4444]/30 text-[#ef4444] rounded-lg font-tactical transition-colors text-left flex items-center gap-2"
              aria-label="Close all positions (hotkey: X)"
            >
              <X className="w-4 h-4" aria-hidden="true" />
              Close All [X]
            </button>

            <button
              onClick={onNotebook}
              className="md:col-span-2 px-6 py-3 bg-[#cbd5e0]/10 hover:bg-[#cbd5e0]/20 border border-[#cbd5e0]/30 text-[#cbd5e0] rounded-lg font-tactical transition-colors text-left flex items-center gap-2"
              aria-label="Open notebook (hotkey: N)"
            >
              <BookOpen className="w-4 h-4" aria-hidden="true" />
              Notebook [N]
            </button>
          </div>
        </div>
      </div>

      {/* Footer */}
      <FooterStatus className="sticky bottom-0" />
    </div>
  );
}

/**
 * TradeLane - Individual trade row with visual progress track
 */
function TradeLane({
  trade,
  index,
  prefersReducedMotion,
}: {
  trade: LiveTrade;
  index: number;
  prefersReducedMotion: boolean;
}) {
  const pnlPercent = ((trade.current - trade.entry) / trade.entry) * 100;
  const isProfitable = trade.equity >= 0;

  // Calculate progress on the TP/SL track (0-100%)
  const range =
    trade.direction === "BUY"
      ? trade.takeProfit - trade.stopLoss
      : trade.stopLoss - trade.takeProfit;
  const progress =
    trade.direction === "BUY"
      ? ((trade.current - trade.stopLoss) / range) * 100
      : ((trade.stopLoss - trade.current) / range) * 100;
  const clampedProgress = Math.max(0, Math.min(100, progress));

  return (
    <motion.div
      initial={prefersReducedMotion ? {} : { opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      className="bg-[#1a1f2e] border border-[#2d3748] rounded-lg p-4"
    >
      <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
        {/* Left Meta */}
        <div className="md:col-span-3">
          <div className="flex items-center gap-2 mb-1">
            {trade.direction === "BUY" ? (
              <TrendingUp
                className="w-4 h-4 text-[#34d399]"
                aria-hidden="true"
              />
            ) : (
              <TrendingDown
                className="w-4 h-4 text-[#ef4444]"
                aria-hidden="true"
              />
            )}
            <span className="font-tactical text-[#cbd5e0]">{trade.pair}</span>
          </div>
          <p className="text-xs text-[#4a5568]">
            {trade.lots} lots • {fmtRelative(trade.startTime)}
          </p>
        </div>

        {/* Center: Progress Track */}
        <div className="md:col-span-6">
          <div className="relative h-6 bg-[#0a0e1a] rounded-lg overflow-hidden">
            {/* SL Gate (Red) */}
            <div
              className="absolute left-0 top-0 h-full w-1 bg-[#ef4444]"
              aria-label="Stop loss"
            />

            {/* TP Gate (Green) */}
            <div
              className="absolute right-0 top-0 h-full w-1 bg-[#34d399]"
              aria-label="Take profit"
            />

            {/* Fill area */}
            <div
              className={`absolute top-0 left-0 h-full transition-all ${isProfitable ? "bg-[#34d399]/20" : "bg-[#ef4444]/20"}`}
              style={{ width: `${clampedProgress}%` }}
              aria-hidden="true"
            />

            {/* NOW cursor (Yellow) */}
            <div
              className="absolute top-0 h-full w-1 bg-[#fbbf24] transition-all"
              style={{ left: `${clampedProgress}%` }}
              aria-label="Current price"
            />

            {/* Price labels */}
            <div className="absolute inset-0 flex items-center justify-between px-2 text-xs font-mono tabular-nums">
              <span className="text-[#ef4444]">{fmtPrice(trade.stopLoss)}</span>
              <span className="text-[#fbbf24]">{fmtPrice(trade.current)}</span>
              <span className="text-[#34d399]">
                {fmtPrice(trade.takeProfit)}
              </span>
            </div>
          </div>
        </div>

        {/* Right: P/L */}
        <div className="md:col-span-3 text-right">
          <p
            className={`text-xl font-mono tabular-nums ${isProfitable ? "text-[#34d399]" : "text-[#ef4444]"}`}
          >
            {fmtSigned(trade.equity)}
          </p>
          <p
            className={`text-xs font-mono tabular-nums ${isProfitable ? "text-[#34d399]/70" : "text-[#ef4444]/70"}`}
          >
            {fmtSigned(pnlPercent)}%
          </p>

          {/* Optional Sparkline */}
          {trade.history && trade.history.length > 0 && (
            <svg
              viewBox="0 0 60 20"
              className="w-full h-5 mt-1"
              aria-label="Price history sparkline"
            >
              <polyline
                points={trade.history
                  .map(
                    (val, i) =>
                      `${(i / (trade.history!.length - 1)) * 60},${10 - (val / 100) * 5}`,
                  )
                  .join(" ")}
                fill="none"
                stroke={isProfitable ? "#34d399" : "#ef4444"}
                strokeWidth="1"
                opacity="0.5"
              />
            </svg>
          )}
        </div>
      </div>
    </motion.div>
  );
}
