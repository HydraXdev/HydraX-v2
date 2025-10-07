"use client"

import React, { useEffect, useState } from "react";
import { useRouter } from 'next/navigation';

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

interface BeaconProps {
  label: string;
  ok?: boolean;
  value?: string;
}

function Beacon({ label, ok = true, value }: BeaconProps) {
  return (
    <div className="flex items-center gap-1 text-xs text-zinc-400 m-0 p-0">
      <div className={`h-2.5 w-2.5 rounded-full m-0 p-0 ${ok ? "bg-emerald-400" : "bg-red-500"}`} />
      <span className="uppercase tracking-wide m-0 p-0">{label}</span>
      {value && <span className="tabular-nums text-zinc-300 m-0 p-0">{value}</span>}
    </div>
  );
}

interface SparklineProps {
  data?: number[];
}

function Sparkline({ data = [] }: SparklineProps) {
  if (!data.length) return null;
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
    <svg viewBox="0 0 100 16" className="w-full h-4 m-0 p-0">
      <path d={path} fill="none" stroke="currentColor" strokeWidth="1.5" className="text-emerald-400/80" />
    </svg>
  );
}

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

interface TradeLaneProps {
  trade: Trade;
  now: Date;
}

function TradeLane({ trade, now }: TradeLaneProps) {
  const range = trade.takeProfit - trade.stopLoss;
  const progress = clamp01((trade.current - trade.stopLoss) / (range || 1));
  const pos = progress * 100;
  const isPos = trade.equity >= 0;
  const agingSec = Math.floor((+now - +trade.startTime) / 1000);
  const ageTint = agingSec > 3 * 3600 ? "ring-yellow-600/50" : "ring-emerald-700/40";

  return (
    <div className="bg-black/50 border border-emerald-700/50 rounded-lg overflow-hidden m-0">
      <div className="p-3 sm:p-4 m-0">
        <div className="flex flex-col sm:flex-row sm:items-center gap-3 m-0 p-0">
          {/* Left meta */}
          <div className="w-full sm:w-40 m-0 p-0">
            <div className="flex items-center justify-between m-0 p-0">
              <div className="text-lg font-bold text-emerald-300 m-0 p-0">{trade.pair}</div>
              <span className="border border-zinc-700 text-zinc-300 bg-zinc-900/40 px-2 py-0.5 text-xs rounded m-0">{trade.lots} LOTS</span>
            </div>
            <div className="text-[11px] text-zinc-400 mt-0.5 flex items-center gap-1 m-0 p-0">
              ⏱ {durationSince(trade.startTime, now)}
            </div>
          </div>

          {/* Track */}
          <div className="relative flex-1 m-0 p-0">
            <div className={`relative h-12 bg-zinc-900 border border-emerald-700/50 ring-1 ${ageTint} rounded m-0 p-0`}>
              {/* SL gate */}
              <div className="absolute left-0 top-0 bottom-0 w-1 bg-red-600 rounded-l m-0 p-0"/>
              <div className="absolute left-2 top-1/2 -translate-y-1/2 text-[11px] text-red-400 m-0 p-0">SL {trade.stopLoss}</div>

              {/* Fill */}
              <div className={`absolute top-0 bottom-0 transition-all duration-300 rounded-l m-0 p-0 ${isPos ? "bg-emerald-600/60" : "bg-red-600/60"}`} style={{ width: pct(progress) }} />

              {/* Cursor (NOW) */}
              <div className="absolute top-0 bottom-0 w-1 bg-yellow-400 m-0 p-0" style={{ left: pct(progress) }} />
              <div className="absolute -translate-y-1/2 top-1/2 text-[11px] text-yellow-300 font-bold whitespace-nowrap m-0 p-0" style={{ left: `calc(${pct(progress)} + 6px)` }}>{trade.current}</div>

              {/* TP gate */}
              <div className="absolute right-0 top-0 bottom-0 w-1 bg-emerald-600 rounded-r m-0 p-0"/>
              <div className="absolute right-2 top-1/2 -translate-y-1/2 text-[11px] text-emerald-400 m-0 p-0">TP {trade.takeProfit}</div>
            </div>
            <div className="mt-1 text-[11px] text-zinc-400 m-0 p-0">ENTRY {trade.entry}</div>
          </div>

          {/* P/L tile */}
          <div className="w-full sm:w-44 text-right border-2 border-emerald-700/50 bg-black/60 p-3 rounded m-0">
            <div className="text-[11px] text-zinc-400 m-0 p-0">P/L</div>
            <div className={`text-2xl font-bold tabular-nums m-0 p-0 ${isPos ? "text-emerald-300" : "text-red-400"}`}>{fmtSigned(trade.equity)}</div>
            <div className="text-[11px] text-zinc-400 m-0 p-0">USD</div>
            {trade.history && trade.history.length > 1 && <div className="mt-1 text-emerald-400/70 m-0 p-0"><Sparkline data={trade.history} /></div>}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function InProgressPage() {
  const router = useRouter();
  const [now, setNow] = useState(new Date());
  const [trades, setTrades] = useState<Trade[]>([]);
  const [balance, setBalance] = useState(10000);
  const [level, setLevel] = useState("LOADING...");
  const [slots, setSlots] = useState(6);
  const [loading, setLoading] = useState(true);

  // Fetch real data from API
  useEffect(() => {
    async function fetchData() {
      try {
        // Fetch user profile for balance and tier
        const profileRes = await fetch('/api/user/profile');
        if (profileRes.ok) {
          const profileData = await profileRes.json();
          setBalance(profileData.balance || 10000);
          setLevel(profileData.tier || "NIBBLER");
          setSlots(profileData.max_slots || 6);
        }

        // Fetch open positions
        const positionsRes = await fetch('/api/positions/open');
        if (positionsRes.ok) {
          const positionsData = await positionsRes.json();

          // Transform API data to Trade format
          const openTrades: Trade[] = positionsData.positions?.map((pos: any) => ({
            id: pos.ticket || pos.position_id,
            pair: pos.symbol,
            entry: parseFloat(pos.open_price || pos.entry_price),
            current: parseFloat(pos.current_price || pos.entry_price),
            stopLoss: parseFloat(pos.sl || pos.stop_loss),
            takeProfit: parseFloat(pos.tp || pos.take_profit),
            equity: parseFloat(pos.profit || pos.pnl || 0),
            lots: parseFloat(pos.volume || pos.lot_size),
            startTime: new Date(pos.open_time || pos.created_at || Date.now()),
            history: pos.pnl_history || undefined
          })) || [];

          setTrades(openTrades);
        }
      } catch (err) {
        console.error('Failed to fetch positions:', err);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
    // Refresh every 5 seconds
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  // Clock update every second
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const totalPL = trades.reduce((s, t) => s + t.equity, 0);
  const equity = balance + totalPL;
  const dd = (equity - balance) / balance;

  return (
    <div className="min-h-screen bg-zinc-950 text-emerald-300 font-mono m-0 p-0">
      {/* Header */}
      <div className="border-b border-emerald-800/50 bg-gradient-to-b from-zinc-900 to-black m-0 p-0">
        <div className="mx-auto max-w-7xl p-3 sm:p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 m-0">
          <div className="m-0 p-0">
            <div className="text-2xl sm:text-3xl font-extrabold tracking-[0.15em] m-0 p-0" style={{ color: "#8b7355" }}>⬢ B.I.T.T.E.N</div>
            <div className="text-emerald-400/70 text-xs sm:text-sm m-0 p-0">LIVE POSITION MONITOR</div>
          </div>
          <div className="flex items-center gap-4 text-zinc-400 flex-wrap m-0 p-0">
            <Beacon label="OPERATIONAL" />
            <Beacon label="SECURE" />
            <Beacon label="LAT" value="12ms" />
            <time className="tabular-nums text-zinc-200 m-0 p-0">{now.toLocaleTimeString(undefined, { hour12: false })}</time>
            <span className="text-zinc-400 m-0 p-0">{now.toLocaleDateString(undefined, { month: "short", day: "numeric" })}</span>
            <span className="border border-yellow-600/60 text-yellow-300 bg-yellow-900/20 px-2 py-1 text-xs rounded m-0">LEVEL: {level}</span>
          </div>
        </div>
        <div className="h-1 bg-emerald-500 m-0 p-0"></div>
      </div>

      {/* Account Telemetry */}
      <div className="mx-auto max-w-7xl p-3 sm:p-4 m-0">
        <div className="bg-black/60 border border-emerald-700/50 rounded-lg m-0 p-0">
          <div className="p-3 sm:p-4 m-0">
            <div className="grid sm:grid-cols-3 gap-3 m-0 p-0">
              <div className="m-0 p-0">
                <div className="flex items-center justify-between m-0 p-0">
                  <span className="text-sm m-0 p-0">BALANCE</span>
                  <span className="text-2xl font-bold tabular-nums m-0 p-0">{fmtUSD(balance)}</span>
                </div>
                <div className="mt-2 text-[11px] text-zinc-400 m-0 p-0">Base capital</div>
              </div>
              <div className="m-0 p-0">
                <div className="flex items-center justify-between m-0 p-0">
                  <span className="text-sm m-0 p-0">EQUITY</span>
                  <span className={`text-2xl font-bold tabular-nums m-0 p-0 ${totalPL >= 0 ? "text-emerald-300" : "text-red-400"}`}>{fmtUSD(equity)}</span>
                </div>
                <div className="mt-2 m-0 p-0">
                  <div className="text-[11px] text-zinc-400 mb-1 m-0 p-0">Live Δ from balance</div>
                  <div className="h-2 bg-zinc-800 rounded-full overflow-hidden m-0 p-0">
                    <div className={`${dd >= 0 ? "bg-emerald-500" : "bg-red-500"} h-2 transition-all m-0 p-0`} style={{ width: `${Math.min(100, Math.abs(dd) * 100)}%` }} />
                  </div>
                </div>
              </div>
              <div className="m-0 p-0">
                <div className="flex items-center justify-between m-0 p-0">
                  <span className="text-sm m-0 p-0">OPEN POSITIONS</span>
                  <span className="text-2xl font-bold tabular-nums m-0 p-0">{trades.length}/{slots}</span>
                </div>
                <div className="mt-2 text-[11px] text-zinc-400 m-0 p-0">Capacity remaining: {Math.max(0, slots - trades.length)}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Trades */}
      <div className="mx-auto max-w-7xl p-3 sm:p-4 space-y-3 m-0">
        {loading ? (
          <div className="bg-black/30 border border-zinc-800 rounded-lg m-0 p-0">
            <div className="p-3 sm:p-4 text-center text-zinc-400 m-0">Loading positions...</div>
          </div>
        ) : trades.length === 0 ? (
          <div className="bg-black/30 border border-zinc-800 rounded-lg m-0 p-0">
            <div className="p-3 sm:p-4 text-center text-zinc-400 m-0">
              <div className="text-lg mb-2 m-0 p-0">No open positions</div>
              <div className="text-sm m-0 p-0">All {slots} slots available</div>
            </div>
          </div>
        ) : (
          <>
            {trades.map(t => <TradeLane key={t.id} trade={t} now={now} />)}

            {/* Empty slots */}
            {Array.from({ length: Math.max(0, slots - trades.length) }).map((_, idx) => (
              <div key={`empty-${idx}`} className="bg-black/30 border border-zinc-800 rounded-lg m-0 p-0">
                <div className="p-3 sm:p-4 m-0">
                  <div className="flex items-center gap-3 sm:gap-4 h-10 m-0 p-0">
                    <div className="w-20 sm:w-32 text-zinc-600 text-xs sm:text-sm m-0 p-0">SLOT {trades.length + idx + 1}</div>
                    <div className="flex-1 bg-zinc-900/60 h-full grid place-items-center text-zinc-600 text-xs sm:text-sm rounded m-0 p-0">[ AVAILABLE ]</div>
                    <div className="w-16 sm:w-40 text-right text-zinc-600 text-xs sm:text-sm m-0 p-0">—</div>
                  </div>
                </div>
              </div>
            ))}
          </>
        )}
      </div>

      {/* Control Panel */}
      <div className="mx-auto max-w-7xl p-3 sm:p-4 m-0">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-4 m-0 p-0">
          <button
            onClick={() => router.push('/alerts')}
            className="bg-transparent appearance-none border border-emerald-600 text-emerald-300 hover:bg-emerald-900/30 px-4 py-3 rounded font-bold transition-colors m-0 cursor-pointer"
          >
            🔔 ALERTS <span className="ml-1 text-[10px] opacity-70">(A)</span>
          </button>
          <button
            onClick={() => router.push('/war-room')}
            className="bg-transparent appearance-none border border-yellow-600 text-yellow-300 hover:bg-yellow-900/20 px-4 py-3 rounded font-bold transition-colors m-0 cursor-pointer"
          >
            📡 WAR ROOM <span className="ml-1 text-[10px] opacity-70">(W)</span>
          </button>
          <button
            onClick={() => router.push('/stats')}
            className="bg-transparent appearance-none border border-blue-600 text-blue-300 hover:bg-blue-900/20 px-4 py-3 rounded font-bold transition-colors m-0 cursor-pointer"
          >
            📊 STATS <span className="ml-1 text-[10px] opacity-70">(S)</span>
          </button>
          <button
            onClick={() => router.push('/close-all')}
            className="bg-transparent appearance-none border border-red-600 text-red-300 hover:bg-red-900/20 px-4 py-3 rounded font-bold transition-colors m-0 cursor-pointer"
          >
            🛡 CLOSE <span className="ml-1 text-[10px] opacity-70">(X)</span>
          </button>
        </div>
        <button
          onClick={() => router.push('/notebook')}
          className="bg-transparent appearance-none mt-2 w-full border border-purple-600 text-purple-300 hover:bg-purple-900/20 px-4 py-3 rounded font-bold transition-colors m-0 cursor-pointer"
        >
          📓 NORMAN'S NOTEBOOK <span className="ml-1 text-[10px] opacity-70">(N)</span>
        </button>
      </div>

      {/* Footer Status Bar */}
      <div className="mx-auto max-w-7xl p-3 sm:p-4 pt-0 m-0">
        <div className="bg-black/60 border border-emerald-700/50 rounded-lg m-0 p-0">
          <div className="p-2 text-center text-[12px] text-emerald-400 m-0">
            <span className="hidden sm:inline m-0 p-0">SYSTEM STATUS: </span>
            <span className="inline-flex items-center gap-4 flex-wrap justify-center m-0 p-0">
              <span className="inline-flex items-center gap-1 m-0 p-0"><div className="h-2.5 w-2.5 rounded-full bg-emerald-400 m-0 p-0"/> OPERATIONAL</span>
              <span className="inline-flex items-center gap-1 m-0 p-0">🔒 SECURE</span>
              <span className="inline-flex items-center gap-1 m-0 p-0">📶 12ms</span>
              <span className="inline-flex items-center gap-1 m-0 p-0">💻 HYDRA NODE OK</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
