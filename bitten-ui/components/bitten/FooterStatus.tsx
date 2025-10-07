"use client";

import React from "react";
import { Shield, Zap, Server } from "lucide-react";
import type { SystemStatus } from "@/lib/eventBus/contracts";

export interface FooterStatusProps {
  systemStatus?: SystemStatus;
  className?: string;
}

/**
 * FooterStatus - System status footer bar
 *
 * Features:
 * - Operational / Secure / Hydra Node status
 * - Latency indicator
 * - Color-coded status (green = OK, yellow = WARN, red = DOWN)
 * - Sticky bottom positioning
 */
export function FooterStatus({
  systemStatus,
  className = "",
}: FooterStatusProps) {
  const secure = systemStatus?.secure ?? true;
  const latency = systemStatus?.latencyMs ?? 0;
  const hydraNode = systemStatus?.hydraNode ?? "OK";

  return (
    <footer
      className={`
        border-t border-[#2d3748] bg-[#1a1f2e]/90 backdrop-blur-sm
        px-4 py-2
        ${className}
      `}
      role="contentinfo"
    >
      <div className="max-w-7xl mx-auto flex items-center justify-between text-xs">
        {/* Left: Status indicators */}
        <div className="flex items-center gap-4">
          {/* Operational */}
          <div
            className="flex items-center gap-1.5"
            role="status"
            aria-label="System operational"
          >
            <Shield className="w-3.5 h-3.5 text-[#34d399]" aria-hidden="true" />
            <span className="font-tactical text-[#34d399]">OPERATIONAL</span>
          </div>

          {/* Secure */}
          <div
            className="flex items-center gap-1.5"
            role="status"
            aria-label={secure ? "Secure" : "Insecure"}
          >
            <Zap
              className={`w-3.5 h-3.5 ${secure ? "text-[#34d399]" : "text-[#ef4444]"}`}
              aria-hidden="true"
            />
            <span
              className={`font-tactical ${secure ? "text-[#34d399]" : "text-[#ef4444]"}`}
            >
              {secure ? "SECURE" : "INSECURE"}
            </span>
          </div>

          {/* Hydra Node */}
          <div
            className="flex items-center gap-1.5"
            role="status"
            aria-label={`Hydra node ${hydraNode}`}
          >
            <Server
              className={`w-3.5 h-3.5 ${
                hydraNode === "OK"
                  ? "text-[#34d399]"
                  : hydraNode === "WARN"
                    ? "text-[#fbbf24]"
                    : "text-[#ef4444]"
              }`}
              aria-hidden="true"
            />
            <span
              className={`font-tactical ${
                hydraNode === "OK"
                  ? "text-[#34d399]"
                  : hydraNode === "WARN"
                    ? "text-[#fbbf24]"
                    : "text-[#ef4444]"
              }`}
            >
              HYDRA NODE {hydraNode}
            </span>
          </div>
        </div>

        {/* Right: Latency */}
        <div
          className="flex items-center gap-1.5"
          role="status"
          aria-label={`Latency ${latency} milliseconds`}
        >
          <span className="text-[#4a5568]">LATENCY:</span>
          <span
            className={`font-mono tabular-nums ${
              latency < 100
                ? "text-[#34d399]"
                : latency < 200
                  ? "text-[#fbbf24]"
                  : "text-[#ef4444]"
            }`}
          >
            {latency}ms
          </span>
        </div>
      </div>
    </footer>
  );
}
