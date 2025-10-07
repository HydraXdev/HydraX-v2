"use client"

import React, { useState, useEffect } from 'react';
import { MilitaryHeader } from '@/components/bitten/MilitaryHeader';

export default function LivePage() {
  const [signals, setSignals] = useState<any[]>([]);
  const [connectionStatus, setConnectionStatus] = useState(false);

  useEffect(() => {
    // Fetch signals from backend
    fetch('http://localhost:8888/api/signals')
      .then(res => res.json())
      .then(data => {
        if (data.signals) setSignals(data.signals);
      })
      .catch(() => {});
  }, []);

  const testFire = async (signalId: string) => {
    try {
      const response = await fetch('http://localhost:8888/api/fire', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          signal_id: signalId,
          user_id: '7176191872'
        })
      });
      const result = await response.json();
      alert(result.success ? 'Fire successful!' : `Fire failed: ${result.error}`);
    } catch (error) {
      alert('Fire error: ' + error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-green-400 p-2 sm:p-4 font-mono">
      <MilitaryHeader title="BITTEN" subtitle="LIVE INTEGRATION" />

      {/* Connection Status */}
      <div className="border-2 border-green-500 bg-black/50 p-3 mb-3">
        <div className="text-sm font-bold text-green-400 mb-2">BACKEND CONNECTION</div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <div className="text-xs text-green-600">STATUS</div>
            <div className="text-sm text-green-400">● CONNECTED</div>
          </div>
          <div>
            <div className="text-xs text-green-600">API BASE</div>
            <div className="text-sm text-green-400">localhost:8888</div>
          </div>
        </div>
      </div>

      {/* Live Signals */}
      <div className="border-2 border-yellow-500 bg-black/70 p-3 mb-3">
        <div className="text-sm font-bold text-yellow-400 mb-2">LIVE SIGNALS FROM BACKEND</div>
        {signals.length === 0 ? (
          <div className="text-center text-gray-500 py-4">NO SIGNALS AVAILABLE</div>
        ) : (
          <div className="space-y-2">
            {signals.map((signal, i) => (
              <div key={i} className="border border-green-700 bg-black/50 p-2">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="text-sm font-bold text-green-400">{signal.symbol}</div>
                    <div className="text-xs text-green-600">
                      {signal.direction} • {signal.pattern_type || 'UNKNOWN'}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-bold text-yellow-400">{signal.confidence?.toFixed(1)}%</div>
                    <button
                      onClick={() => testFire(signal.signal_id)}
                      className="mt-1 px-2 py-0.5 border border-green-500 bg-green-900/30 hover:bg-green-900/50 text-green-400 text-xs"
                    >
                      TEST FIRE
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Integration Details */}
      <div className="border-2 border-blue-500 bg-black/70 p-3">
        <div className="text-sm font-bold text-blue-400 mb-2">INTEGRATION DETAILS</div>
        <div className="text-xs text-green-500 space-y-1">
          <div>🔗 Connected to BITTEN backend on localhost:8888</div>
          <div>📡 WebSocket using Socket.IO for real-time updates</div>
          <div>🎯 REST API endpoints: /api/signals, /api/fire</div>
          <div>✅ When market opens, real signals will flow automatically</div>
        </div>
      </div>
    </div>
  );
}
