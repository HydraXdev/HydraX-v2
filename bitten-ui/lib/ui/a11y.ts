"use client"

import { useEffect, useState } from 'react';

/**
 * Accessibility helpers for BITTEN UI
 * - Live region announcements
 * - Motion preference detection
 * - Keyboard navigation helpers
 */

/**
 * Hook to detect user's motion preference
 * Returns true if user prefers reduced motion
 *
 * @example
 * const prefersReducedMotion = useReducedMotion();
 * <motion.div animate={prefersReducedMotion ? {} : { scale: 1.05 }}>
 */
export function useReducedMotion(): boolean {
  const [prefersReduced, setPrefersReduced] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReduced(mediaQuery.matches);

    const handler = (event: MediaQueryListEvent) => {
      setPrefersReduced(event.matches);
    };

    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  return prefersReduced;
}

/**
 * Announce message to screen readers via live region
 * Creates a temporary aria-live region to announce changes
 *
 * @param message - Text to announce
 * @param priority - 'polite' (default) or 'assertive'
 *
 * @example
 * announce('Trade executed successfully');
 * announce('Critical error occurred', 'assertive');
 */
export function announce(message: string, priority: 'polite' | 'assertive' = 'polite') {
  if (typeof document === 'undefined') return;

  const liveRegion = document.createElement('div');
  liveRegion.setAttribute('role', 'status');
  liveRegion.setAttribute('aria-live', priority);
  liveRegion.setAttribute('aria-atomic', 'true');
  liveRegion.className = 'sr-only'; // Visually hidden but readable by screen readers
  liveRegion.textContent = message;

  document.body.appendChild(liveRegion);

  // Remove after announcement is read
  setTimeout(() => {
    document.body.removeChild(liveRegion);
  }, 1000);
}

/**
 * Generate unique ID for ARIA relationships
 * Useful for aria-labelledby, aria-describedby
 *
 * @example
 * const id = useAriaId('mission-brief');
 * <h1 id={id}>Mission Brief</h1>
 * <section aria-labelledby={id}>...</section>
 */
export function useAriaId(prefix: string): string {
  const [id] = useState(() => `${prefix}-${Math.random().toString(36).substr(2, 9)}`);
  return id;
}

/**
 * Focus trap utility for modals/dialogs
 * Keeps focus within a container element
 *
 * @param containerRef - React ref to the container element
 * @param active - Whether the trap is active
 */
export function useFocusTrap(
  containerRef: React.RefObject<HTMLElement>,
  active: boolean = true
) {
  useEffect(() => {
    if (!active || !containerRef.current) return;

    const container = containerRef.current;
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    if (focusableElements.length === 0) return;

    const firstElement = focusableElements[0] as HTMLElement;
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

    const handleTab = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        // Shift+Tab
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        // Tab
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    };

    container.addEventListener('keydown', handleTab);
    firstElement.focus();

    return () => {
      container.removeEventListener('keydown', handleTab);
    };
  }, [containerRef, active]);
}

/**
 * Visually hidden class for screen-reader-only content
 * Use in global CSS or Tailwind config
 */
export const SR_ONLY_CLASS = 'absolute w-px h-px p-0 -m-px overflow-hidden whitespace-nowrap border-0';
