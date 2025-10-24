/**
 * PM2 Ecosystem Configuration - BITTEN Production Architecture
 *
 * 🚨 CRITICAL: This file defines the OFFICIAL process architecture
 *
 * DO NOT modify without explicit approval
 * DO NOT add processes that duplicate functionality
 * DO NOT start processes manually that conflict with this config
 *
 * Last Updated: 2025-10-13
 */

module.exports = {
  apps: [
    // ============================================================
    // SIGNAL GENERATION & RELAY (OFFICIAL ARCHITECTURE)
    // ============================================================

    /**
     * Elite Guard - Signal Generator
     * Status: PRODUCTION - DO NOT MODIFY
     * Port: 5557 (ZMQ PUB)
     */
    {
      name: 'elite_guard',
      script: 'elite_guard_with_citadel.py',
      interpreter: 'python3',
      cwd: '/root/HydraX-v2',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        NODE_ENV: 'production'
      }
    },

    /**
     * Elite Guard ZMQ Relay - Signal Bridge to WebApp
     * Status: PRODUCTION - OFFICIAL RELAY
     *
     * ⚠️ THIS IS THE ONLY SIGNAL RELAY - NO REDIS BRIDGES!
     *
     * Flow: Elite Guard ZMQ 5557 → HTTP POST /api/signals → WebApp
     */
    {
      name: 'elite_guard_relay',
      script: 'elite_guard_zmq_relay.py',
      interpreter: 'python3',
      cwd: '/root/HydraX-v2',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '100M',
      env: {
        NODE_ENV: 'production'
      }
    }
  ]
};

/**
 * ============================================================
 * ⛔ DEPRECATED / FORBIDDEN PROCESSES ⛔
 * ============================================================
 *
 * The following processes MUST NOT be started:
 *
 * ❌ signals_zmq_to_redis.py          - Replaced by elite_guard_relay
 * ❌ signals_redis_to_webapp.py       - Replaced by elite_guard_relay
 * ❌ signals_redis_to_webapp_fixed.py - Replaced by elite_guard_relay
 *
 * WHY: These processes cause:
 * - Consumer group deadlocks in Redis
 * - Unnecessary complexity
 * - Signal relay failures
 * - Resource waste
 *
 * IF YOU SEE THESE RUNNING:
 * 1. Kill them immediately: kill <PID>
 * 2. Verify elite_guard_relay is running: pm2 status elite_guard_relay
 * 3. Check signals flowing: pm2 logs elite_guard_relay --lines 20
 *
 * ============================================================
 */
