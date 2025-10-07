/**
 * BITTEN theme tokens and semantic color system
 * Military ops terminal aesthetic with neon accents
 */

export const colors = {
  // Core palette
  onyx: "#0a0e1a", // Deep background
  slate: "#1a1f2e", // Panel background
  steel: "#2d3748", // Borders, dividers
  ash: "#4a5568", // Muted text
  silver: "#cbd5e0", // Secondary text

  // Accent colors
  emerald: "#10b981", // Success, TP, profit
  mint: "#34d399", // Primary accent, wins
  cyan: "#06b6d4", // Info, highlights
  gold: "#fbbf24", // Warning, pending
  amber: "#f59e0b", // Caution
  crimson: "#ef4444", // Danger, SL, loss

  // Semantic aliases
  primary: "#0a0e1a", // Main background
  secondary: "#4a5568", // Secondary text
  accent: "#34d399", // Primary interactions
  danger: "#ef4444", // Destructive actions
  warning: "#fbbf24", // Warnings
  success: "#10b981", // Success states
} as const;

/**
 * Semantic color classes for Tailwind
 * Use these for consistent theming across components
 */
export const semanticClasses = {
  // Backgrounds
  bgPrimary: "bg-[#0a0e1a]",
  bgPanel: "bg-[#1a1f2e]",
  bgOverlay: "bg-[#2d3748]/30",
  bgAccent: "bg-[#34d399]/10",

  // Text
  textPrimary: "text-[#cbd5e0]",
  textSecondary: "text-[#4a5568]",
  textMuted: "text-[#cbd5e0]/60",
  textAccent: "text-[#34d399]",
  textDanger: "text-[#ef4444]",
  textWarning: "text-[#fbbf24]",
  textSuccess: "text-[#10b981]",

  // Borders
  borderActive: "border-[#34d399]/30",
  borderMuted: "border-[#2d3748]",
  borderDanger: "border-[#ef4444]/30",
  borderWarning: "border-[#fbbf24]/30",

  // Interactive states
  hoverAccent: "hover:bg-[#34d399]/20",
  hoverDanger: "hover:bg-[#ef4444]/20",
  activeAccent: "active:bg-[#34d399]/30",

  // Glow effects (for neon aesthetic)
  glowMint: "shadow-[0_0_20px_rgba(52,211,153,0.5)]",
  glowCyan: "shadow-[0_0_20px_rgba(6,182,212,0.5)]",
  glowDanger: "shadow-[0_0_20px_rgba(239,68,68,0.5)]",
} as const;

/**
 * Component-specific theme variants
 */
export const componentThemes = {
  button: {
    primary: "bg-[#34d399] hover:bg-[#10b981] text-[#0a0e1a] font-tactical",
    secondary: "bg-[#2d3748] hover:bg-[#4a5568] text-[#cbd5e0] font-tactical",
    danger: "bg-[#ef4444] hover:bg-[#dc2626] text-white font-tactical",
  },

  panel: {
    default: "bg-[#1a1f2e] border border-[#2d3748] rounded-lg",
    accent: "bg-[#1a1f2e] border border-[#34d399]/30 rounded-lg",
    danger: "bg-[#1a1f2e] border border-[#ef4444]/30 rounded-lg",
  },

  badge: {
    success: "bg-[#10b981]/20 text-[#10b981] border border-[#10b981]/30",
    warning: "bg-[#fbbf24]/20 text-[#fbbf24] border border-[#fbbf24]/30",
    danger: "bg-[#ef4444]/20 text-[#ef4444] border border-[#ef4444]/30",
    info: "bg-[#06b6d4]/20 text-[#06b6d4] border border-[#06b6d4]/30",
  },
} as const;

/**
 * Typography scale for tabular numerals
 * Use these for consistent number display
 */
export const typography = {
  // Fonts
  tactical: 'font-["Rajdhani",sans-serif]', // Headers, UI elements
  code: 'font-["JetBrains_Mono",monospace]', // Numbers, data

  // Sizes
  displayLarge: "text-4xl font-tactical",
  displayMedium: "text-2xl font-tactical",
  displaySmall: "text-xl font-tactical",
  bodyLarge: "text-base",
  bodyMedium: "text-sm",
  bodySmall: "text-xs",

  // Special
  tabularNums: "font-mono tabular-nums", // For aligned number columns
} as const;

/**
 * Animation durations (respects prefers-reduced-motion)
 */
export const durations = {
  instant: "100ms",
  fast: "200ms",
  normal: "300ms",
  slow: "500ms",
} as const;

/**
 * Get color value by token name
 */
export function getColor(token: keyof typeof colors): string {
  return colors[token];
}

/**
 * Generate gradient background for panels
 */
export function gradientPanel(
  from: keyof typeof colors,
  to: keyof typeof colors,
): string {
  return `linear-gradient(135deg, ${colors[from]}, ${colors[to]})`;
}
