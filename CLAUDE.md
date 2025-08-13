# BITTEN PRODUCTION SYSTEM - ACTUAL STATE

**Last Verified**: August 13, 2025 19:10 UTC  
**Method**: Direct process inspection (ps aux)

## ⚠️ CRITICAL EA VERSION - AUGUST 13, 2025 ⚠️

**PRODUCTION EA:** `/root/HydraX-v2/BITTEN_Universal_EA_v2.05_PRODUCTION.mq5`
- Version 2.05 is the ONLY valid EA in production
- Uses DEALER socket with ZMQ_IDENTITY for targeted commands  
- Sends confirmations WITH fire_id tracking
- All other EA versions are OUTDATED/INVALID/SUPERSEDED/ANTIQUE

**Fire Command Format the EA expects EXACTLY:**
```json
{
  "type": "fire",
  "fire_id": "fir_xxx",
  "target_uuid": "COMMANDER_DEV_001",
  "symbol": "EURUSD",
  "direction": "BUY",
  "entry": 1.1700,
  "sl": 1.1690,
  "tp": 1.1720,
  "lot": 0.01
}
```

## WORK COMPLETED - AUGUST 12, 2025 (CONTINUED SESSION)

### Additional Fixes & Deployments:

6. **VCB Guard Additive Detector**
   - **Created**: `/root/HydraX-v2/tools/vcb_guard.py`
   - Volatility Compression Breakout pattern detection
   - Fixed timestamp parsing for "2025.08.13 01:37:57" format
   - Min RR 1.4 gate, shadow/live mode support
   - Currently tracking 15 symbols, 100+ candles built
   - PM2 process: vcb_guard (PID 3308978)

7. **XP System Implementation**
   - **Database**: Added xp_events and xp_totals tables
   - **Daemon**: `/root/HydraX-v2/tools/xp_daemon.py`
   - Awards variety bonuses (5 XP per new pattern type)
   - Awards streak bonuses (3 XP per 3-in-a-row same type)
   - PM2 process: xp_daemon (PID 3292601)

8. **FOMO Funnel System (RAPID vs SNIPER)**
   - **Pattern Classification**:
     - RAPID (all tiers): VCB_BREAKOUT, SWEEP_RETURN
     - SNIPER (PRO+ only): LIQUIDITY_SWEEP_REVERSAL, ORDER_BLOCK_BOUNCE, FAIR_VALUE_GAP_FILL
   - **Webapp Tier Gates**: 
     - Added helper functions: _bitten_can_fire(), _bitten_user_tier(), _bitten_signal_class_from_id()
     - /api/fire endpoint now enforces tier restrictions
     - Returns upgrade_required=true with upgrade_url for non-eligible users
   - **Upgrade Endpoint**: Added /upgrade landing page
   - **Telegram Alerts**: Distinct formatting ⚡ RAPID vs 🎯 SNIPER

9. **Infrastructure Repairs**
   - **Telemetry Bridge**: Restarted (was down, now PID 3312722)
   - **Tick Flow**: Fixed ZMQ 5556 → 5560 pipeline
   - **Live Balance Helpers**: Added to webapp for fresh EA balance display

## WORK COMPLETED - AUGUST 12, 2025

### Signal Generation Fixes:
1. **Elite Guard Signal Blackout Fixed** 
   - Removed fake confidence validation blocking scores 65, 70, 75
   - File: `/root/HydraX-v2/elite_guard_with_citadel.py`
   - These are legitimate pattern scores, not fake

2. **ZMQ→Redis Bridge Fixed**
   - Added handling for "ELITE_GUARD_SIGNAL " prefix
   - File: `/root/HydraX-v2/tools/signals_zmq_to_redis.py`
   - Signals now flowing: 7 in Redis stream

3. **Additive Detectors Deployed**
   - **SRL Guard** (Sweep-and-Return): `/root/HydraX-v2/tools/srl_guard.py`
     - Min RR 1.4, 60% wick requirement
     - PM2 process: srl_guard (LIVE mode)
   - **VCB Guard** (Volume Climax Breakout): Already running
     - PM2 process: vcb_guard (LIVE mode)

4. **Broadcast Lane Implemented**
   - signals → alerts → Telegram pipeline
   - Pattern classification: RAPID vs SNIPER
   - Files created:
     - `/root/HydraX-v2/tools/signals_to_alerts.py` (fanout with classification)
     - `/root/HydraX-v2/tools/telegram_broadcaster_alerts.py` (Telegram alerts)
   - Pattern mapping:
     - VCB_BREAKOUT, SWEEP_RETURN → ⚡ RAPID
     - LIQUIDITY_SWEEP_REVERSAL, ORDER_BLOCK_BOUNCE, FAIR_VALUE_GAP_FILL → 🎯 SNIPER

5. **Monitoring/Watchdogs Fixed**
   - EA watchdog now loops continuously
   - File: `/root/HydraX-v2/tools/watchdog_ea_and_fires.sh`

### Current PM2 Processes (As of 22:50 UTC):
- elite_guard (PID 3259337) - SMC pattern detection
- vcb_guard (PID 3308978) - LIVE mode, tracking 15 symbols
- srl_guard (PID 3310201) - LIVE mode, sweep-return patterns
- xp_daemon (PID 3292601) - XP award system
- signals_zmq_to_redis (PID 3245481) - ZMQ→Redis bridge
- signals_to_alerts (PID 3320888) - Pattern classification
- telegram_broadcaster_alerts (PID 3329820) - RAPID/SNIPER alerts
- signals_redis_to_webapp (PID 3219389) - WebApp feed
- webapp (PID 3331218) - Port 8888 with tier gates
- zmq_telemetry_bridge_debug (PID 3312722) - Tick relay

### Summary of Session Work:
- **VCB Guard**: Created and deployed volatility breakout detector
- **XP System**: Database tables and daemon for pattern variety rewards
- **FOMO Funnel**: RAPID vs SNIPER classification with tier-based access
- **Infrastructure**: Fixed telemetry bridge, tick flow restored
- **Webapp**: Added tier gates, upgrade endpoint, pattern classification helpers

### Notes:
- All 3 pattern detectors running (Elite Guard, VCB, SRL)
- Ticks flowing, 100+ candles built, waiting for patterns
- FOMO system ready: base tiers see all, can only fire RAPID
- Commander Dev 001 is active (00 archived)
- Telegram bot token configured and running

## WHAT'S ACTUALLY RUNNING RIGHT NOW

```bash
# Signal Generation
PID 2581568: elite_guard_with_citadel.py
PID 2577665: elite_guard_zmq_relay.py  
PID 2411770: zmq_telemetry_bridge_debug.py

# User Interface
PID 2588730: bitten_production_bot.py (Telegram)
PID 2582822: webapp_server_optimized.py (Port 8888)
PID 2454259: commander_throne.py (Port 8899)

# Infrastructure
PID 2455681: simple_truth_tracker.py
PID 2409025: position_tracker.py
PID 2586467: handshake_processor.py
```

## CRITICAL FACTS

1. **NO LOCAL MT5** - All MT5 operations via ForexVPS API
2. **NO VENOM** - Elite Guard is the ONLY signal generator running
3. **FOREXVPS ONLY** - Zero local terminal management

## DON'T ADD CODE - CHECK WHAT'S RUNNING

Before writing ANY code:
1. Run `ps aux | grep {process_name}`
2. Check if it's already running
3. Don't create duplicates
4. Don't trust old documentation

## STOP CREATING FILES

The system has 280+ Python files. STOP ADDING MORE.
- Fix what exists
- Delete what's broken
- Don't create new versions

That's it. Everything else is outdated bloat.