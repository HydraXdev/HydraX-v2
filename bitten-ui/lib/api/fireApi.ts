"use client"

/**
 * Trading API Client - Fire & Close Operations
 * Handles all trading actions with backend
 */

const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8888';
const FIRE_ENDPOINT = process.env.NEXT_PUBLIC_API_FIRE || '/api/fire';
const CLOSE_ALL_ENDPOINT = process.env.NEXT_PUBLIC_API_CLOSE_ALL || '/api/trades/close-all';

export interface FireRequest {
  alertId: string | number;
  entry: number;
  sl: number;
  tp: number;
  riskUsd: number;
}

export interface FireResponse {
  success: boolean;
  opId?: string;
  message?: string;
  error?: string;
}

export interface CloseAllRequest {
  reason: 'manual' | 'risk' | 'weekend';
}

export interface CloseAllResponse {
  success: boolean;
  opId?: string;
  message?: string;
  closedCount?: number;
}

/**
 * Execute a trade (fire signal)
 * Returns 202 Accepted - actual confirmation comes via event bus
 */
export async function executeFire(request: FireRequest): Promise<FireResponse> {
  try {
    const response = await fetch(`${API_BASE}${FIRE_ENDPOINT}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // TODO: Add auth header if needed
        // 'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.text();
      return {
        success: false,
        error: `HTTP ${response.status}: ${error}`,
      };
    }

    const data = await response.json();
    return {
      success: true,
      opId: data.opId,
      message: data.message,
    };
  } catch (error) {
    console.error('[Fire API] Error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Close all open positions
 * Returns 202 Accepted - closures stream via event bus
 */
export async function closeAllTrades(request: CloseAllRequest): Promise<CloseAllResponse> {
  try {
    const response = await fetch(`${API_BASE}${CLOSE_ALL_ENDPOINT}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // TODO: Add auth header if needed
        // 'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.text();
      return {
        success: false,
        error: `HTTP ${response.status}: ${error}`,
      };
    }

    const data = await response.json();
    return {
      success: true,
      opId: data.opId,
      message: data.message,
      closedCount: data.closedCount,
    };
  } catch (error) {
    console.error('[Close All API] Error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Test API connectivity
 */
export async function testConnection(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/healthz`, {
      method: 'GET',
    });
    return response.ok;
  } catch {
    return false;
  }
}
