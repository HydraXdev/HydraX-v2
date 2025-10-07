"use client"

import React from 'react';

export interface LegendItem {
  label: string;
  color: string;
  icon?: 'line' | 'dot' | 'gate';
}

export interface LegendProps {
  items: LegendItem[];
  className?: string;
}

/**
 * Legend - Chart legend with color chips
 *
 * Features:
 * - Compact horizontal layout
 * - Color-coded indicators (line, dot, or gate icons)
 * - Used for mission charts (Past/Now/Expected)
 */
export function Legend({
  items,
  className = '',
}: LegendProps) {
  return (
    <div className={`flex items-center gap-4 ${className}`} role="list" aria-label="Chart legend">
      {items.map((item, index) => (
        <div key={index} className="flex items-center gap-1.5" role="listitem">
          {/* Icon based on type */}
          {item.icon === 'line' && (
            <div className="w-4 h-px" style={{ backgroundColor: item.color }} aria-hidden="true" />
          )}
          {item.icon === 'dot' && (
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }} aria-hidden="true" />
          )}
          {item.icon === 'gate' && (
            <div className="w-1 h-3 rounded-sm" style={{ backgroundColor: item.color }} aria-hidden="true" />
          )}
          {!item.icon && (
            <div className="w-3 h-3 rounded" style={{ backgroundColor: item.color }} aria-hidden="true" />
          )}

          <span className="text-xs text-[#cbd5e0]">{item.label}</span>
        </div>
      ))}
    </div>
  );
}

/**
 * Common legend presets for BITTEN charts
 */
export const LEGEND_PRESETS = {
  tradePath: [
    { label: 'Past', color: '#4a5568', icon: 'line' as const },
    { label: 'Now', color: '#fbbf24', icon: 'dot' as const },
    { label: 'Expected', color: '#34d399', icon: 'line' as const },
  ],
  zones: [
    { label: 'TP', color: '#34d399', icon: 'gate' as const },
    { label: 'Entry', color: '#cbd5e0', icon: 'gate' as const },
    { label: 'SL', color: '#ef4444', icon: 'gate' as const },
  ],
};
