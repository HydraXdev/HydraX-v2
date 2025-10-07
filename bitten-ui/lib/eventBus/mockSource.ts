"use client";

import type {
  BusTopics,
  TopicName,
  UserProfile,
  AlertData,
  LiveTrade,
  SystemStatus,
} from "./contracts";

/**
 * Mock event source for development
 * Only runs when NEXT_PUBLIC_USE_MOCKS='1'
 *
 * Emits realistic fake events on intervals:
 * - user.profile (once on start)
 * - mission.alert (every 20-40s)
 * - trades.open (initial snapshot + deltas every 2-4s)
 * - system.status (every 10s)
 */

type EmitFn = <T extends TopicName>(topic: T, data: BusTopics[T]) => void;

const PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"];
const PATTERNS = [
  "LIQUIDITY_SWEEP_REVERSAL",
  "ORDER_BLOCK_BOUNCE",
  "FAIR_VALUE_GAP_FILL",
  "VCB_BREAKOUT",
  "SWEEP_RETURN",
];
const SESSIONS = ["LONDON", "NY", "ASIAN", "OVERLAP"];

function randomItem<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

function randomBetween(min: number, max: number): number {
  return Math.random() * (max - min) + min;
}

let signalCounter = 1000;
let tradeCounter = 5000;

function generateMockAlert(): AlertData {
  const pair = randomItem(PAIRS);
  const pattern = randomItem(PATTERNS);
  const confidence = Math.floor(randomBetween(70, 95));
  const entry = randomBetween(1.0, 1.3);
  const slPips = Math.floor(randomBetween(15, 30));
  const tpPips = Math.floor(randomBetween(30, 60));

  return {
    pattern,
    patternId: signalCounter++,
    pair,
    timeframe: "M15",
    session: randomItem(SESSIONS),
    timestamp: new Date().toISOString(),
    confidence,
    entry,
    takeProfit: entry + tpPips * 0.0001,
    stopLoss: entry - slPips * 0.0001,
    pips: { tp: tpPips, sl: slPips },
    riskReward: parseFloat((tpPips / slPips).toFixed(2)),
    signalId: `ELITE_${pair}_${Date.now()}`,
    direction: Math.random() > 0.5 ? "BUY" : "SELL",
  };
}

function generateMockTrade(): LiveTrade {
  const pair = randomItem(PAIRS);
  const entry = randomBetween(1.0, 1.3);
  const direction = Math.random() > 0.5 ? "BUY" : "SELL";
  const slPips = randomBetween(15, 30);
  const tpPips = randomBetween(30, 60);

  return {
    id: tradeCounter++,
    pair,
    entry,
    current: entry + randomBetween(-0.001, 0.001),
    stopLoss: entry - slPips * 0.0001,
    takeProfit: entry + tpPips * 0.0001,
    equity: randomBetween(-50, 100),
    lots: parseFloat(randomBetween(0.1, 1.0).toFixed(2)),
    startTime: new Date(Date.now() - Math.random() * 3600000).toISOString(),
    direction,
    history: Array.from({ length: 20 }, () => randomBetween(-30, 50)),
  };
}

let mockTrades: LiveTrade[] = [];

