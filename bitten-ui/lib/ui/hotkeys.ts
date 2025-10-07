"use client";

import { useEffect, useCallback } from "react";

/**
 * Hotkey handler with cleanup
 * Maps keys to actions with automatic event listener management
 */

export type HotkeyMap = {
  [key: string]: () => void;
};

/**
 * Register global hotkeys
 * @param keyMap - Object mapping keys to callbacks (e.g., { 'e': executeAction })
 * @param enabled - Whether hotkeys are active (default: true)
 *
 * @example
 * useHotkeys({
 *   'e': () => executeTrade(),
 *   'd': () => router.push('/status'),
 *   '?': () => openHelp(),
 * });
 */
export function useHotkeys(keyMap: HotkeyMap, enabled: boolean = true) {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      // Skip if user is typing in an input/textarea
      const target = event.target as HTMLElement;
      if (
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable
      ) {
        return;
      }

      // Skip if modifier keys are pressed (except Shift for ? help)
      if (event.ctrlKey || event.altKey || event.metaKey) {
        return;
      }

      const key = event.key.toLowerCase();
      const handler = keyMap[key];

      if (handler) {
        event.preventDefault();
        handler();
      }
    },
    [keyMap],
  );

  useEffect(() => {
    if (!enabled) return;

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown, enabled]);
}

/**
 * Hotkey hint component helper
 * Returns formatted string for UI display
 *
 * @example
 * <button>Execute {hotkeyHint('E')}</button>
 * // renders: "Execute [E]"
 */
export function hotkeyHint(key: string): string {
  return `[${key.toUpperCase()}]`;
}

/**
 * Common hotkey patterns for BITTEN app
 */
export const COMMON_HOTKEYS = {
  EXECUTE: "e",
  DECLINE: "x",
  HELP: "?",
  NOTEBOOK: "n",
  STATUS: "d",
  WAR_ROOM: "w",
  ALERTS: "a",
  STATS: "s",
  CLOSE: "x",
} as const;
