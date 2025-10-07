/**
 * Formatting utilities for consistent number/currency/date display
 */

/**
 * Format USD currency
 * @example fmtUSD(1234.56) => "$1,234.56"
 */
export function fmtUSD(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

/**
 * Format number with commas
 * @example fmtNum(1234.56) => "1,234.56"
 */
export function fmtNum(value: number, decimals: number = 2): string {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

/**
 * Format signed number (always show + or -)
 * @example fmtSigned(12.34) => "+12.34"
 * @example fmtSigned(-12.34) => "-12.34"
 */
export function fmtSigned(value: number, decimals: number = 2): string {
  const sign = value >= 0 ? '+' : '';
  return sign + fmtNum(value, decimals);
}

/**
 * Format pips (forex precision)
 * @example fmtPips(12.345) => "12.3"
 */
export function fmtPips(pips: number): string {
  return pips.toFixed(1);
}

/**
 * Format price to 5 decimals (forex standard)
 * @example fmtPrice(1.23456789) => "1.23457"
 */
export function fmtPrice(price: number): string {
  return price.toFixed(5);
}

/**
 * Format percentage
 * @example fmtPercent(0.1234) => "12.3%"
 */
export function fmtPercent(value: number, decimals: number = 1): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * Format timestamp to relative time
 * @example fmtRelative("2024-01-01T12:00:00Z") => "2h ago"
 */
export function fmtRelative(isoTimestamp: string): string {
  const date = new Date(isoTimestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHr = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHr / 24);

  if (diffSec < 60) return `${diffSec}s ago`;
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHr < 24) return `${diffHr}h ago`;
  return `${diffDay}d ago`;
}

/**
 * Format timestamp to time only
 * @example fmtTime("2024-01-01T12:34:56Z") => "12:34 UTC"
 */
export function fmtTime(isoTimestamp: string): string {
  const date = new Date(isoTimestamp);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'UTC',
    timeZoneName: 'short',
  });
}

/**
 * Format duration in seconds to MM:SS
 * @example fmtDuration(125) => "02:05"
 */
export function fmtDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Shorten large numbers with K/M suffix
 * @example fmtCompact(1234) => "1.2K"
 */
export function fmtCompact(value: number): string {
  if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
  if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
  return value.toString();
}
