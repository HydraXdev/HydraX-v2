"use client"

import React, { useEffect, useState } from 'react';

export default function MissionSimple() {
  const [missionData, setMissionData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Get URL parameters
    const params = new URLSearchParams(window.location.search);
    const sessionId = params.get('ms');
    const token = params.get('token');

    if (!sessionId) {
      setError('No mission session ID provided');
      setLoading(false);
      return;
    }

    // Fetch mission data
    fetch(`http://134.199.204.67:8888/api/mission_session/${sessionId}`)
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setMissionData(data.mission);
        } else {
          setError(data.error || 'Failed to load mission');
        }
        setLoading(false);
      })
      .catch(err => {
        setError('Network error: ' + err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0e1a] flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[#34d399] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-[#cbd5e0]">Loading mission brief...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#0a0e1a] flex items-center justify-center p-4">
        <div className="bg-[#1a1f2e] border border-red-500 rounded-lg p-6 max-w-md">
          <h2 className="text-red-500 text-xl font-bold mb-2">Error</h2>
          <p className="text-[#cbd5e0]">{error}</p>
        </div>
      </div>
    );
  }

  if (!missionData) {
    return (
      <div className="min-h-screen bg-[#0a0e1a] flex items-center justify-center">
        <p className="text-[#cbd5e0]">No mission data available</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0e1a] p-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="bg-[#1a1f2e] border border-[#34d399] rounded-lg p-6 mb-4">
          <div className="flex items-center gap-4 mb-4">
            <div className="text-4xl">{missionData.direction === 'BUY' ? '📈' : '📉'}</div>
            <div>
              <h1 className="text-2xl font-bold text-[#34d399]">{missionData.symbol}</h1>
              <p className="text-[#cbd5e0]">{missionData.direction} • {missionData.confidence}%</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <p className="text-[#8b92a8] text-sm">Pattern</p>
              <p className="text-[#e5e7eb] font-semibold">{missionData.pattern_type?.replace(/_/g, ' ')}</p>
            </div>
            <div>
              <p className="text-[#8b92a8] text-sm">Timeframe</p>
              <p className="text-[#e5e7eb] font-semibold">{missionData.timeframe}</p>
            </div>
          </div>

          {/* Trade Levels */}
          <div className="border-t border-[#2a3142] pt-4 space-y-2">
            <div className="flex justify-between">
              <span className="text-[#8b92a8]">Entry:</span>
              <span className="text-[#e5e7eb] font-mono">{missionData.entry_price || 'Market'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#8b92a8]">Stop Loss:</span>
              <span className="text-red-500 font-mono">{missionData.stop_loss || 'N/A'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#8b92a8]">Take Profit:</span>
              <span className="text-[#34d399] font-mono">{missionData.take_profit || 'N/A'}</span>
            </div>
          </div>
        </div>

        {/* Briefing */}
        {missionData.briefing && (
          <div className="bg-[#1a1f2e] border border-[#2a3142] rounded-lg p-6 mb-4">
            <h2 className="text-[#34d399] font-bold mb-2">Mission Briefing</h2>
            <pre className="text-[#cbd5e0] whitespace-pre-wrap font-sans text-sm">
              {missionData.briefing}
            </pre>
          </div>
        )}

        {/* Fire Button */}
        {missionData.can_fire && (
          <button
            className="w-full bg-[#34d399] hover:bg-[#2dca89] text-black font-bold py-4 rounded-lg transition-colors"
            onClick={() => alert('Fire functionality coming soon!')}
          >
            🔥 FIRE COMMAND
          </button>
        )}
      </div>
    </div>
  );
}
