"use client"

import React, { useEffect, useState } from "react";

// Type definitions
interface Trade {
  id: number;
  pair: string;
  entry: number;
  current: number;
  stopLoss: number;
  takeProfit: number;
  equity: number;
  lots: number;
  startTime: Date;
  history?: number[];
}

interface AccountData {
  balance: number;
  equity: number;
  openPositions: number;
  maxSlots: number;
  trades: Trade[];
}

const clamp01 = (v: number) => Math.max(0, Math.min(1, v));
const pct = (v: number) => `${(v * 100).toFixed(0)}%`;
const fmtUSD = (n: number) => n.toLocaleString(undefined, { style: "currency", currency: "USD" });
const fmtSigned = (n: number) => (n >= 0 ? `+${n.toFixed(2)}` : n.toFixed(2));

function durationSince(start: Date, now: Date) {
  const diff = +now - +start;
  const h = Math.floor(diff / 3_600_000);
  const m = Math.floor((diff % 3_600_000) / 60_000);
  const s = Math.floor((diff % 60_000) / 1000);
  return h > 0 ? `${h}h ${m}m` : m > 0 ? `${m}m ${s}s` : `${s}s`;
}

function Beacon({ label, ok = true, value }: { label: string; ok?: boolean; value?: string }) {
  return (
    <div className="flex items-center gap-1 text-xs text-zinc-400">
      <div className={`h-2.5 w-2.5 rounded-full ${ok ? "bg-emerald-400" : "bg-red-500"}`} />
      <span className="uppercase tracking-wide">{label}</span>
      {value && <span className="tabular-nums text-zinc-300">{value}</span>}
    </div>
  );
}

function Sparkline({ data = [] }: { data?: number[] }) {
  if (!data || !data.length) return null;
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = Math.max(1e-9, max - min);
  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * 100;
    const y = 16 - ((v - min) / range) * 16;
    return `${x.toFixed(2)},${y.toFixed(2)}`;
  }).join(" ");
  const path = `M ${points}`;

  return (
    <svg viewBox="0 0 100 16" className="w-full h-4">
      <path d={path} fill="none" stroke="currentColor" strokeWidth="1.5" className="text-emerald-400/80" />
    </svg>
  );
}

