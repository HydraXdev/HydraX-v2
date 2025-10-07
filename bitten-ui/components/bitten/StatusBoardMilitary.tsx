"use client"

import React from 'react';
import { MilitaryHeader } from './MilitaryHeader';
import type { LiveTrade } from '@/lib/eventBus/contracts';

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
}: StatusBoardProps) {
  const equity = balance + trades.reduce((sum, t) => sum + t.equity, 0);
  const totalPnL = trades.reduce((sum, t) => sum + t.equity, 0);
  const openSlots = trades.length;
  const availableSlots = slots - openSlots;

  return (
    <div className="min-h-screen bg-gray-950 text-green-400 p-2 sm:p-4 font-mono">
      <MilitaryHeader title="BITTEN" subtitle="STATUS BOARD" />

      {/* Account Telemetry */}
      <div className="border-2 border-green-500 bg-black/50 p-3 mb-3">
        <div className="grid grid-cols-3 gap-3">
          <div>
            <div className="text-xs text-green-600">BALANCE</div>
            <div className="text-xl font-bold text-green-400">${balance.toFixed(2)}</div>
          </div>
          <div>
            <div className="text-xs text-green-600">EQUITY</div>
            <div className="text-xl font-bold text-green-400">${equity.toFixed(2)}</div>
          </div>
          <div>
            <div className="text-xs text-green-600">P/L</div>
            <div className={`text-xl font-bold ${totalPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {totalPnL >= 0 ? '+' : ''}${totalPnL.toFixed(2)}
            </div>
          </div>
        </div>
      </div>

      {/* Slots */}
      <div className="border-2 border-yellow-500 bg-black/70 p-3 mb-3">
        <div className="text-sm font-bold text-yellow-400 mb-2">POSITION SLOTS</div>
        <div className="flex gap-2">
          {[...Array(slots)].map((_, i) => (
            <div key={i} className={`w-12 h-12 border-2 flex items-center justify-center ${
              i < openSlots ? 'border-green-500 bg-green-900/30 text-green-400' : 'border-gray-600 bg-gray-900/30 text-gray-600'
            }`}>
              {i < openSlots ? '●' : '○'}
            </div>
          ))}
        </div>
        <div className="text-xs text-green-500 mt-2">{openSlots}/{slots} ACTIVE • {availableSlots} AVAILABLE</div>
      </div>

      {/* Active Trades */}
      <div className="border-2 border-blue-500 bg-black/70 p-3 mb-3">
        <div className="text-sm font-bold text-blue-400 mb-2">ACTIVE POSITIONS</div>
        {trades.length === 0 ? (
          <div className="text-center text-gray-500 py-4">NO ACTIVE POSITIONS</div>
        ) : (
          <div className="space-y-2">
            {trades.map((trade) => (
              <div key={trade.id} className="border border-green-700 bg-black/50 p-2">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="text-sm font-bold text-green-400">{trade.symbol}</div>
                    <div className="text-xs text-green-600">{trade.direction} • {trade.volume} lots</div>
                  </div>
                  <div className="text-right">
                    <div className={`text-sm font-bold ${trade.equity >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {trade.equity >= 0 ? '+' : ''}${trade.equity.toFixed(2)}
                    </div>
                    <div className="text-xs text-gray-500">{trade.openPrice}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="grid grid-cols-2 gap-2 mb-3">
        <button onClick={onAlerts} className="border-2 border-green-500 bg-green-900/30 p-3 hover:bg-green-900/50 transition-colors text-green-400 font-bold">
          📡 ALERTS
        </button>
        <button onClick={onWarRoom} className="border-2 border-yellow-500 bg-yellow-900/30 p-3 hover:bg-yellow-900/50 transition-colors text-yellow-400 font-bold">
          🏛️ WAR ROOM
        </button>
        <button onClick={onStats} className="border-2 border-blue-500 bg-blue-900/30 p-3 hover:bg-blue-900/50 transition-colors text-blue-400 font-bold">
          📊 STATS
        </button>
        <button onClick={onCloseAll} className="border-2 border-red-500 bg-red-900/30 p-3 hover:bg-red-900/50 transition-colors text-red-400 font-bold" disabled={trades.length === 0}>
          ✕ CLOSE ALL
        </button>
      </div>

      <button onClick={onNotebook} className="w-full border-2 border-purple-500 bg-purple-900/30 p-3 hover:bg-purple-900/50 transition-colors text-purple-400 font-bold">
        📓 NOTEBOOK
      </button>
    </div>
  );
}
