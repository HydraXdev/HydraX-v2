// Event bus contracts - THE ONLY THINGS UI NEEDS FROM BACKEND
// Clean separation: components never know about backend structure

// User/account
export type UserProfile = {
  id: string;
  codename: string;
  balance: number;
  maxTrades: number;
  activeTrades: number;
  riskPerTrade: number;
  potentialReward: number;
  level: 'NIBBLER' | 'FANG_I' | 'FANG_II' | 'FANG_III' | 'COMMANDER' | string;
};

// Mission alert (trading signal)
export type AlertData = {
  pattern: string;
  patternId: number;
  pair: string;
  timeframe: string;
  session: string;
  timestamp: string; // ISO
  confidence: number;
  entry: number;
  takeProfit: number;
  stopLoss: number;
  pips: { tp: number; sl: number };
  riskReward: number;
  signalId?: string;
  direction?: 'BUY' | 'SELL';
};

// Live trade position
export type LiveTrade = {
  id: string | number;
  pair: string;
  entry: number;
  current: number;
  stopLoss: number;
  takeProfit: number;
  equity: number; // P/L in currency
  lots: number;
  startTime: string; // ISO
  direction: 'BUY' | 'SELL';
  history?: number[]; // optional sparkline data
};

// System health
export type SystemStatus = {
  secure: boolean;
  latencyMs: number;
  hydraNode: 'OK' | 'WARN' | 'DOWN';
};

// Stats/Analytics types
export type EquityPoint = {
  t: string;        // timestamp ISO
  balance: number;
  equity: number;
  dd?: number;      // drawdown percentage (optional)
};

export type KPI = {
  label: string;
  value: string;
  sub?: string;     // subtitle/secondary info
};

export type StatEvent = {
  id: string | number;
  when: string;     // ISO timestamp
  title: string;
  delta: number;    // P/L amount
  tag?: 'WIN' | 'LOSS' | 'INFO';
};

export type DistItem = {
  name: string;
  value: number;
};

// Streams/topics UI cares about
export type BusTopics = {
  'user.profile': UserProfile;
  'mission.alert': AlertData;
  'trades.open': LiveTrade[];        // snapshot of all open trades
  'trades.delta': LiveTrade;         // point update for one trade
  'system.status': SystemStatus;
  'stats.equity': EquityPoint[];     // equity curve series
  'stats.kpis': KPI[];               // key performance indicators
  'stats.events': StatEvent[];       // recent trading events
  'stats.dist.pair': DistItem[];     // distribution by pair
  'stats.dist.session': DistItem[];  // distribution by session
};

// Topic names for type safety
export type TopicName = keyof BusTopics;