function TradeLane({ trade, now }: { trade: Trade; now: Date }) {
  const range = trade.takeProfit - trade.stopLoss;
  const progress = clamp01((trade.current - trade.stopLoss) / (range || 1));
  const pos = progress * 100;
  const isPos = trade.equity >= 0;
  const agingSec = Math.floor((+now - +trade.startTime) / 1000);
  const ageTint = agingSec > 3 * 3600 ? "ring-yellow-600/50" : "ring-emerald-700/40";

  return (
    <div className="bg-black/50 border border-emerald-700/50 rounded-lg overflow-hidden">
      <div className="p-3 sm:p-4">
        <div className="flex flex-col sm:flex-row sm:items-center gap-3">
          {/* Left meta */}
          <div className="w-full sm:w-40">
            <div className="flex items-center justify-between">
              <div className="text-lg font-bold text-emerald-300">{trade.pair}</div>
              <span className="border border-zinc-700 text-zinc-300 bg-zinc-900/40 px-2 py-0.5 text-xs rounded">{trade.lots} LOTS</span>
            </div>
            <div className="text-[11px] text-zinc-400 mt-0.5 flex items-center gap-1">
              ⏱ {durationSince(trade.startTime, now)}
            </div>
          </div>

          {/* Track */}
          <div className="relative flex-1">
            <div className={`relative h-12 bg-zinc-900 border border-emerald-700/50 ring-1 ${ageTint} rounded`}>
              {/* SL gate */}
              <div className="absolute left-0 top-0 bottom-0 w-1 bg-red-600 rounded-l"/>
              <div className="absolute left-2 top-1/2 -translate-y-1/2 text-[11px] text-red-400">SL {trade.stopLoss}</div>

              {/* Fill */}
              <div className={`absolute top-0 bottom-0 transition-all duration-300 rounded-l ${isPos ? "bg-emerald-600/60" : "bg-red-600/60"}`} style={{ width: pct(progress) }} />

              {/* Cursor (NOW) */}
              <div className="absolute top-0 bottom-0 w-1 bg-yellow-400" style={{ left: pct(progress) }} />
              <div className="absolute -translate-y-1/2 top-1/2 text-[11px] text-yellow-300 font-bold whitespace-nowrap" style={{ left: `calc(${pct(progress)} + 6px)` }}>{trade.current}</div>

              {/* TP gate */}
              <div className="absolute right-0 top-0 bottom-0 w-1 bg-emerald-600 rounded-r"/>
              <div className="absolute right-2 top-1/2 -translate-y-1/2 text-[11px] text-emerald-400">TP {trade.takeProfit}</div>
            </div>
            <div className="mt-1 text-[11px] text-zinc-400">ENTRY {trade.entry}</div>
          </div>

          {/* P/L tile */}
          <div className="w-full sm:w-44 text-right border-2 border-emerald-700/50 bg-black/60 p-3 rounded">
            <div className="text-[11px] text-zinc-400">P/L</div>
            <div className={`text-2xl font-bold tabular-nums ${isPos ? "text-emerald-300" : "text-red-400"}`}>{fmtSigned(trade.equity)}</div>
            <div className="text-[11px] text-zinc-400">USD</div>
            {trade.history && trade.history.length > 1 && <div className="mt-1 text-emerald-400/70"><Sparkline data={trade.history} /></div>}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function StatusBoardLive() {
  const [now, setNow] = useState(new Date());
  const [accountData, setAccountData] = useState<AccountData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Get user ID from URL params
  const userId = typeof window !== 'undefined' ? new URLSearchParams(window.location.search).get('user_id') || '7176191872' : '7176191872';

  // Fetch real account data
  useEffect(() => {
    async function fetchAccountData() {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8888';
        const response = await fetch(`${apiUrl}/api/status/${userId}`);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
          setAccountData(data.data);
          setError(null);
        } else {
          setError(data.error || 'Failed to load data');
        }
      } catch (err) {
        console.error('Failed to fetch account data:', err);
        setError('Connection error');
      } finally {
        setLoading(false);
      }
    }

    fetchAccountData();
    const interval = setInterval(fetchAccountData, 3000); // Refresh every 3 seconds

    return () => clearInterval(interval);
  }, [userId]);

  // Update clock every second
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 text-emerald-300 font-mono flex items-center justify-center">
        <div className="text-center">
          <div className="text-2xl font-bold mb-2">Loading...</div>
          <div className="text-sm text-zinc-400">Connecting to live data feed</div>
        </div>
      </div>
    );
  }

  if (error || !accountData) {
    return (
      <div className="min-h-screen bg-zinc-950 text-emerald-300 font-mono flex items-center justify-center">
        <div className="text-center">
          <div className="text-2xl font-bold text-red-400 mb-2">⚠️ Connection Error</div>
          <div className="text-sm text-zinc-400">{error || 'No data available'}</div>
        </div>
      </div>
    );
  }

  const { balance, equity, openPositions, maxSlots, trades } = accountData;
  const totalPL = equity - balance;
  const dd = (equity - balance) / balance;

  return (
    <div className="min-h-screen bg-zinc-950 text-emerald-300 font-mono">
      {/* Header */}
      <div className="border-b border-emerald-800/50 bg-gradient-to-b from-zinc-900 to-black">
        <div className="mx-auto max-w-7xl p-3 sm:p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
          <div>
            <div className="text-2xl sm:text-3xl font-extrabold tracking-[0.15em]" style={{ color: "#8b7355" }}>⬢ B.I.T.T.E.N</div>
            <div className="text-emerald-400/70 text-xs sm:text-sm">LIVE POSITION MONITOR</div>
          </div>
          <div className="flex items-center gap-4 text-zinc-400 flex-wrap">
            <Beacon label="OPERATIONAL" />
            <Beacon label="SECURE" />
            <Beacon label="LIVE" ok={true} />
            <time className="tabular-nums text-zinc-200">{now.toLocaleTimeString(undefined, { hour12: false })}</time>
            <span className="text-zinc-400">{now.toLocaleDateString(undefined, { month: "short", day: "numeric" })}</span>
          </div>
        </div>
        <div className="h-1 bg-emerald-500"></div>
      </div>

      {/* Account Telemetry */}
      <div className="mx-auto max-w-7xl p-3 sm:p-4">
        <div className="bg-black/60 border border-emerald-700/50 rounded-lg">
          <div className="p-3 sm:p-4">
            <div className="grid sm:grid-cols-3 gap-3">
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">BALANCE</span>
                  <span className="text-2xl font-bold tabular-nums">{fmtUSD(balance)}</span>
                </div>
                <div className="mt-2 text-[11px] text-zinc-400">Base capital</div>
              </div>
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">EQUITY</span>
                  <span className={`text-2xl font-bold tabular-nums ${totalPL >= 0 ? "text-emerald-300" : "text-red-400"}`}>{fmtUSD(equity)}</span>
                </div>
                <div className="mt-2">
                  <div className="text-[11px] text-zinc-400 mb-1">Live Δ from balance</div>
                  <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                    <div className={`${dd >= 0 ? "bg-emerald-500" : "bg-red-500"} h-2 transition-all`} style={{ width: `${Math.min(100, Math.abs(dd) * 100)}%` }} />
                  </div>
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">OPEN POSITIONS</span>
                  <span className="text-2xl font-bold tabular-nums">{openPositions}/{maxSlots}</span>
                </div>
                <div className="mt-2 text-[11px] text-zinc-400">Capacity remaining: {Math.max(0, maxSlots - openPositions)}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Trades */}
      <div className="mx-auto max-w-7xl p-3 sm:p-4 space-y-3">
        {trades.map(t => <TradeLane key={t.id} trade={t} now={now} />)}

        {/* Empty slots */}
        {Array.from({ length: Math.max(0, maxSlots - openPositions) }).map((_, i) => (
          <div key={`empty-${i}`} className="bg-black/30 border border-zinc-800 rounded-lg">
            <div className="p-3 sm:p-4">
              <div className="flex items-center gap-3 sm:gap-4 h-10">
                <div className="w-20 sm:w-32 text-zinc-600 text-xs sm:text-sm">SLOT {openPositions + i + 1}</div>
                <div className="flex-1 bg-zinc-900/60 h-full grid place-items-center text-zinc-600 text-xs sm:text-sm rounded">[ AVAILABLE ]</div>
                <div className="w-16 sm:w-40 text-right text-zinc-600 text-xs sm:text-sm">—</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Footer Status Bar */}
      <div className="mx-auto max-w-7xl p-3 sm:p-4 pt-0">
        <div className="bg-black/60 border border-emerald-700/50 rounded-lg">
          <div className="p-2 text-center text-[12px] text-emerald-400">
            <span className="hidden sm:inline">SYSTEM STATUS: </span>
            <span className="inline-flex items-center gap-4 flex-wrap justify-center">
              <span className="inline-flex items-center gap-1"><div className="h-2.5 w-2.5 rounded-full bg-emerald-400"/> OPERATIONAL</span>
              <span className="inline-flex items-center gap-1">🔒 SECURE</span>
              <span className="inline-flex items-center gap-1">📶 LIVE DATA</span>
              <span className="inline-flex items-center gap-1">💻 HYDRA NODE OK</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
