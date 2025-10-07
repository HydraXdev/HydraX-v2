"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { MilitaryHeader } from "@/components/bitten/MilitaryHeader";

export default function StatsPage() {
  const router = useRouter();

  // Mock data - will be replaced with event bus data
  const balance = 10005.0;
  const equity = 10152.4;
  const totalPnL = 147.4;
  const growthPct = 1.47;

  const kpis = [
    { label: "WIN RATE", value: "71%", sub: "Last 90 days" },
    { label: "AVG R:R", value: "1.84", sub: "Risk/Reward" },
    { label: "PROFIT FACTOR", value: "1.62", sub: "Net profit" },
    { label: "BEST TRADE", value: "$486.40", sub: "XAU/USD" },
    { label: "LONGEST STREAK", value: "5 wins", sub: "Best run" },
    { label: "AVG HOLD", value: "2h 18m", sub: "Position time" },
  ];

  const recentOps = [
    {
      id: 1,
      when: "2h ago",
      title: "EUR/USD — London Breakout",
      delta: 97.2,
      tag: "WIN",
    },
    {
      id: 2,
      when: "6h ago",
      title: "GBP/JPY — Session Continuation",
      delta: 45.5,
      tag: "WIN",
    },
    {
      id: 3,
      when: "1d ago",
      title: "Z-Trap Reversal",
      delta: -36.75,
      tag: "LOSS",
    },
    { id: 4, when: "2d ago", title: "Impulse Catch", delta: 86.4, tag: "WIN" },
  ];

  const pairDist = [
    { name: "EUR/USD", value: 8 },
    { name: "XAU/USD", value: 5 },
    { name: "GBP/JPY", value: 3 },
    { name: "USD/CAD", value: 4 },
  ];

  return (
    <div className="min-h-screen bg-gray-950 text-green-400 p-2 sm:p-4 font-mono">
      <MilitaryHeader title="BITTEN" subtitle="MISSION ANALYTICS" />

      {/* Account Growth */}
      <div className="border-2 border-green-500 bg-black/50 p-3 mb-3">
        <div className="text-sm font-bold text-green-400 mb-2">
          TOTAL ACCOUNT GROWTH
        </div>
        <div className="grid grid-cols-3 gap-3 mb-2">
          <div>
            <div className="text-xs text-green-600">BALANCE</div>
            <div className="text-lg font-bold text-green-400">
              ${balance.toFixed(2)}
            </div>
          </div>
          <div>
            <div className="text-xs text-green-600">EQUITY</div>
            <div className="text-lg font-bold text-green-400">
              ${equity.toFixed(2)}
            </div>
          </div>
          <div>
            <div className="text-xs text-green-600">GROWTH</div>
            <div
              className={`text-lg font-bold ${totalPnL >= 0 ? "text-green-400" : "text-red-400"}`}
            >
              {totalPnL >= 0 ? "+" : ""}
              {growthPct.toFixed(2)}%
            </div>
          </div>
        </div>
      </div>

      {/* Key Performance */}
      <div className="border-2 border-yellow-500 bg-black/70 p-3 mb-3">
        <div className="text-sm font-bold text-yellow-400 mb-2">
          KEY PERFORMANCE
        </div>
        <div className="grid grid-cols-3 gap-2">
          {kpis.map((k) => (
            <div
              key={k.label}
              className="border border-green-700 bg-black/50 p-2"
            >
              <div className="text-xs text-green-600">{k.label}</div>
              <div className="text-xl font-bold text-green-400">{k.value}</div>
              {k.sub && <div className="text-xs text-gray-500">{k.sub}</div>}
            </div>
          ))}
        </div>
      </div>

      {/* Recent Operations */}
      <div className="border-2 border-blue-500 bg-black/70 p-3 mb-3">
        <div className="text-sm font-bold text-blue-400 mb-2">
          RECENT OPERATIONS
        </div>
        <div className="space-y-2">
          {recentOps.map((op) => (
            <div
              key={op.id}
              className="border border-green-700 bg-black/50 p-2 flex justify-between items-center"
            >
              <div>
                <div className="text-sm text-green-400">{op.title}</div>
                <div className="text-xs text-green-600">
                  {op.when} • {op.tag}
                </div>
              </div>
              <div
                className={`text-sm font-bold ${op.delta >= 0 ? "text-green-400" : "text-red-400"}`}
              >
                {op.delta >= 0 ? "+" : ""}${Math.abs(op.delta).toFixed(2)}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Distribution */}
      <div className="border-2 border-purple-500 bg-black/70 p-3 mb-3">
        <div className="text-sm font-bold text-purple-400 mb-2">
          DISTRIBUTION BY PAIR
        </div>
        <div className="space-y-1">
          {pairDist.map((pair) => (
            <div key={pair.name} className="flex justify-between items-center">
              <div className="text-sm text-green-400">{pair.name}</div>
              <div className="flex items-center gap-2">
                <div
                  className="h-2 bg-green-500"
                  style={{ width: `${pair.value * 10}px` }}
                ></div>
                <div className="text-sm text-green-400">{pair.value}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="grid grid-cols-2 gap-2">
        <button
          onClick={() => router.push("/war-room")}
          className="border-2 border-yellow-500 bg-yellow-900/30 p-3 hover:bg-yellow-900/50 transition-colors text-yellow-400 font-bold"
        >
          🏛️ WAR ROOM
        </button>
        <button
          onClick={() => router.push("/notebook")}
          className="border-2 border-purple-500 bg-purple-900/30 p-3 hover:bg-purple-900/50 transition-colors text-purple-400 font-bold"
        >
          📓 NOTEBOOK
        </button>
      </div>
    </div>
  );
}
