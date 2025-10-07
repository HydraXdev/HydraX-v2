"use client";

import React, { useEffect, useState } from "react";

interface TacticalBriefProps {
  userData: {
    balance: number;
    activeTrades: number;
    maxTrades: number;
    riskPerTrade: number;
    potentialReward: number;
  };
  alertData: {
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
    pips: { tp: number; sl: number };
    riskReward: number;
  };
  onExecute?: () => void;
  executing?: boolean;
}

const fmtUSD = (n: number) =>
  n.toLocaleString(undefined, { style: "currency", currency: "USD" });
const fmtNum = (n: number, d: number = 5) => n.toFixed(d);

function AmmoBar({ max, active }: { max: number; active: number }) {
  const remaining = Math.max(0, max - active);
  return (
    <div className="space-y-1">
      <div className="m-0 p-0 text-xs text-yellow-400 tracking-wide font-mono">
        REMAINING AMMO
      </div>
      <div className="flex gap-1 m-0 p-0">
        {Array.from({ length: max }).map((_, i) => {
          const available = i < remaining;
          return (
            <div key={i} className="m-0 p-0">
              {available ? (
                <svg
                  width="18"
                  height="28"
                  viewBox="0 0 20 32"
                  className="drop-shadow block"
                >
                  <ellipse
                    cx="10"
                    cy="8"
                    rx="6"
                    ry="8"
                    fill="#fbbf24"
                    stroke="#f59e0b"
                    strokeWidth="1"
                  />
                  <rect
                    x="4"
                    y="8"
                    width="12"
                    height="20"
                    fill="#fbbf24"
                    stroke="#f59e0b"
                    strokeWidth="1"
                  />
                  <rect x="4" y="28" width="12" height="3" fill="#92400e" />
                </svg>
              ) : (
                <svg
                  width="18"
                  height="28"
                  viewBox="0 0 20 32"
                  className="opacity-30 block"
                >
                  <ellipse
                    cx="10"
                    cy="8"
                    rx="6"
                    ry="8"
                    fill="none"
                    stroke="#78716c"
                    strokeWidth="1"
                  />
                  <rect
                    x="4"
                    y="8"
                    width="12"
                    height="20"
                    fill="none"
                    stroke="#78716c"
                    strokeWidth="1"
                  />
                  <rect
                    x="4"
                    y="28"
                    width="12"
                    height="3"
                    fill="#1c1917"
                    stroke="#78716c"
                    strokeWidth="1"
                  />
                </svg>
              )}
            </div>
          );
        })}
      </div>
      <div className="m-0 p-0 text-[11px] text-green-400 font-mono">
        {remaining}/{max} SHOTS AVAILABLE
      </div>
    </div>
  );
}

function KV({ k, v, accent }: { k: string; v: string; accent?: string }) {
  return (
    <div className="flex items-center justify-between py-1 m-0 text-sm">
      <span className="text-zinc-400 font-mono m-0 p-0">{k}</span>
      <span className={`font-mono m-0 p-0 ${accent || "text-zinc-200"}`}>
        {v}
      </span>
    </div>
  );
}

