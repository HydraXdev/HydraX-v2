"use client"

import dynamic from 'next/dynamic';

// Dynamically import to avoid SSR issues - this component fetches real live data
const StatusBoardLive = dynamic(() => import('@/components/bitten/StatusBoardLive'), {
  ssr: false,
  loading: () => (
    <div className="min-h-screen bg-zinc-950 text-emerald-300 font-mono flex items-center justify-center">
      <div className="text-2xl font-bold">Loading...</div>
    </div>
  )
});

/**
 * Status Board Page
 *
 * Real-time trading dashboard with live data from backend
 * - Account balance & equity
 * - Open positions with real-time P&L
 * - Position progress bars
 * - Auto-refreshing every 3 seconds
 */
export default function StatusPage() {
  return <StatusBoardLive />;
}
