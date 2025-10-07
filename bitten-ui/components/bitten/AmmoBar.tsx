"use client"

import React from 'react';

export interface AmmoBarProps {
  maxTrades: number;
  activeTrades: number;
  className?: string;
}

/**
 * AmmoBar - Visual representation of trade capacity
 *
 * Features:
 * - Bullet icons showing available slots
 * - Filled bullets = used slots, empty = available
 * - Color-coded: green (available), yellow (used), red (at capacity)
 * - Accessible labels
 */
export function AmmoBar({
  maxTrades,
  activeTrades,
  className = '',
}: AmmoBarProps) {
  const availableSlots = maxTrades - activeTrades;
  const bullets = Array.from({ length: maxTrades });

  return (
    <div className={`flex items-center gap-1 ${className}`} role="status" aria-label={`${availableSlots} of ${maxTrades} trade slots available`}>
      {bullets.map((_, index) => {
        const isUsed = index < activeTrades;
        return (
          <div
            key={index}
            className={`
              w-2 h-5 rounded-sm
              ${isUsed ? 'bg-[#fbbf24]' : 'bg-[#34d399]'}
              ${activeTrades === maxTrades ? 'animate-pulse' : ''}
            `}
            aria-hidden="true"
          />
        );
      })}
      <span className="ml-2 text-xs font-mono tabular-nums text-[#cbd5e0]">
        {availableSlots}/{maxTrades}
      </span>
    </div>
  );
}