export function TacticalBrief({
  userData,
  alertData,
  onExecute,
  executing = false,
}: TacticalBriefProps) {
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [ackRisk, setAckRisk] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const [now, setNow] = useState(new Date());

  const bulletsRemaining = Math.max(
    0,
    userData.maxTrades - userData.activeTrades,
  );

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const ts = new Date(alertData.timestamp);
  const ageSec = Math.max(0, Math.floor((+now - +ts) / 1000));
  const agePct = Math.min(100, (ageSec / 300) * 100);

  async function handleExecuteConfirmed() {
    if (onExecute) {
      onExecute();
      setConfirmOpen(false);
      setAckRisk(false);
    }
  }

  return (
    <div
      className="min-h-screen bg-zinc-950 text-green-300 font-mono antialiased isolate m-0 p-0"
      style={{ fontFeatureSettings: "'tnum'" }}
    >
      {/* Header */}
      <div className="border-b border-zinc-800 bg-gradient-to-b from-zinc-900 to-black m-0">
        <div className="mx-auto max-w-6xl p-2 sm:p-3 md:p-4 flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2 sm:gap-3 m-0">
            <div className="w-8 h-8 sm:w-10 sm:h-10 md:w-12 md:h-12 rounded-full bg-zinc-800 border-2 border-zinc-700 grid place-items-center m-0 p-0 flex-shrink-0">
              <div className="w-5 h-5 sm:w-6 sm:h-6 md:w-7 md:h-7 rounded-full border-2 border-zinc-600/70 m-0 p-0" />
            </div>
            <div
              className="text-xl sm:text-2xl md:text-3xl lg:text-4xl font-extrabold tracking-[0.10em] sm:tracking-[0.15em] m-0 p-0"
              style={{
                color: "#8b7355",
                textShadow: "2px 2px 4px rgba(0,0,0,0.8)",
              }}
            >
              BITTEN
            </div>
            <span className="hidden sm:inline-block border border-emerald-700/60 text-emerald-300 bg-emerald-900/20 px-2 py-1 text-xs rounded m-0">
              MISSION BRIEF
            </span>
          </div>
          <div className="flex items-center gap-2 sm:gap-3 text-zinc-500 text-xs sm:text-sm m-0">
            <span className="border border-zinc-700 bg-black/40 text-zinc-300 px-2 py-1 rounded text-[10px] sm:text-xs m-0">
              {alertData.session}
            </span>
            <time className="tabular-nums text-[10px] sm:text-xs m-0 p-0">
              {now.toLocaleTimeString()}
            </time>
          </div>
        </div>
        {/* Freshness bar */}
        <div className="h-1 bg-zinc-900 m-0 p-0 overflow-hidden">
          <div
            className="h-full bg-emerald-500 transition-all m-0 p-0"
            style={{ width: `${100 - agePct}%` }}
          ></div>
        </div>
      </div>

      <div className="mx-auto max-w-6xl p-2 sm:p-3 md:p-4 grid grid-cols-1 lg:grid-cols-[1.15fr,0.85fr] gap-3 sm:gap-4">
        {/* Left: Tactical Map */}
        <div className="bg-black/60 border border-green-700/50 rounded-lg m-0 p-0">
          <div className="p-2 sm:p-3 md:p-4 border-b border-zinc-800 m-0">
            <div className="flex items-start sm:items-center justify-between gap-2 mb-2 m-0 flex-wrap sm:flex-nowrap">
              <div className="m-0 p-0 flex-1 min-w-0">
                <div className="text-emerald-300 text-base sm:text-lg md:text-xl lg:text-2xl tracking-wide font-bold m-0 p-0 truncate">
                  {alertData.pattern}
                </div>
                <div className="text-[10px] sm:text-xs text-emerald-400/70 m-0 p-0">
                  {alertData.pair} · {alertData.timeframe}
                </div>
              </div>
              <div className="text-right m-0 p-0 flex-shrink-0">
                <div className="text-yellow-300 text-base sm:text-lg md:text-xl font-bold tabular-nums m-0 p-0">
                  {alertData.confidence.toFixed(1)}%
                </div>
                <span className="mt-1 border border-yellow-600 bg-yellow-900/40 text-yellow-300 px-1.5 sm:px-2 py-0.5 sm:py-1 text-[10px] sm:text-xs rounded inline-block">
                  R:R {alertData.riskReward.toFixed(2)}
                </span>
              </div>
            </div>
          </div>

          <div className="p-2 sm:p-3 md:p-4 m-0">
            {/* Chart */}
            <div className="relative h-64 sm:h-80 md:h-96 bg-gradient-to-b from-zinc-900 to-black border border-green-700/60 rounded m-0 p-0">
              <div className="absolute left-0 top-0 bottom-8 w-16 bg-black/60 border-r border-green-700/60 flex flex-col justify-around py-3 text-sm font-bold text-green-400 m-0">
                {[
                  "1.0550",
                  "1.0540",
                  "1.0530",
                  "1.0520",
                  "1.0510",
                  "1.0500",
                ].map((p) => (
                  <div key={p} className="text-right pr-2 m-0 p-0">
                    {p}
                  </div>
                ))}
              </div>

              <div className="absolute left-16 right-0 top-0 bottom-8 m-0 p-0">
                <svg
                  className="w-full h-full block"
                  viewBox="0 0 100 100"
                  preserveAspectRatio="none"
                >
                  <line
                    x1="0"
                    y1="15"
                    x2="100"
                    y2="15"
                    stroke="#10b981"
                    strokeWidth="0.8"
                    strokeDasharray="2,2"
                  />
                  <rect
                    x="75"
                    y="10"
                    width="24"
                    height="8"
                    fill="#10b981"
                    opacity="0.9"
                  />
                  <text
                    x="77"
                    y="16"
                    fill="#000"
                    fontSize="5"
                    fontWeight="bold"
                  >
                    TP {fmtNum(alertData.takeProfit, 5)}
                  </text>

                  <line
                    x1="0"
                    y1="50"
                    x2="100"
                    y2="50"
                    stroke="#3b82f6"
                    strokeWidth="0.6"
                    strokeDasharray="2,1"
                  />
                  <rect
                    x="70"
                    y="47"
                    width="29"
                    height="6"
                    fill="#3b82f6"
                    opacity="0.9"
                  />
                  <text
                    x="72"
                    y="51.5"
                    fill="#000"
                    fontSize="4"
                    fontWeight="bold"
                  >
                    ENTRY {fmtNum(alertData.entry, 5)}
                  </text>

                  <line
                    x1="0"
                    y1="78"
                    x2="100"
                    y2="78"
                    stroke="#ef4444"
                    strokeWidth="0.8"
                    strokeDasharray="2,2"
                  />
                  <rect
                    x="75"
                    y="75"
                    width="24"
                    height="6"
                    fill="#ef4444"
                    opacity="0.9"
                  />
                  <text
                    x="77"
                    y="79.5"
                    fill="#000"
                    fontSize="5"
                    fontWeight="bold"
                  >
                    SL {fmtNum(alertData.stopLoss, 5)}
                  </text>

                  <rect
                    x="15"
                    y="52"
                    width="18"
                    height="12"
                    fill="#fbbf24"
                    opacity="0.3"
                    stroke="#fbbf24"
                    strokeWidth="0.5"
                  />
                  <text
                    x="16.5"
                    y="57"
                    fill="#fbbf24"
                    fontSize="4"
                    fontWeight="bold"
                  >
                    ORDER
                  </text>
                  <text
                    x="16.5"
                    y="61"
                    fill="#fbbf24"
                    fontSize="4"
                    fontWeight="bold"
                  >
                    BLOCK
                  </text>

                  <rect
                    x="50"
                    y="82"
                    width="12"
                    height="10"
                    fill="#ef4444"
                    opacity="0.3"
                    stroke="#ef4444"
                    strokeWidth="0.5"
                  />
                  <text
                    x="51"
                    y="86"
                    fill="#ef4444"
                    fontSize="3.5"
                    fontWeight="bold"
                  >
                    SWEEP
                  </text>

                  <path
                    d="M 5,30 L 15,40 L 25,48 L 32,56 L 38,54 L 45,52 L 52,70 L 58,85"
                    stroke="#ffffff"
                    strokeWidth="1.5"
                    fill="none"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />

                  <circle
                    cx="58"
                    cy="85"
                    r="3"
                    fill="#fbbf24"
                    stroke="#f59e0b"
                    strokeWidth="0.8"
                  >
                    <animate
                      attributeName="r"
                      values="3;4.5;3"
                      dur="1.5s"
                      repeatCount="indefinite"
                    />
                  </circle>
                  <text
                    x="50"
                    y="95"
                    fill="#fbbf24"
                    fontSize="6"
                    fontWeight="bold"
                  >
                    YOU ARE HERE
                  </text>

                  <path
                    d="M 58,85 L 65,70 L 72,50 L 80,30 L 88,18"
                    stroke="#06b6d4"
                    strokeWidth="2"
                    fill="none"
                    strokeLinecap="round"
                    strokeDasharray="4,2"
                  />
                  <polygon points="88,18 86,22 90,22" fill="#06b6d4" />

                  <text
                    x="6"
                    y="70"
                    fill="#fbbf24"
                    fontSize="3.5"
                    fontWeight="bold"
                  >
                    ① Bounce at support
                  </text>
                  <text
                    x="40"
                    y="94"
                    fill="#ef4444"
                    fontSize="3.5"
                    fontWeight="bold"
                  >
                    ② Liquidity sweep
                  </text>
                  <text
                    x="72"
                    y="42"
                    fill="#06b6d4"
                    fontSize="4"
                    fontWeight="bold"
                  >
                    ③ Rally to TP
                  </text>
                </svg>
              </div>

              <div className="absolute left-16 right-0 bottom-0 h-8 bg-black/70 border-t border-green-700/60 flex items-center justify-around text-sm font-bold rounded-b m-0">
                <span className="text-zinc-500 m-0 p-0">13:15</span>
                <span className="text-zinc-500 m-0 p-0">13:30</span>
                <span className="text-yellow-300 text-base m-0 p-0">⬤ NOW</span>
                <span className="text-cyan-300 m-0 p-0">→ Future</span>
              </div>

              <div className="absolute top-2 right-2 bg-black/80 border border-green-700/60 p-2 text-xs space-y-1.5 rounded m-0">
                <div className="flex items-center gap-2 m-0 p-0">
                  <div className="w-6 h-1 bg-white m-0 p-0" />
                  <span className="text-white font-bold m-0 p-0">Past</span>
                </div>
                <div className="flex items-center gap-2 m-0 p-0">
                  <div className="w-4 h-4 rounded-full bg-yellow-400 m-0 p-0" />
                  <span className="text-yellow-300 font-bold m-0 p-0">Now</span>
                </div>
                <div className="flex items-center gap-2 m-0 p-0">
                  <div className="w-6 h-1 bg-cyan-400 opacity-70 m-0 p-0" />
                  <span className="text-cyan-300 font-bold m-0 p-0">
                    Expected
                  </span>
                </div>
              </div>
            </div>

            <div className="mt-3 grid sm:grid-cols-3 gap-2 text-sm">
              <div className="flex items-start gap-2 text-emerald-300 m-0 p-0">
                ✓ Swept liquidity under structure
              </div>
              <div className="flex items-start gap-2 text-emerald-300 m-0 p-0">
                ✓ Strong reversal print
              </div>
              <div className="flex items-start gap-2 text-emerald-300 m-0 p-0">
                ✓ Confidence {alertData.confidence}%
              </div>
            </div>
          </div>
        </div>

        {/* Right: Dossier */}
        <div className="space-y-4 m-0 p-0">
          <div className="bg-zinc-950/60 border border-yellow-600/50 rounded-lg m-0 p-0">
            <div className="p-4 border-b border-zinc-800 m-0">
              <div className="flex items-center gap-2 text-yellow-300 font-bold m-0 p-0">
                🎯 Operation Dossier
              </div>
            </div>
            <div className="p-4 m-0">
              <KV
                k="PAIR / TF"
                v={`${alertData.pair} · ${alertData.timeframe}`}
              />
              <KV
                k="ENTRY"
                v={fmtNum(alertData.entry, 5)}
                accent="text-blue-300"
              />
              <KV
                k="TP / SL (pips)"
                v={`${fmtNum(alertData.takeProfit, 5)} / ${fmtNum(alertData.stopLoss, 5)} (${alertData.pips.tp} / ${alertData.pips.sl})`}
              />
              <KV
                k="RISK → REWARD"
                v={`${fmtUSD(userData.riskPerTrade)} → ${fmtUSD(userData.potentialReward)} (R:R ${alertData.riskReward})`}
                accent="text-emerald-300"
              />
              <div className="mt-3 pt-3 border-t border-zinc-800 m-0">
                <AmmoBar
                  max={userData.maxTrades}
                  active={userData.activeTrades}
                />
              </div>
            </div>
          </div>

          <div className="bg-zinc-950/60 border border-emerald-700/50 rounded-lg m-0 p-0">
            <div className="p-4 border-b border-zinc-800 m-0">
              <div className="flex items-center gap-2 text-emerald-300 font-bold m-0 p-0">
                ⚡ Actions
              </div>
            </div>
            <div className="p-4 space-y-2 m-0">
              <button
                className="w-full bg-transparent appearance-none border border-emerald-600 text-emerald-300 hover:bg-emerald-900/30 px-4 py-3 rounded font-bold transition-colors disabled:opacity-50 m-0 cursor-pointer"
                onClick={() => setConfirmOpen(true)}
                disabled={executing}
              >
                ▶ {executing ? "EXECUTING…" : "EXECUTE TRADE"}{" "}
                <span className="ml-2 text-xs opacity-70">(E)</span>
              </button>
              <div className="grid grid-cols-2 gap-2 m-0">
                <button className="bg-transparent appearance-none border border-blue-600 text-blue-300 hover:bg-blue-900/20 px-3 py-2 rounded text-sm transition-colors m-0 cursor-pointer">
                  📊 STATUS <span className="text-[10px] opacity-70">(D)</span>
                </button>
                <button className="bg-transparent appearance-none border border-purple-600 text-purple-300 hover:bg-purple-900/20 px-3 py-2 rounded text-sm transition-colors m-0 cursor-pointer">
                  📓 NOTEBOOK{" "}
                  <span className="text-[10px] opacity-70">(N)</span>
                </button>
              </div>
              <button
                className="w-full bg-transparent appearance-none border border-zinc-700 text-zinc-300 hover:bg-zinc-900/50 px-3 py-2 rounded text-sm transition-colors m-0 cursor-pointer"
                onClick={() => setHelpOpen(true)}
              >
                ⓘ KEYBINDS & HELP{" "}
                <span className="text-[10px] opacity-70">(?)</span>
              </button>
            </div>
          </div>

          <div className="bg-zinc-950/60 border border-zinc-700/60 rounded-lg m-0 p-0">
            <div className="p-4 border-b border-zinc-800 m-0">
              <div className="text-zinc-300 font-bold m-0 p-0">
                Your Profile
              </div>
            </div>
            <div className="p-4 m-0">
              <KV k="Balance" v={fmtUSD(userData.balance)} />
              <KV k="Risk / Trade" v={fmtUSD(userData.riskPerTrade)} />
              <KV k="Potential Reward" v={fmtUSD(userData.potentialReward)} />
            </div>
          </div>
        </div>
      </div>

      {/* Confirm Dialog */}
      {confirmOpen && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50 m-0">
          <div className="bg-zinc-950 border border-emerald-700/60 text-emerald-200 rounded-lg max-w-md w-full p-6 m-0">
            <div className="flex items-center gap-2 text-lg font-bold mb-4 m-0">
              <span className="text-yellow-300 m-0 p-0">🛡</span> Confirm
              Execution
            </div>
            <div className="space-y-2 text-sm mb-4 m-0">
              <p className="m-0">
                Deploy order for{" "}
                <span className="font-bold">{alertData.pair}</span> at{" "}
                <span className="font-bold">{fmtNum(alertData.entry, 5)}</span>.
              </p>
              <p className="m-0">
                Risk{" "}
                <span className="text-red-300 font-bold">
                  {fmtUSD(userData.riskPerTrade)}
                </span>{" "}
                to target{" "}
                <span className="text-emerald-300 font-bold">
                  {fmtUSD(userData.potentialReward)}
                </span>{" "}
                (R:R {alertData.riskReward}).
              </p>
              <p className="m-0">
                Shots remaining after deploy:{" "}
                <span className="font-bold">{bulletsRemaining - 1}</span>.
              </p>
              <label className="flex items-center gap-2 mt-3 select-none cursor-pointer m-0">
                <input
                  type="checkbox"
                  className="w-4 h-4 appearance-none bg-transparent border border-zinc-500 checked:bg-emerald-600 rounded m-0 cursor-pointer"
                  checked={ackRisk}
                  onChange={(e) => setAckRisk(e.target.checked)}
                />
                <span className="m-0 p-0">
                  I acknowledge the risk and confirm this operation.
                </span>
              </label>
            </div>
            <div className="flex gap-2 m-0">
              <button
                className="flex-1 bg-transparent appearance-none border border-zinc-700 text-zinc-400 px-4 py-2 rounded hover:bg-zinc-900/50 transition-colors m-0 cursor-pointer"
                onClick={() => setConfirmOpen(false)}
              >
                ✕ Cancel
              </button>
              <button
                disabled={!ackRisk || executing}
                className="flex-1 bg-transparent appearance-none border border-emerald-600 bg-emerald-900/30 hover:bg-emerald-900/50 px-4 py-2 rounded font-bold disabled:opacity-50 transition-colors m-0 cursor-pointer"
                onClick={handleExecuteConfirmed}
              >
                ▶ {executing ? "Executing…" : "Confirm & Execute"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Help Dialog */}
      {helpOpen && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50 m-0">
          <div className="bg-zinc-950 border border-zinc-700 text-zinc-200 rounded-lg max-w-md w-full p-6 m-0">
            <div className="text-lg font-bold mb-4 m-0 p-0">Keybinds</div>
            <ul className="space-y-2 text-sm list-none m-0 p-0">
              <li className="m-0 p-0">
                <kbd className="px-2 py-1 bg-zinc-800 rounded text-xs">E</kbd> —
                Execute (opens confirmation)
              </li>
              <li className="m-0 p-0">
                <kbd className="px-2 py-1 bg-zinc-800 rounded text-xs">D</kbd> —
                Status Board
              </li>
              <li className="m-0 p-0">
                <kbd className="px-2 py-1 bg-zinc-800 rounded text-xs">N</kbd> —
                Notebook
              </li>
              <li className="m-0 p-0">
                <kbd className="px-2 py-1 bg-zinc-800 rounded text-xs">?</kbd> —
                Toggle this help
              </li>
            </ul>
            <button
              className="mt-4 w-full bg-transparent appearance-none border border-zinc-700 px-4 py-2 rounded hover:bg-zinc-900/50 transition-colors m-0 cursor-pointer"
              onClick={() => setHelpOpen(false)}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
