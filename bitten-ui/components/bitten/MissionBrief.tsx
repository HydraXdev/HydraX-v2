"use client"

import React, { useState } from 'react';
import { PatternOverlayRenderer } from './PatternOverlayRenderer';
import { PATTERN_REGISTRY, type PatternId, type SignalSnapshot } from '@/lib/patterns/registry';

interface UserData {
  balance: number;
  activeTrades: number;
  maxTrades: number;
  riskPerTrade: number;
  potentialReward: number;
}

interface AlertData {
  pattern: string;
  patternId: number;
  pair: string;
  timeframe: string;
  session: string;
  timestamp: string;
  confidence: number;
  entry: number;
  takeProfit: number;
  stopLoss: number;
  pips: {
    tp: number;
    sl: number;
  };
  riskReward: number;
  snapshot?: SignalSnapshot; // Optional snapshot data
}

export interface MissionBriefProps {
  userData: UserData;
  alertData: AlertData;
  onExecute: () => void;
  executing?: boolean;
  onGoToDashboard?: () => void;
  onOpenNotebook?: () => void;
}

export const MissionBrief: React.FC<MissionBriefProps> = ({
  userData,
  alertData,
  onExecute,
  executing = false,
  onGoToDashboard,
  onOpenNotebook
}) => {
  const handleExecute = () => {
    onExecute();
  };

  // Calculate bullets remaining
  const bulletsRemaining = userData.maxTrades - userData.activeTrades;

  return (
    <div className="min-h-screen bg-gray-950 text-green-400 p-2 sm:p-4 font-mono">
      {/* Military Header with Frame */}
      <div className="relative border-4 border-gray-700 bg-gradient-to-b from-gray-800 to-gray-900 p-4 mb-3 shadow-2xl" style={{
        boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.5), 0 4px 8px rgba(0,0,0,0.5)'
      }}>
        {/* Corner rivets */}
        <div className="absolute top-1 left-1 w-2 h-2 rounded-full bg-gray-600 border border-gray-800"></div>
        <div className="absolute top-1 right-1 w-2 h-2 rounded-full bg-gray-600 border border-gray-800"></div>
        <div className="absolute bottom-1 left-1 w-2 h-2 rounded-full bg-gray-600 border border-gray-800"></div>
        <div className="absolute bottom-1 right-1 w-2 h-2 rounded-full bg-gray-600 border border-gray-800"></div>

        <div className="flex justify-between items-center">
          <div className="flex items-center gap-3">
            {/* Globe/Logo placeholder */}
            <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-gray-700 border-2 border-gray-600 flex items-center justify-center">
              <div className="w-6 h-6 sm:w-8 sm:h-8 rounded-full border-2 border-gray-500 opacity-50"></div>
            </div>
            {/* BITTEN text - military stencil style */}
            <div className="text-3xl sm:text-4xl font-bold tracking-wider" style={{
              color: '#8b7355',
              textShadow: '2px 2px 4px rgba(0,0,0,0.8)',
              fontFamily: 'Impact, Arial Black, sans-serif',
              letterSpacing: '0.15em'
            }}>
              BITTEN
            </div>
          </div>

          {/* Gear icon */}
          <div className="text-gray-600">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="3"/>
              <path d="M12 1v6m0 6v6m11-11h-6m-6 0H1m16.24 6.76l-4.24-4.24m-6 6l-4.24-4.24M19.07 19.07l-4.24-4.24m-6 6l-4.24-4.24"/>
            </svg>
          </div>
        </div>
      </div>

      {/* Alert Info Bar */}
      <div className="border-2 border-green-500 bg-black/50 p-3 mb-3">
        <div className="flex justify-between items-start gap-2">
          <div>
            <div className="text-xl sm:text-2xl font-bold text-green-400 mb-1">
              {alertData.pattern}
            </div>
            <div className="text-xs sm:text-sm text-green-500">
              {alertData.pair} | {alertData.timeframe} | {alertData.session}
            </div>
            <div className="text-xs text-green-600 mt-1">
              {alertData.timestamp}
            </div>
          </div>
          <div className="text-right">
            <div className="text-lg sm:text-xl font-bold text-yellow-400">
              {alertData.confidence}%
            </div>
            <div className="text-xs sm:text-sm text-green-500 mt-1">
              R:R {alertData.riskReward}
            </div>
          </div>
        </div>
      </div>

      {/* Pattern Chart with Overlay System */}
      <div className="border-2 border-green-500 bg-black/90 p-2 sm:p-3 mb-3">
        <div className="flex justify-between items-center mb-2">
          <div className="text-xs text-green-500 uppercase tracking-wide">
            Pattern Analysis Chart
          </div>
          {alertData.snapshot && (
            <div className="text-xs text-yellow-400">
              {PATTERN_REGISTRY[alertData.pattern as PatternId]?.signals || 0} signals @ {PATTERN_REGISTRY[alertData.pattern as PatternId]?.avgConfidence.toFixed(1)}%
            </div>
          )}
        </div>

        <div className="relative h-80 sm:h-96 bg-gradient-to-b from-gray-900 to-black border-2 border-green-600">
          {alertData.snapshot?.imageUrl ? (
            // Real detection-time snapshot with overlay
            <>
              <img
                src={alertData.snapshot.imageUrl}
                alt="Pattern Chart"
                className="absolute inset-0 w-full h-full object-contain"
              />
              <PatternOverlayRenderer
                patternId={alertData.pattern as PatternId}
                snapshot={alertData.snapshot}
                dimensions={{
                  width: alertData.snapshot.imageWidth || 800,
                  height: alertData.snapshot.imageHeight || 400
                }}
              />
            </>
          ) : (
            // Tactical fallback visualization
            <>
              {/* Price scale */}
              <div className="absolute left-0 top-0 bottom-8 w-16 bg-black/80 border-r-2 border-green-600 flex flex-col justify-around py-3 text-sm font-bold text-green-400">
                <div className="text-right pr-2">{alertData.takeProfit}</div>
                <div className="text-right pr-2">{(alertData.takeProfit - (alertData.takeProfit - alertData.entry) * 0.33).toFixed(5)}</div>
                <div className="text-right pr-2">{alertData.entry}</div>
                <div className="text-right pr-2">{(alertData.entry + (alertData.stopLoss - alertData.entry) * 0.33).toFixed(5)}</div>
                <div className="text-right pr-2">{alertData.stopLoss}</div>
              </div>

              {/* Main visual area */}
              <div className="absolute left-16 right-0 top-0 bottom-8">
                <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                  {/* TP Zone */}
                  <line x1="0" y1="15" x2="100" y2="15" stroke="#10b981" strokeWidth="0.8" strokeDasharray="2,2"/>
                  <rect x="75" y="10" width="24" height="8" fill="#10b981" opacity="0.9"/>
                  <text x="77" y="16" fill="#000" fontSize="5" fontWeight="bold">TP {alertData.pips.tp}p</text>

                  {/* Entry Zone */}
                  <line x1="0" y1="50" x2="100" y2="50" stroke="#3b82f6" strokeWidth="0.6" strokeDasharray="2,1"/>
                  <rect x="70" y="47" width="29" height="6" fill="#3b82f6" opacity="0.9"/>
                  <text x="72" y="51.5" fill="#000" fontSize="4" fontWeight="bold">ENTRY</text>

                  {/* SL Zone */}
                  <line x1="0" y1="78" x2="100" y2="78" stroke="#ef4444" strokeWidth="0.8" strokeDasharray="2,2"/>
                  <rect x="75" y="75" width="24" height="6" fill="#ef4444" opacity="0.9"/>
                  <text x="77" y="79.5" fill="#000" fontSize="5" fontWeight="bold">SL {alertData.pips.sl}p</text>

                  {/* Pattern-specific zones */}
                  <rect x="15" y="52" width="18" height="12" fill={PATTERN_REGISTRY[alertData.pattern as PatternId]?.color || '#fbbf24'} opacity="0.3" stroke={PATTERN_REGISTRY[alertData.pattern as PatternId]?.color || '#fbbf24'} strokeWidth="0.5"/>

                  {/* Price action path */}
                  <path
                    d="M 5,30 L 15,40 L 25,48 L 32,56 L 38,54 L 45,52 L 52,70 L 58,85"
                    stroke="#ffffff"
                    strokeWidth="1.5"
                    fill="none"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />

                  {/* Current position marker */}
                  <circle cx="58" cy="85" r="3" fill="#fbbf24" stroke="#f59e0b" strokeWidth="0.8">
                    <animate attributeName="r" values="3;4.5;3" dur="1.5s" repeatCount="indefinite"/>
                  </circle>

                  {/* Expected path */}
                  <path
                    d="M 58,85 L 65,70 L 72,50 L 80,30 L 88,18"
                    stroke="#06b6d4"
                    strokeWidth="2"
                    fill="none"
                    strokeLinecap="round"
                    strokeDasharray="4,2"
                  />
                  <polygon points="88,18 86,22 90,22" fill="#06b6d4"/>
                </svg>
              </div>

              {/* Time axis */}
              <div className="absolute left-16 right-0 bottom-0 h-8 bg-black/80 border-t-2 border-green-600 flex items-center justify-around text-sm font-bold">
                <span className="text-gray-500">{alertData.timestamp.split(' ')[1]}</span>
                <span className="text-yellow-400 text-lg">⬤ NOW</span>
                <span className="text-cyan-400">→ Future</span>
              </div>
            </>
          )}

          {/* Pattern legend chip */}
          <div className="absolute top-2 right-2 bg-black/90 border-2 border-green-500 p-2 text-xs">
            <div className="flex items-center gap-2 mb-1">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: PATTERN_REGISTRY[alertData.pattern as PatternId]?.color || '#fbbf24' }}></div>
              <span className="text-green-400 font-bold">{alertData.pattern}</span>
            </div>
            {PATTERN_REGISTRY[alertData.pattern as PatternId]?.description && (
              <div className="text-gray-400 text-xs">{PATTERN_REGISTRY[alertData.pattern as PatternId].description}</div>
            )}
          </div>
        </div>
      </div>

      {/* Execute Button */}
      <button
        onClick={handleExecute}
        disabled={executing}
        className="w-full border-2 border-green-500 bg-green-900/30 p-4 hover:bg-green-900/50 active:bg-green-900/70 transition-colors text-green-400 font-bold disabled:opacity-50 mb-3"
      >
        {executing ? '⏳ EXECUTING...' : '✓ EXECUTE TRADE'}
      </button>

      {/* User Financial Info - FROM DATABASE */}
      <div className="border-2 border-yellow-500 bg-black/70 p-3 mb-3">
        <div className="text-sm font-bold text-yellow-400 mb-2 flex items-center justify-between">
          <span>💰 YOUR TRADE PROFILE</span>
          <span className="text-green-400">${userData.balance.toFixed(2)}</span>
        </div>

        <div className="grid grid-cols-2 gap-3 mb-3">
          <div className="border border-red-500 bg-black/50 p-2 text-center">
            <div className="text-xs text-red-400">RISK</div>
            <div className="text-lg font-bold text-red-400">-${userData.riskPerTrade.toFixed(2)}</div>
          </div>
          <div className="border border-green-500 bg-black/50 p-2 text-center">
            <div className="text-xs text-green-400">REWARD</div>
            <div className="text-lg font-bold text-green-400">+${userData.potentialReward.toFixed(2)}</div>
          </div>
        </div>

        {/* Bullets/Ammo Visualization */}
        <div className="border-t border-yellow-600 pt-2">
          <div className="text-xs text-yellow-400 mb-2">REMAINING AMMO:</div>
          <div className="flex justify-center gap-2">
            {[...Array(userData.maxTrades)].map((_, i) => (
              <div key={i} className="relative">
                {i < bulletsRemaining ? (
                  // Filled bullet - available
                  <svg width="20" height="32" viewBox="0 0 20 32" className="drop-shadow-lg">
                    <ellipse cx="10" cy="8" rx="6" ry="8" fill="#fbbf24" stroke="#f59e0b" strokeWidth="1"/>
                    <rect x="4" y="8" width="12" height="20" fill="#fbbf24" stroke="#f59e0b" strokeWidth="1"/>
                    <rect x="4" y="28" width="12" height="3" fill="#92400e"/>
                  </svg>
                ) : (
                  // Empty outline - used
                  <svg width="20" height="32" viewBox="0 0 20 32" className="opacity-30">
                    <ellipse cx="10" cy="8" rx="6" ry="8" fill="none" stroke="#78716c" strokeWidth="1"/>
                    <rect x="4" y="8" width="12" height="20" fill="none" stroke="#78716c" strokeWidth="1"/>
                    <rect x="4" y="28" width="12" height="3" fill="#1c1917" stroke="#78716c" strokeWidth="1"/>
                  </svg>
                )}
              </div>
            ))}
          </div>
          <div className="text-center text-xs text-green-500 mt-2">
            {bulletsRemaining}/{userData.maxTrades} SHOTS AVAILABLE
          </div>
        </div>
      </div>

      {/* Pattern Explanation - Condensed */}
      <div className="border-2 border-yellow-500 bg-black/70 p-3 mb-3">
        <div className="text-sm font-bold text-yellow-400 mb-2">📋 WHAT HAPPENED</div>
        <div className="space-y-1 text-xs sm:text-sm">
          <div className="text-green-400">✓ Price swept liquidity below structure</div>
          <div className="text-green-400">✓ Strong reversal candle formed</div>
          <div className="text-green-400">✓ Pattern confidence: {alertData.confidence}%</div>
        </div>
      </div>

      {/* Navigation Buttons */}
      <div className="space-y-2 mb-3">
        <div className="grid grid-cols-2 gap-3">
          <button
            onClick={onGoToDashboard}
            className="border-2 border-blue-500 bg-blue-900/30 p-4 hover:bg-blue-900/50 active:bg-blue-900/70 transition-colors text-blue-400 font-bold"
          >
            📊 STATUS BOARD
          </button>
          <button
            onClick={onOpenNotebook}
            className="border-2 border-purple-500 bg-purple-900/30 p-4 hover:bg-purple-900/50 active:bg-purple-900/70 transition-colors text-purple-400 font-bold"
          >
            📓 NOTEBOOK
          </button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="border-2 border-green-500 bg-black/50 p-2 text-xs text-center text-green-500">
        RISK ${userData.riskPerTrade.toFixed(2)} TO WIN ${userData.potentialReward.toFixed(2)} | R:R {alertData.riskReward} | {alertData.pips.tp} PIPS TARGET
      </div>
    </div>
  );
};

export default MissionBrief;
