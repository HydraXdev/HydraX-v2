"use client";

import React from "react";
import { HelpCircle, Menu } from "lucide-react";
import { motion } from "framer-motion";

export interface HelpMenuButtonsProps {
  onHelp: () => void;
  onMenu: () => void;
  className?: string;
}

/**
 * HelpMenuButtons - Always-present help and menu controls
 *
 * Features:
 * - Fixed position buttons (bottom-right on mobile, top-right on desktop)
 * - Keyboard accessible
 * - Touch-friendly 44px+ targets
 * - Respects safe areas
 */
export function HelpMenuButtons({
  onHelp,
  onMenu,
  className = "",
}: HelpMenuButtonsProps) {
  return (
    <div
      className={`
        fixed bottom-4 right-4 md:top-4 md:bottom-auto
        flex gap-2 z-40
        ${className}
      `}
      style={{
        paddingBottom: "env(safe-area-inset-bottom)",
        paddingRight: "env(safe-area-inset-right)",
      }}
    >
      {/* Help Button */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={onHelp}
        className="
          w-12 h-12 rounded-full
          bg-[#1a1f2e] border border-[#34d399]/30
          flex items-center justify-center
          hover:bg-[#34d399]/20 hover:border-[#34d399]
          transition-colors
          focus:outline-none focus:ring-2 focus:ring-[#34d399] focus:ring-offset-2 focus:ring-offset-[#0a0e1a]
        "
        aria-label="Open help"
        title="Help [?]"
      >
        <HelpCircle className="w-5 h-5 text-[#34d399]" aria-hidden="true" />
      </motion.button>

      {/* Menu Button */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={onMenu}
        className="
          w-12 h-12 rounded-full
          bg-[#1a1f2e] border border-[#cbd5e0]/30
          flex items-center justify-center
          hover:bg-[#cbd5e0]/20 hover:border-[#cbd5e0]
          transition-colors
          focus:outline-none focus:ring-2 focus:ring-[#cbd5e0] focus:ring-offset-2 focus:ring-offset-[#0a0e1a]
        "
        aria-label="Open menu"
        title="Menu"
      >
        <Menu className="w-5 h-5 text-[#cbd5e0]" aria-hidden="true" />
      </motion.button>
    </div>
  );
}
