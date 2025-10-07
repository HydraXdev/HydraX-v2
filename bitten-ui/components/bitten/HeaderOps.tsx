"use client";

import React from "react";
import { Shield, Activity, Clock } from "lucide-react";
import { fmtTime } from "@/lib/ui/format";
import type { SystemStatus } from "@/lib/eventBus/contracts";

export interface HeaderOpsProps {
  pageTitle: string;
  systemStatus?: SystemStatus;
  userLevel?: string;
  className?: string;
}

/**
 * HeaderOps - Military HUD-style header with system beacons
 *
 * Features:
 * - BITTEN branding + page title badge
 * - System status beacons (Operational/Secure/Latency)
 * - UTC clock
 * - User level pill
 * - Mobile responsive (2-row layout on small screens)
 */
export function HeaderOps({
  pageTitle,
  systemStatus,
  userLevel,
  className = "",
}: HeaderOpsProps) {
  const [currentTime, setCurrentTime] = React.useState(
    new Date().toISOString(),
  );

  React.useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toISOString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header
      className={`
        border-b border-[#2d3748] backdrop-blur-sm bg-[#1a1f2e]/90
        sticky top-0 z-50 px-4 py-3
        ${className}
      `}
      role="banner"
    >
      <div className="max-w-7xl mx-auto">
        {/* Desktop layout */}
        <div className="hidden md:flex items-center justify-between">
          {/* Left: Branding + Title */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Shield className="w-6 h-6 text-[#34d399]" aria-hidden="true" />
              <span className="text-xl font-tactical text-[#34d399]">
                BITTEN
              </span>
            </div>
            <div className="h-6 w-px bg-[#2d3748]" aria-hidden="true" />
            <div className="px-3 py-1 bg-[#34d399]/10 border border-[#34d399]/30 rounded text-sm font-tactical text-[#34d399]">
              {pageTitle}
            </div>
          </div>

          {/* Right: Status Beacons */}
          <div className="flex items-center gap-6">
            {/* Operational Beacon */}
            <div
              className="flex items-center gap-2"
              role="status"
              aria-label="System operational"
            >
              <Activity className="w-4 h-4 text-[#34d399]" aria-hidden="true" />
              <span className="text-sm font-tactical text-[#34d399]">
                OPERATIONAL
              </span>
            </div>

            {/* Secure Beacon */}
            {systemStatus && (
              <div
                className="flex items-center gap-2"
                role="status"
                aria-label={
                  systemStatus.secure
                    ? "Secure connection"
                    : "Insecure connection"
                }
              >
                <div
                  className={`w-2 h-2 rounded-full ${
                    systemStatus.secure
                      ? "bg-[#34d399] animate-pulse"
                      : "bg-[#ef4444] animate-pulse"
                  }`}
                  aria-hidden="true"
                />
                <span
                  className={`text-sm font-tactical ${systemStatus.secure ? "text-[#34d399]" : "text-[#ef4444]"}`}
                >
                  {systemStatus.secure ? "SECURE" : "INSECURE"}
                </span>
              </div>
            )}

            {/* Latency */}
            {systemStatus && (
              <div
                className="flex items-center gap-2"
                role="status"
                aria-label={`Latency ${systemStatus.latencyMs} milliseconds`}
              >
                <span className="text-xs text-[#4a5568]">LAT:</span>
                <span
                  className={`text-sm font-mono tabular-nums ${
                    systemStatus.latencyMs < 100
                      ? "text-[#34d399]"
                      : systemStatus.latencyMs < 200
                        ? "text-[#fbbf24]"
                        : "text-[#ef4444]"
                  }`}
                >
                  {systemStatus.latencyMs}ms
                </span>
              </div>
            )}

            {/* UTC Clock */}
            <div
              className="flex items-center gap-2"
              role="timer"
              aria-label={`Current time ${fmtTime(currentTime)}`}
            >
              <Clock className="w-4 h-4 text-[#cbd5e0]" aria-hidden="true" />
              <time className="text-sm font-mono tabular-nums text-[#cbd5e0]">
                {fmtTime(currentTime)}
              </time>
            </div>

            {/* User Level */}
            {userLevel && (
              <div className="px-3 py-1 bg-[#06b6d4]/10 border border-[#06b6d4]/30 rounded text-sm font-tactical text-[#06b6d4]">
                {userLevel}
              </div>
            )}
          </div>
        </div>

        {/* Mobile layout (2 rows) */}
        <div className="md:hidden space-y-2">
          {/* Row 1: Branding + Title */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-[#34d399]" aria-hidden="true" />
              <span className="text-lg font-tactical text-[#34d399]">
                BITTEN
              </span>
            </div>
            <div className="px-2 py-1 bg-[#34d399]/10 border border-[#34d399]/30 rounded text-xs font-tactical text-[#34d399]">
              {pageTitle}
            </div>
          </div>

          {/* Row 2: Compact Status */}
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1">
                <div
                  className={`w-2 h-2 rounded-full ${systemStatus?.secure ? "bg-[#34d399]" : "bg-[#ef4444]"} animate-pulse`}
                  aria-hidden="true"
                />
                <span className="text-[#4a5568]">OPS</span>
              </div>
              {systemStatus && (
                <span className="font-mono tabular-nums text-[#cbd5e0]">
                  {systemStatus.latencyMs}ms
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <time className="font-mono tabular-nums text-[#cbd5e0]">
                {fmtTime(currentTime)}
              </time>
              {userLevel && (
                <span className="px-2 py-0.5 bg-[#06b6d4]/10 border border-[#06b6d4]/30 rounded text-[#06b6d4]">
                  {userLevel}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
