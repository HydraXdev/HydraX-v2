"use client"

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { MilitaryHeader } from '@/components/bitten/MilitaryHeader';

interface KPI {
  label: string;
  value: string;
  sub?: string;
}

interface RecentOp {
  id: number;
  when: string;
  title: string;
  delta: number;
  tag: string;
}

interface PairDist {
  name: string;
  value: number;
}

export default function StatsPage() {
  const router = useRouter();

  // Real data from API
  const [balance, setBalance] = useState(10000.00);
  const [equity, setEquity] = useState(10000.00);
  const [kpis, setKpis] = useState<KPI[]>([]);
  const [recentOps, setRecentOps] = useState<RecentOp[]>([]);
  const [pairDist, setPairDist] = useState<PairDist[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        // Fetch user profile
        const profileRes = await fetch('/api/user/profile');
        if (profileRes.ok) {
          const profileData = await profileRes.json();
          setBalance(profileData.balance || 10000);
          setEquity(profileData.equity || profileData.balance || 10000);
        }

        // Fetch stats
        const statsRes = await fetch('/api/user/stats');
        if (statsRes.ok) {
          const statsData = await statsRes.json();

          // Build KPIs from real data
          const realKpis: KPI[] = [
            { label: 'WIN RATE', value: `${Math.round(statsData.win_rate || 0)}%`, sub: 'Last 90 days' },
            { label: 'AVG R:R', value: (statsData.avg_rr || 0).toFixed(2), sub: 'Risk/Reward' },
            { label: 'PROFIT FACTOR', value: (statsData.profit_factor || 0).toFixed(2), sub: 'Net profit' },
            { label: 'BEST TRADE', value: `$${(statsData.best_trade || 0).toFixed(2)}`, sub: statsData.best_trade_symbol || 'N/A' },
            { label: 'LONGEST STREAK', value: `${statsData.longest_streak || 0} wins`, sub: 'Best run' },
            { label: 'AVG HOLD', value: statsData.avg_hold_time || '0h 0m', sub: 'Position time' },
          ];
          setKpis(realKpis);

          // Recent operations
          if (statsData.recent_trades) {
            setRecentOps(statsData.recent_trades.map((trade: any, idx: number) => ({
              id: idx + 1,
              when: trade.time_ago || 'N/A',
              title: `${trade.symbol || 'N/A'} — ${trade.pattern || 'Trade'}`,
              delta: trade.pnl || 0,
              tag: trade.outcome || 'PENDING'
            })));
          }

          // Pair distribution
          if (statsData.pair_distribution) {
            setPairDist(statsData.pair_distribution.map((pair: any) => ({
              name: pair.symbol,
              value: pair.count
            })));
          }
        }
      } catch (err) {
        console.error('Failed to fetch stats:', err);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  const totalPnL = equity - balance;
  const growthPct = balance > 0 ? ((totalPnL / balance) * 100) : 0;

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 text-green-400 p-2 sm:p-4 font-mono m-0">
        <MilitaryHeader title="BITTEN" subtitle="MISSION ANALYTICS" />
        <div className="text-center mt-10 m-0 p-0">Loading stats...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-green-400 p-2 sm:p-4 font-mono m-0">
      <MilitaryHeader title="BITTEN" subtitle="MISSION ANALYTICS" />

      {/* Account Growth */}
      <div className="border-2 border-green-500 bg-black/50 p-2 sm:p-3 mb-3 m-0">
        <div className="text-xs sm:text-sm font-bold text-green-400 mb-2 m-0 p-0">TOTAL ACCOUNT GROWTH</div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 sm:gap-3 mb-2 m-0 p-0">
          <div className="m-0 p-0">
            <div className="text-xs text-green-600 m-0 p-0">BALANCE</div>
            <div className="text-base sm:text-lg font-bold text-green-400 m-0 p-0">${balance.toFixed(2)}</div>
          </div>
          <div className="m-0 p-0">
            <div className="text-xs text-green-600 m-0 p-0">EQUITY</div>
            <div className="text-base sm:text-lg font-bold text-green-400 m-0 p-0">${equity.toFixed(2)}</div>
          </div>
          <div className="m-0 p-0">
            <div className="text-xs text-green-600 m-0 p-0">GROWTH</div>
            <div className={`text-base sm:text-lg font-bold m-0 p-0 ${totalPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {totalPnL >= 0 ? '+' : ''}{growthPct.toFixed(2)}%
            </div>
          </div>
        </div>
      </div>

      {/* Key Performance */}
      <div className="border-2 border-yellow-500 bg-black/70 p-2 sm:p-3 mb-3 m-0">
        <div className="text-xs sm:text-sm font-bold text-yellow-400 mb-2 m-0 p-0">KEY PERFORMANCE</div>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 m-0 p-0">
          {kpis.map((k) => (
            <div key={k.label} className="border border-green-700 bg-black/50 p-2 m-0">
              <div className="text-xs text-green-600 m-0 p-0">{k.label}</div>
              <div className="text-lg sm:text-xl font-bold text-green-400 m-0 p-0">{k.value}</div>
              {k.sub && <div className="text-xs text-gray-500 m-0 p-0">{k.sub}</div>}
            </div>
          ))}
        </div>
      </div>

      {/* Recent Operations */}
      <div className="border-2 border-blue-500 bg-black/70 p-2 sm:p-3 mb-3 m-0">
        <div className="text-xs sm:text-sm font-bold text-blue-400 mb-2 m-0 p-0">RECENT OPERATIONS</div>
        <div className="space-y-2 m-0 p-0">
          {recentOps.length === 0 ? (
            <div className="text-center text-gray-500 text-sm m-0 p-2">No recent operations</div>
          ) : (
            recentOps.map(op => (
              <div key={op.id} className="border border-green-700 bg-black/50 p-2 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-1 sm:gap-0 m-0">
                <div className="m-0 p-0">
                  <div className="text-xs sm:text-sm text-green-400 m-0 p-0">{op.title}</div>
                  <div className="text-xs text-green-600 m-0 p-0">{op.when} • {op.tag}</div>
                </div>
                <div className={`text-sm font-bold m-0 p-0 ${op.delta >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {op.delta >= 0 ? '+' : ''}${Math.abs(op.delta).toFixed(2)}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Distribution */}
      <div className="border-2 border-purple-500 bg-black/70 p-2 sm:p-3 mb-3 m-0">
        <div className="text-xs sm:text-sm font-bold text-purple-400 mb-2 m-0 p-0">DISTRIBUTION BY PAIR</div>
        <div className="space-y-1 m-0 p-0">
          {pairDist.length === 0 ? (
            <div className="text-center text-gray-500 text-sm m-0 p-2">No trade data available</div>
          ) : (
            pairDist.map(pair => (
              <div key={pair.name} className="flex justify-between items-center m-0 p-0">
                <div className="text-xs sm:text-sm text-green-400 m-0 p-0">{pair.name}</div>
                <div className="flex items-center gap-2 m-0 p-0">
                  <div className="h-2 bg-green-500 m-0 p-0" style={{ width: `${Math.min(pair.value * 10, 100)}px` }}></div>
                  <div className="text-xs sm:text-sm text-green-400 m-0 p-0">{pair.value}</div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 m-0 p-0">
        <button
          onClick={() => router.push('/war-room')}
          className="bg-transparent appearance-none border-2 border-yellow-500 bg-yellow-900/30 p-3 hover:bg-yellow-900/50 transition-colors text-yellow-400 font-bold m-0 cursor-pointer"
        >
          🏛️ WAR ROOM
        </button>
        <button
          onClick={() => router.push('/notebook')}
          className="bg-transparent appearance-none border-2 border-purple-500 bg-purple-900/30 p-3 hover:bg-purple-900/50 transition-colors text-purple-400 font-bold m-0 cursor-pointer"
        >
          📓 NOTEBOOK
        </button>
      </div>
    </div>
  );
}