export function startMockEvents(emit: EmitFn) {
  if (process.env.NEXT_PUBLIC_USE_MOCKS !== "1") {
    console.warn(
      "[MockSource] Not starting - NEXT_PUBLIC_USE_MOCKS not set to 1",
    );
    return () => {};
  }

  console.log("[MockSource] Starting mock event stream...");

  // Emit initial user profile
  const userProfile: UserProfile = {
    id: "7176191872",
    codename: "VIPER_SIX",
    balance: 5420.5,
    maxTrades: 7,
    activeTrades: 3,
    riskPerTrade: 108.41, // 2% of balance
    potentialReward: 325.23,
    level: "COMMANDER",
  };
  emit("user.profile", userProfile);

  // Generate initial trades
  mockTrades = Array.from({ length: 3 }, generateMockTrade);
  emit("trades.open", mockTrades);

  // Emit system status
  const emitSystemStatus = () => {
    const status: SystemStatus = {
      secure: true,
      latencyMs: Math.floor(randomBetween(50, 200)),
      hydraNode: Math.random() > 0.9 ? "WARN" : "OK",
    };
    emit("system.status", status);
  };
  emitSystemStatus();

  // Schedule recurring events
  const intervals: NodeJS.Timeout[] = [];

  // Mission alerts every 20-40s
  intervals.push(
    setInterval(
      () => {
        const alert = generateMockAlert();
        console.log("[MockSource] Emitting mission.alert:", alert.pair);
        emit("mission.alert", alert);
      },
      randomBetween(20000, 40000),
    ),
  );

  // Trade deltas every 2-4s
  intervals.push(
    setInterval(
      () => {
        if (mockTrades.length > 0) {
          const trade =
            mockTrades[Math.floor(Math.random() * mockTrades.length)];

          // Simulate price movement
          const movement = randomBetween(-0.0002, 0.0002);
          trade.current += movement;
          trade.equity =
            ((trade.current - trade.entry) / trade.entry) * trade.lots * 100000;

          // Update history
          if (trade.history) {
            trade.history.push(trade.equity);
            trade.history = trade.history.slice(-20);
          }

          emit("trades.delta", { ...trade });
        }
      },
      randomBetween(2000, 4000),
    ),
  );

  // System status every 10s
  intervals.push(setInterval(emitSystemStatus, 10000));

  // Generate stats data
  const generateEquitySeries = () => {
    const baseBalance = 10000;
    const now = Date.now();
    const points: BusTopics["stats.equity"] = [];

    for (let i = 60; i >= 0; i--) {
      const t = new Date(now - i * 3600000).toISOString(); // hourly points
      const drift = (60 - i) * 15; // gentle upward trend
      const noise = Math.sin(i / 10) * 200 + randomBetween(-100, 100);
      const balance = baseBalance;
      const equity = baseBalance + drift + noise;
      const dd = equity < balance ? ((balance - equity) / balance) * 100 : 0;

      points.push({ t, balance, equity, dd });
    }

    return points;
  };

  let equitySeries = generateEquitySeries();
  emit("stats.equity", equitySeries);

  // Generate initial KPIs
  const kpis: BusTopics["stats.kpis"] = [
    { label: "Win Rate", value: "68.5%", sub: "137/200 trades" },
    { label: "Avg R:R", value: "1.85:1", sub: "Risk/Reward" },
    { label: "Profit Factor", value: "2.34", sub: "Gross P/L ratio" },
    { label: "Best Trade", value: "+$427", sub: "GBPUSD 3d ago" },
    { label: "Longest Streak", value: "9 wins", sub: "Last week" },
    { label: "Avg Hold", value: "2.3h", sub: "Position duration" },
  ];
  emit("stats.kpis", kpis);

  // Generate initial events
  const generateEvents = () => {
    const events: BusTopics["stats.events"] = [];
    for (let i = 0; i < 8; i++) {
      const isWin = Math.random() > 0.35;
      events.push({
        id: 9000 + i,
        when: new Date(Date.now() - i * 1800000).toISOString(),
        title: `${randomItem(PAIRS)} ${isWin ? "WIN" : "LOSS"}`,
        delta: isWin ? randomBetween(50, 200) : -randomBetween(30, 100),
        tag: isWin ? "WIN" : "LOSS",
      });
    }
    return events.reverse();
  };

  let statsEvents = generateEvents();
  emit("stats.events", statsEvents);

  // Generate distributions
  emit("stats.dist.pair", [
    { name: "EURUSD", value: 45 },
    { name: "GBPUSD", value: 28 },
    { name: "USDJPY", value: 15 },
    { name: "AUDUSD", value: 8 },
    { name: "USDCAD", value: 4 },
  ]);

  emit("stats.dist.session", [
    { name: "LONDON", value: 42 },
    { name: "NY", value: 35 },
    { name: "OVERLAP", value: 18 },
    { name: "ASIAN", value: 5 },
  ]);

  // Update equity series every 15s (add new point)
  intervals.push(
    setInterval(() => {
      const lastPoint = equitySeries[equitySeries.length - 1];
      const newEquity = lastPoint.equity + randomBetween(-50, 80);
      const newPoint = {
        t: new Date().toISOString(),
        balance: lastPoint.balance,
        equity: newEquity,
        dd:
          newEquity < lastPoint.balance
            ? ((lastPoint.balance - newEquity) / lastPoint.balance) * 100
            : 0,
      };

      equitySeries.push(newPoint);
      equitySeries = equitySeries.slice(-60); // keep last 60 points
      emit("stats.equity", equitySeries);
    }, 15000),
  );

  // Rotate events every 20s
  intervals.push(
    setInterval(() => {
      const isWin = Math.random() > 0.35;
      statsEvents.shift();
      statsEvents.push({
        id: Date.now(),
        when: new Date().toISOString(),
        title: `${randomItem(PAIRS)} ${isWin ? "WIN" : "LOSS"}`,
        delta: isWin ? randomBetween(50, 200) : -randomBetween(30, 100),
        tag: isWin ? "WIN" : "LOSS",
      });
      emit("stats.events", [...statsEvents]);
    }, 20000),
  );

  // Cleanup function
  return () => {
    console.log("[MockSource] Stopping mock event stream");
    intervals.forEach(clearInterval);
  };
}
