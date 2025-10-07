"use client"

import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, BarChart3, Calendar, Target, Award } from 'lucide-react';
import type { EquityPoint, KPI, StatEvent, DistItem } from '@/lib/eventBus/contracts';
import { fmtUSD, fmtPercent, fmtRelative } from '@/lib/ui/format';
import { useHotkeys, COMMON_HOTKEYS } from '@/lib/ui/hotkeys';
import { announce } from '@/lib/ui/a11y';
import { HeaderOps } from './HeaderOps';
import { FooterStatus } from './FooterStatus';

export type StatsCenterProps = {
  equitySeries: EquityPoint[];
  kpis: KPI[];
  events: StatEvent[];
  byPair: DistItem[];
  bySession: DistItem[];
  level: string;
  onWarRoom?: () => void;
  onNotebook?: () => void;
  onHelp?: () => void;
  onMenu?: () => void;
  onBio?: () => void;
};

export function StatsCenter({
  equitySeries,
  kpis,
  events,
  byPair,
  bySession,
  level,
  onWarRoom,
  onNotebook,
  onHelp,
  onMenu,
  onBio,
}: StatsCenterProps) {
  // Calculate growth percentage
  const growth = useMemo(() => {
    if (equitySeries.length < 2) return 0;
    const first = equitySeries[0];
    const last = equitySeries[equitySeries.length - 1];
    return ((last.equity - first.balance) / first.balance) * 100;
  }, [equitySeries]);

  // Setup hotkeys
  useHotkeys({
    [COMMON_HOTKEYS.WAR_ROOM]: () => {
      onWarRoom?.();
      announce('Navigating to War Room', 'polite');
    },
    [COMMON_HOTKEYS.NOTEBOOK]: () => {
      onNotebook?.();
      announce('Opening notebook', 'polite');
    },
    [COMMON_HOTKEYS.HELP]: () => {
      onHelp?.();
      announce('Opening help', 'polite');
    },
    [COMMON_HOTKEYS.MENU]: () => {
      onMenu?.();
      announce('Opening menu', 'polite');
    },
  });

  // SVG chart dimensions
  const chartWidth = 600;
  const chartHeight = 200;
  const padding = { top: 20, right: 20, bottom: 30, left: 50 };
  const innerWidth = chartWidth - padding.left - padding.right;
  const innerHeight = chartHeight - padding.top - padding.bottom;

  // Calculate scales
  const yExtent = useMemo(() => {
    if (equitySeries.length === 0) return [0, 100];
    const values = equitySeries.map(p => p.equity);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min;
    return [min - range * 0.1, max + range * 0.1];
  }, [equitySeries]);

  // Generate path
  const equityPath = useMemo(() => {
    if (equitySeries.length === 0) return '';

    const points = equitySeries.map((point, i) => {
      const x = (i / (equitySeries.length - 1)) * innerWidth;
      const y = innerHeight - ((point.equity - yExtent[0]) / (yExtent[1] - yExtent[0])) * innerHeight;
      return `${x},${y}`;
    });

    return `M ${points.join(' L ')}`;
  }, [equitySeries, innerWidth, innerHeight, yExtent]);

  // Area fill path
  const areaPath = useMemo(() => {
    if (!equityPath) return '';
    const lastX = innerWidth;
    const bottomY = innerHeight;
    return `${equityPath} L ${lastX},${bottomY} L 0,${bottomY} Z`;
  }, [equityPath, innerWidth, innerHeight]);

  return (
    <div className="min-h-screen bg-[#0a0e1a] text-[#cbd5e0] flex flex-col">
      {/* Header */}
      <HeaderOps
        title="MISSION ANALYTICS"
        level={level}
        onHelp={onHelp}
        onMenu={onMenu}
      />

      <main className="flex-1 px-4 py-6 space-y-6 overflow-y-auto">
        {/* Equity Curve Hero */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-[#1a202c] border border-[#2d3748] rounded-lg p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-[#34d399]">Equity Curve</h2>
            <div className="flex items-center gap-2">
              {growth >= 0 ? (
                <TrendingUp className="w-5 h-5 text-[#34d399]" aria-hidden="true" />
              ) : (
                <TrendingDown className="w-5 h-5 text-[#ef4444]" aria-hidden="true" />
              )}
              <span className={`text-lg font-mono ${growth >= 0 ? 'text-[#34d399]' : 'text-[#ef4444]'}`}>
                {growth >= 0 ? '+' : ''}{fmtPercent(growth / 100)}
              </span>
            </div>
          </div>

          {/* SVG Chart */}
          <div className="w-full overflow-x-auto">
            <svg
              viewBox={`0 0 ${chartWidth} ${chartHeight}`}
              className="w-full h-auto"
              role="img"
              aria-label={`Equity curve showing ${fmtPercent(growth / 100)} growth`}
            >
              <defs>
                <linearGradient id="equityGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#34d399" stopOpacity="0.3" />
                  <stop offset="100%" stopColor="#34d399" stopOpacity="0.05" />
                </linearGradient>
              </defs>

              <g transform={`translate(${padding.left}, ${padding.top})`}>
                {/* Area fill */}
                <path
                  d={areaPath}
                  fill="url(#equityGradient)"
                />

                {/* Line */}
                <path
                  d={equityPath}
                  fill="none"
                  stroke="#34d399"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />

                {/* Y-axis labels */}
                <text x="-10" y="0" textAnchor="end" fill="#718096" fontSize="12">
                  {fmtUSD(yExtent[1])}
                </text>
                <text x="-10" y={innerHeight} textAnchor="end" fill="#718096" fontSize="12">
                  {fmtUSD(yExtent[0])}
                </text>
              </g>
            </svg>
          </div>

          {/* A11y live region */}
          <div className="sr-only" role="status" aria-live="polite" aria-atomic="true">
            Current equity: {equitySeries.length > 0 ? fmtUSD(equitySeries[equitySeries.length - 1].equity) : 'Loading'}.
            Growth: {fmtPercent(growth / 100)}.
          </div>
        </motion.section>

        {/* KPIs Grid */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
        >
          {kpis.map((kpi, idx) => (
            <div
              key={idx}
              className="bg-[#1a202c] border border-[#2d3748] rounded-lg p-4 hover:border-[#34d399] transition-colors"
            >
              <div className="text-sm text-[#718096] mb-1">{kpi.label}</div>
              <div className="text-2xl font-mono font-bold text-[#cbd5e0] mb-1">{kpi.value}</div>
              {kpi.sub && <div className="text-xs text-[#4a5568]">{kpi.sub}</div>}
            </div>
          ))}
        </motion.section>

        {/* Distribution Panel */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-[#1a202c] border border-[#2d3748] rounded-lg p-6"
        >
          <h2 className="text-lg font-bold text-[#34d399] mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5" aria-hidden="true" />
            Distribution Analysis
          </h2>

          <div className="grid md:grid-cols-2 gap-6">
            {/* By Pair */}
            <div>
              <h3 className="text-sm text-[#718096] mb-3">By Pair</h3>
              <div className="space-y-2">
                {byPair.map((item, idx) => {
                  const maxValue = Math.max(...byPair.map(i => i.value));
                  const percent = (item.value / maxValue) * 100;
                  return (
                    <div key={idx}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-[#cbd5e0]">{item.name}</span>
                        <span className="text-[#718096] font-mono">{item.value}%</span>
                      </div>
                      <div className="h-2 bg-[#2d3748] rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${percent}%` }}
                          transition={{ duration: 0.5, delay: idx * 0.05 }}
                          className="h-full bg-[#34d399] rounded-full"
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* By Session */}
            <div>
              <h3 className="text-sm text-[#718096] mb-3">By Session</h3>
              <div className="space-y-2">
                {bySession.map((item, idx) => {
                  const maxValue = Math.max(...bySession.map(i => i.value));
                  const percent = (item.value / maxValue) * 100;
                  return (
                    <div key={idx}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-[#cbd5e0]">{item.name}</span>
                        <span className="text-[#718096] font-mono">{item.value}%</span>
                      </div>
                      <div className="h-2 bg-[#2d3748] rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${percent}%` }}
                          transition={{ duration: 0.5, delay: idx * 0.05 }}
                          className="h-full bg-[#60a5fa] rounded-full"
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </motion.section>

        {/* Recent Operations */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-[#1a202c] border border-[#2d3748] rounded-lg p-6"
        >
          <h2 className="text-lg font-bold text-[#34d399] mb-4 flex items-center gap-2">
            <Calendar className="w-5 h-5" aria-hidden="true" />
            Recent Operations
          </h2>

          <div className="space-y-2">
            {events.slice(-10).reverse().map((event, idx) => (
              <motion.div
                key={event.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.03 }}
                className="flex items-center justify-between p-3 bg-[#0f1419] rounded border border-[#1a202c] hover:border-[#2d3748] transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${event.tag === 'WIN' ? 'bg-[#34d399]' : event.tag === 'LOSS' ? 'bg-[#ef4444]' : 'bg-[#718096]'}`} />
                  <div>
                    <div className="text-sm font-medium text-[#cbd5e0]">{event.title}</div>
                    <div className="text-xs text-[#4a5568]">{fmtRelative(event.when)}</div>
                  </div>
                </div>
                <div className={`text-sm font-mono font-bold ${event.delta >= 0 ? 'text-[#34d399]' : 'text-[#ef4444]'}`}>
                  {event.delta >= 0 ? '+' : ''}{fmtUSD(event.delta)}
                </div>
              </motion.div>
            ))}
          </div>
        </motion.section>

        {/* Actions */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="grid grid-cols-2 sm:grid-cols-4 gap-4"
        >
          <button
            onClick={onWarRoom}
            className="flex items-center justify-center gap-2 p-4 bg-[#1a202c] border border-[#2d3748] rounded-lg hover:border-[#34d399] transition-colors"
            aria-label="Go to War Room"
          >
            <Target className="w-5 h-5 text-[#34d399]" aria-hidden="true" />
            <span className="text-sm font-medium">WAR ROOM</span>
          </button>

          <button
            onClick={onNotebook}
            className="flex items-center justify-center gap-2 p-4 bg-[#1a202c] border border-[#2d3748] rounded-lg hover:border-[#60a5fa] transition-colors"
            aria-label="Open Notebook"
          >
            <Award className="w-5 h-5 text-[#60a5fa]" aria-hidden="true" />
            <span className="text-sm font-medium">NOTEBOOK</span>
          </button>

          <button
            onClick={onHelp}
            className="flex items-center justify-center gap-2 p-4 bg-[#1a202c] border border-[#2d3748] rounded-lg hover:border-[#fbbf24] transition-colors"
            aria-label="Open Help"
          >
            <span className="text-sm font-medium">HELP</span>
          </button>

          <button
            onClick={onBio}
            className="flex items-center justify-center gap-2 p-4 bg-[#1a202c] border border-[#2d3748] rounded-lg hover:border-[#a78bfa] transition-colors"
            aria-label="View Bio/Subscription"
          >
            <span className="text-sm font-medium">PROFILE</span>
          </button>
        </motion.section>
      </main>

      {/* Footer */}
      <FooterStatus />
    </div>
  );
}
