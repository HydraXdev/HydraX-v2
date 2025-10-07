"use client";

import React from "react";

export interface DossierKVProps {
  label: string;
  value: React.ReactNode;
  valueColor?: "primary" | "success" | "danger" | "warning" | "cyan";
  className?: string;
}

/**
 * DossierKV - Key/Value row for mission dossiers
 *
 * Features:
 * - Compact two-column layout
 * - Tabular numerals for values
 * - Semantic color coding
 * - Responsive (stacks on very small screens)
 */
export function DossierKV({
  label,
  value,
  valueColor = "primary",
  className = "",
}: DossierKVProps) {
  const colorClasses = {
    primary: "text-[#cbd5e0]",
    success: "text-[#34d399]",
    danger: "text-[#ef4444]",
    warning: "text-[#fbbf24]",
    cyan: "text-[#06b6d4]",
  };

  return (
    <div
      className={`flex items-baseline justify-between py-2 border-b border-[#2d3748]/50 ${className}`}
    >
      <dt className="text-sm text-[#4a5568]">{label}</dt>
      <dd
        className={`text-sm font-mono tabular-nums ${colorClasses[valueColor]}`}
      >
        {value}
      </dd>
    </div>
  );
}

/**
 * DossierSection - Container for multiple KV rows
 */
export function DossierSection({
  title,
  children,
  className = "",
}: {
  title?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <dl className={`space-y-0 ${className}`}>
      {title && (
        <div className="mb-2 pb-2 border-b border-[#34d399]/30">
          <h3 className="text-xs font-tactical text-[#34d399] uppercase tracking-wider">
            {title}
          </h3>
        </div>
      )}
      {children}
    </dl>
  );
}
