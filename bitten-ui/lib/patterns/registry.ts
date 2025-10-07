// Pattern Registry with Live Performance Data
export const PATTERN_REGISTRY = {
  KALMAN_QUICKFIRE: {
    name: "KALMAN QUICKFIRE",
    signals: 1094,
    avgConfidence: 84.2,
    color: "#10b981", // emerald
    description: "Adaptive filter isolates clean directional push in chop",
  },
  BB_SCALP: {
    name: "BB SCALP",
    signals: 460,
    avgConfidence: 86.5,
    color: "#3b82f6", // blue
    description: "2.0 SD Bollinger mean reversion + squeeze breakouts",
  },
  ORDER_BLOCK_BOUNCE: {
    name: "ORDER BLOCK BOUNCE",
    signals: 340,
    avgConfidence: 79.3,
    color: "#fbbf24", // gold
    description: "Institutional accumulation zone bounce",
  },
  SWEEP_RETURN: {
    name: "SWEEP & RETURN",
    signals: 302,
    avgConfidence: 75.9,
    color: "#ef4444", // red
    description: "Liquidity sweep with impulsive return",
  },
  FAIR_VALUE_GAP_FILL: {
    name: "FAIR VALUE GAP FILL",
    signals: 258,
    avgConfidence: 90.6,
    color: "#06b6d4", // cyan
    description: "4+ pip inefficiency fill",
  },
  LIQUIDITY_SWEEP_REVERSAL: {
    name: "LIQUIDITY SWEEP REVERSAL",
    signals: 19,
    avgConfidence: 76.1,
    color: "#ef4444", // red
    description: "3+ pip sweep beyond H/L with reversal",
  },
  VCB_BREAKOUT: {
    name: "VCB BREAKOUT",
    signals: 18,
    avgConfidence: 84.9,
    color: "#8b5cf6", // purple
    description: "Volatility compression (<0.7 ATR) breakout",
  },
  MOMENTUM_BURST: {
    name: "MOMENTUM BURST",
    signals: 5,
    avgConfidence: 81.2,
    color: "#f59e0b", // amber
    description: "Multi-timeframe acceleration breakout",
  },
  // Inactive patterns
  BLIND_SPOT: {
    name: "BLIND SPOT",
    signals: 0,
    avgConfidence: 0,
    color: "#6b7280",
    description: "No recent signals",
  },
  TRAPDOOR_SSR: {
    name: "TRAPDOOR SSR",
    signals: 0,
    avgConfidence: 0,
    color: "#6b7280",
    description: "No recent signals",
  },
  PRESSURE_VALVE: {
    name: "PRESSURE VALVE",
    signals: 0,
    avgConfidence: 0,
    color: "#6b7280",
    description: "No recent signals",
  },
  EMA_RSI_BB_VWAP: {
    name: "EMA RSI BB VWAP",
    signals: 0,
    avgConfidence: 0,
    color: "#6b7280",
    description: "No recent signals",
  },
  EMA_RSI_SCALP: {
    name: "EMA RSI SCALP",
    signals: 0,
    avgConfidence: 0,
    color: "#6b7280",
    description: "No recent signals",
  },
} as const;

export type PatternId = keyof typeof PATTERN_REGISTRY;

// Pattern Overlay Types
export interface PatternLevel {
  price: number;
  label: string;
  color: string;
  style?: "solid" | "dashed";
}

export interface PatternZone {
  priceTop: number;
  priceBottom: number;
  tStart: number; // epoch ms
  tEnd: number; // epoch ms
  label: string;
  color: string;
  opacity?: number;
}

export interface PatternMarker {
  t: number; // epoch ms
  price: number;
  kind:
    | "sweep"
    | "reclaim"
    | "break"
    | "wickReject"
    | "kalmanSignal"
    | "squeeze"
    | "vcb"
    | "touch"
    | "midpoint"
    | "momentum";
  label?: string;
}

export interface PatternPath {
  points: Array<{ t: number; price: number }>;
  style: "expected" | "displacement";
  color?: string;
}

export interface PatternNote {
  t: number;
  price: number;
  text: string;
}

export interface PatternOverlay {
  levels?: PatternLevel[];
  zones?: PatternZone[];
  markers?: PatternMarker[];
  paths?: PatternPath[];
  notes?: PatternNote[];
}

// Snapshot data structure
export interface SignalSnapshot {
  snapshotId: string;
  imageUrl?: string; // Optional - for real detection-time PNG
  imageWidth?: number;
  imageHeight?: number;
  xStartTs: number; // chart left bound (epoch ms)
  xEndTs: number; // chart right bound (epoch ms)
  yMin: number; // price bottom
  yMax: number; // price top
  chartTemplateVersion?: string;
  overlayBase: PatternOverlay;
}

// Coordinate transform utilities
export function domainToPixels(
  t: number,
  price: number,
  bounds: { xStartTs: number; xEndTs: number; yMin: number; yMax: number },
  dimensions: { width: number; height: number },
): { x: number; y: number } {
  const x =
    ((t - bounds.xStartTs) / (bounds.xEndTs - bounds.xStartTs)) *
    dimensions.width;
  const y =
    dimensions.height -
    ((price - bounds.yMin) / (bounds.yMax - bounds.yMin)) * dimensions.height;
  return { x, y };
}
