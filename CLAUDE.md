# 🔒 ARCHITECTURE LOCK - CRITICAL INSTRUCTIONS 🔒

**STOP**: Before doing ANYTHING, read `/root/ARCHITECTURE.md` for the ACTUAL system architecture.

The ARCHITECTURE.md file is the ONLY source of truth. It defines:
- **LOCKED COMPONENTS**: DO NOT MODIFY under any circumstances
- **STABLE COMPONENTS**: Modify only with explicit permission  
- **FLEXIBLE COMPONENTS**: Safe to modify

**DO NOT**:
- Trust old documentation over ARCHITECTURE.md
- Modify LOCKED components (Elite Guard, ZMQ ports, EA, etc.)
- Create duplicate processes or files
- Add new pattern detectors (all 10 are integrated)
- Change core trading logic without explicit approval

**ALWAYS**:
- Check ARCHITECTURE.md first
- Verify what's actually running with `ps aux | grep [process]`
- Follow the defined component boundaries
- Ask before modifying STABLE components

If ARCHITECTURE.md and this file conflict, **ARCHITECTURE.md wins**.

---

# BITTEN SYSTEM OPERATIONAL STATUS

**Last Updated**: September 14, 2025  
**Architecture**: See `/root/ARCHITECTURE.md` for complete system design  
**Status**: PRODUCTION - All systems operational

## 📊 CURRENT TRACKING LOCATIONS

**ACTIVE TRACKING FILES (September 2025)**:
- `/root/HydraX-v2/comprehensive_tracking.jsonl` - Primary signal tracking
- `/root/HydraX-v2/dynamic_tracking.jsonl` - Dynamic outcome tracking  
- `/root/HydraX-v2/ml_training_data.jsonl` - ML training data

**DATABASE**:
- `/root/HydraX-v2/bitten.db` - SQLite database with all signals, trades, outcomes

---

## 🚨 EVENT BUS - INSTITUTIONAL GRADE TRACKING SYSTEM (September 15, 2025) 🚨

### **CRITICAL: This is the NEW centralized tracking system - DO NOT USE OLD TRACKING FILES**

**Status**: ✅ FULLY OPERATIONAL - Capturing all events  
**Architecture**: Broker pattern with PULL/PUB sockets  
**Database**: `/root/HydraX-v2/bitten_events.db`  
**Integration**: Webapp publishing signals, more components pending

### **What is the Event Bus?**
The Event Bus is an institutional-grade, event-driven tracking system that replaces ALL previous tracking methods. It captures EVERY event in the trading lifecycle from signal generation to final TP/SL outcome.

### **Architecture (Broker Pattern)**:
```
Components → PUSH(5571) → Event Bus Broker → PUB(5570) → Data Collector → Database
```

- **Port 5571**: PULL socket - receives events from all components
- **Port 5570**: PUB socket - broadcasts events to subscribers
- **Database**: SQLite with specialized tables for different event types

### **Key Features**:
- **Complete Lifecycle Tracking**: Signal → Fire → Execution → Outcome
- **Event Sourcing**: Stores state changes, not current states (efficient)
- **Deduplication**: Shared signal data stored once, user actions tracked separately
- **Immutable Audit Trail**: Every event timestamped with microsecond precision
- **Correlation IDs**: Links related events across the entire trade lifecycle

### **Database Schema**:
```sql
-- Main events table (all events)
events: id, event_type, timestamp, data

-- Specialized tables for analysis
signal_events: signal_id, pattern, confidence, symbol, direction, timestamp
trade_events: trade_id, signal_id, user_id, action, timestamp, outcome
health_events: component, status, metrics, timestamp
```

### **How to Query Event Bus Data**:
```bash
# Check event count
sqlite3 /root/HydraX-v2/bitten_events.db "SELECT COUNT(*) FROM events;"

# Recent signals
sqlite3 /root/HydraX-v2/bitten_events.db "SELECT * FROM signal_events ORDER BY timestamp DESC LIMIT 5;"

# Check specific signal lifecycle
sqlite3 /root/HydraX-v2/bitten_events.db "SELECT * FROM events WHERE data LIKE '%SIGNAL_ID_HERE%' ORDER BY timestamp;"
```

### **Running Processes**:
```bash
pm2 list | grep -E "event_bus|data_collector"
# Should show:
# event_bus - Broker service on ports 5571/5570
# data_collector - Capturing and storing events
```

### **⚠️ IMPORTANT - FOR ALL AGENTS**:
1. **DO NOT** use old tracking files (comprehensive_tracking.jsonl, dynamic_tracking.jsonl, etc.)
2. **DO NOT** create new tracking systems - Event Bus handles everything
3. **DO NOT** write directly to tracking files - publish events to Event Bus instead
4. **ALWAYS** query bitten_events.db for tracking data
5. **ALWAYS** use the Event Bus client to publish new events

### **Integration Status**:
- ✅ **Event Bus**: Running (broker on 5571/5570)
- ✅ **Data Collector**: Running (storing all events)
- ✅ **Webapp**: Publishing signal events
- ⏳ **Elite Guard**: Pending integration
- ⏳ **Fire Router**: Pending integration
- ⏳ **Confirmation Listener**: Pending integration
- ⏳ **Outcome Monitor**: Pending integration

### **Event Bus Client Usage** (for integrating new components):
```python
from event_bus.event_bridge import signal_generated, trade_executed, trade_confirmed

# Publish a signal event
signal_generated({
    'signal_id': 'ELITE_RAPID_EURUSD_123',
    'pattern': 'KALMAN_QUICKFIRE',
    'confidence': 85.0,
    'symbol': 'EURUSD',
    'direction': 'BUY'
})

# Publish a trade execution
trade_executed({
    'trade_id': 'TRADE_123',
    'signal_id': 'ELITE_RAPID_EURUSD_123',
    'user_id': '7176191872',
    'lot_size': 0.10
})
```

### **Why Event Bus vs Old Tracking**:
- **Old**: Multiple JSONL files, inconsistent formats, race conditions, data loss
- **New**: Single source of truth, ACID compliance, event sourcing, correlation tracking
- **Old**: 50,000 files for 5,000 users × 10 signals = disk explosion
- **New**: Efficient deduplication, only track actual events, ~99% space savings

---

### **SYSTEM STATUS COMMANDS:**
```bash
# Check running processes (as defined in ARCHITECTURE.md)
pm2 list

# Check recent signals
tail -5 /root/HydraX-v2/comprehensive_tracking.jsonl

# Check signal database
sqlite3 /root/HydraX-v2/bitten.db "SELECT COUNT(*) FROM signals WHERE created_at > strftime('%s', 'now', '-1 hour');"

# Run performance report
python3 -c "$(cat /root/CLAUDE.md | grep -A 50 'bitten-report' | grep -A 50 'python3')"
```

### **CURRENT SYSTEM CONFIGURATION (Sept 14, 2025)**:
- **10 Active Patterns**: All integrated in Elite Guard (see ARCHITECTURE.md)
- **19 Trading Pairs**: USDCAD and XAGUSD removed for poor performance
- **Auto-Fire Range**: 80-89% confidence (optimal win rate zone)
- **Signal Threshold**: 70%+ for Telegram alerts
- **Architecture**: Fully documented in `/root/ARCHITECTURE.md`

---

## 🎯 BITTEN-REPORT COMMAND - REAL-TIME PERFORMANCE (EVENT BUS)

**Quick Performance Check**: Run `bitten-report` for comprehensive system status

```bash
python3 -c "
import json, sqlite3
from datetime import datetime, timedelta
from collections import defaultdict

print('='*70)
print('🎯 BITTEN SYSTEM PERFORMANCE REPORT (EVENT BUS)')
print('='*70)

# Connect to Event Bus database for real-time data
event_conn = sqlite3.connect('/root/HydraX-v2/event_bus/bitten_events.db')
event_cursor = event_conn.cursor()

# Get total events
event_cursor.execute('SELECT COUNT(*) FROM events')
total_events = event_cursor.fetchone()[0]
print(f'\n📡 EVENT BUS STATUS: {total_events} total events captured')

# Get event type breakdown
event_cursor.execute('''
    SELECT event_type, COUNT(*) as count
    FROM events
    WHERE created_at > (julianday('now') - 1) * 86400
    GROUP BY event_type
    ORDER BY count DESC
''')
print('\n📊 EVENT TYPES (24H):')
print('-'*50)
for row in event_cursor.fetchall():
    print(f'{row[0]:30} {row[1]:6} events')

# Extract signal outcomes from Event Bus
event_cursor.execute('''
    SELECT 
        json_extract(data_json, '$.outcome') as outcome,
        json_extract(data_json, '$.pattern') as pattern,
        json_extract(data_json, '$.pips_result') as pips,
        json_extract(data_json, '$.confidence') as confidence
    FROM events
    WHERE event_type IN ('signal_outcome_recorded', 'trade_outcome')
        AND created_at > (julianday('now') - 1) * 86400
''')

outcomes = event_cursor.fetchall()
wins = sum(1 for o in outcomes if o[0] == 'WIN')
losses = sum(1 for o in outcomes if o[0] == 'LOSS')

if wins + losses > 0:
    win_rate = (wins / (wins + losses)) * 100
    total_pips = sum(float(o[2]) for o in outcomes if o[2])
    avg_conf = sum(float(o[3]) for o in outcomes if o[3]) / len(outcomes) if outcomes else 0
    
    print(f'\n📈 TRACKED OUTCOMES (EVENT BUS):')
    print(f'Wins: {wins} | Losses: {losses}')
    print(f'Win Rate: {win_rate:.1f}%')
    print(f'Total Pips: {total_pips:.1f}')
    print(f'Avg Confidence: {avg_conf:.1f}%')
    
    # Pattern breakdown
    pattern_stats = defaultdict(lambda: {'wins': 0, 'losses': 0})
    for outcome in outcomes:
        if outcome[1] and outcome[0]:
            if outcome[0] == 'WIN':
                pattern_stats[outcome[1]]['wins'] += 1
            elif outcome[0] == 'LOSS':
                pattern_stats[outcome[1]]['losses'] += 1
    
    if pattern_stats:
        print('\n🎯 PATTERN PERFORMANCE:')
        print('-'*50)
        for pattern, stats in sorted(pattern_stats.items()):
            total = stats['wins'] + stats['losses']
            if total > 0:
                wr = (stats['wins'] / total) * 100
                print(f'{pattern:25} W:{stats[\"wins\"]:3} L:{stats[\"losses\"]:3} WR:{wr:.0f}%')
else:
    print('\n⏳ No outcomes recorded in Event Bus yet')

# Still check main database for signal generation
conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
cursor = conn.cursor()
cursor.execute('''
    SELECT COUNT(*) as total,
           COUNT(CASE WHEN created_at > strftime('%s', 'now', '-1 hour') THEN 1 END) as last_hour,
           COUNT(CASE WHEN created_at > strftime('%s', 'now', '-10 minutes') THEN 1 END) as last_10min
    FROM signals
    WHERE created_at > strftime('%s', 'now', '-24 hours')
''')
result = cursor.fetchone()
print(f'\n⚡ SIGNAL GENERATION:')
print(f'Last 10 min: {result[2]} | Last hour: {result[1]} | Last 24h: {result[0]}')

print('='*70)
print('📌 Data source: Event Bus (/root/HydraX-v2/event_bus/bitten_events.db)')
print('='*70)
"
```

---

## ✅ PATTERN SYSTEM - 10 PATTERNS INTEGRATED

### **ALL 10 PATTERNS ACTIVE IN ELITE GUARD**

As documented in `/root/ARCHITECTURE.md`, all patterns are integrated directly into Elite Guard:
1. **LIQUIDITY_SWEEP_REVERSAL** - Smart Money Concepts
2. **ORDER_BLOCK_BOUNCE** - Institutional zones
3. **FAIR_VALUE_GAP_FILL** - Price inefficiencies
4. **VCB_BREAKOUT** - Volatility compression
5. **SWEEP_RETURN** - Sweep and return liquidity
6. **MOMENTUM_BURST** - Momentum acceleration
7. **VOLUME_IMBALANCE** - Order flow imbalance
8. **RANGE_REJECTION** - Range boundary rejection
9. **KALMAN_QUICKFIRE** - Statistical prediction (96% win rate)
10. **BB_SCALP** - Bollinger Band scalping

**Pattern Performance**: Run `bitten-report` for latest statistics

---

## 📊 TRACKING & ML SYSTEMS

**Active Tracking Systems**:
- **Comprehensive Tracker**: Tracks all signals to actual TP/SL outcomes
- **Dynamic Tracker**: ATR-based outcome resolution (max 4 hours)
- **ML Training Data**: Pattern performance for model training
- **Confidence Calibration**: Ensures confidence scores match actual win rates

**ML Components**:
- **Location**: `/root/HydraX-v2/ml_systems/` (various components)
- **Integration**: Direct integration with Elite Guard signal generation
- **Performance**: Tracks expectancy value, not just win rate
- **Auto-adjustment**: Patterns below 40% win rate after 10 trades disabled

## 🔥 CRITICAL SYSTEM COMPONENTS

### **EXPERT ADVISOR (EA)**
- **Version**: v2.06H (Production as of Sept 14, 2025)
- **Documentation**: `/root/HydraX-v2/EA_v2.06H_PRODUCTION.md`
- **Identity**: COMMANDER_DEV_001
- **Features**: Enhanced position tracking, 10-slot limit, hedge prevention
- **Status**: LOCKED component - DO NOT MODIFY

### **ELITE GUARD WITH CITADEL**
- **File**: `/root/HydraX-v2/elite_guard_with_citadel.py`
- **Status**: LOCKED component (see ARCHITECTURE.md)
- **Patterns**: All 10 patterns integrated, no separate processes
- **Thresholds**: 70% for signals, 80-89% for auto-fire
- **Pairs**: 19 active (USDCAD and XAGUSD removed Sept 14)

### **FIRE EXECUTION PIPELINE**
```
Signal → WebApp → Enqueue Fire → IPC Queue → Command Router → EA → MT5
```
- **IPC Queue**: `ipc:///tmp/bitten_cmdqueue`
- **Command Router**: Port 5555 (ROUTER socket)
- **EA Identity**: COMMANDER_DEV_001
- **Confirmations**: Port 5558

### **ZMQ ARCHITECTURE**
- **Port 5555**: Command router (fire commands TO EA)
- **Port 5556**: Market data ingestion (FROM EA)
- **Port 5557**: Elite Guard signals (PUB)
- **Port 5558**: Trade confirmations (FROM EA)
- **Port 5560**: Market data relay (telemetry bridge)

All ports and architecture are LOCKED - see ARCHITECTURE.md

## 🛠️ CURRENT CONFIGURATION

### **TRADING PARAMETERS (Sept 14, 2025)**
- **Signal Threshold**: 70% confidence (for Telegram alerts)
- **Auto-Fire Range**: 80-89% confidence (optimal win rate zone)
- **Risk Per Trade**: 2% account balance
- **Trading Pairs**: 19 active (see Elite Guard config)
- **Pattern Count**: 10 integrated patterns

### **PERFORMANCE METRICS**
- **Sept 12 Win Rate**: 71.5% (253 trades analyzed)
- **Best Pattern**: KALMAN_QUICKFIRE (96.2% win rate)
- **Optimal Confidence**: 80-85% (90% win rate)
- **Auto-Fire Sweet Spot**: 80-89% confidence

### **DATABASE TABLES**
As documented in ARCHITECTURE.md:
- `signals`: All generated signals
- `fires`: Trade execution records
- `missions`: Signal-to-mission mapping
- `ea_instances`: EA connection status
- Plus 20+ other tables (see ARCHITECTURE.md)

## 🔍 QUICK REFERENCE

### **ESSENTIAL COMMANDS**

```bash
# Run performance report
bitten-report

# Check system status
pm2 list

# Check recent signals
tail -5 /root/HydraX-v2/comprehensive_tracking.jsonl

# Monitor Elite Guard
pm2 logs elite_guard --lines 20

# Check architecture documentation
cat /root/ARCHITECTURE.md
```

### **CRITICAL FILES**

**Documentation**:
- `/root/ARCHITECTURE.md` - **COMPLETE SYSTEM DESIGN (SOURCE OF TRUTH)**
- `/root/HydraX-v2/LOCKED_ARCHIVE_20250914_FINAL/QUARANTINE.md` - Archived files list

**Core Components** (DO NOT MODIFY - see ARCHITECTURE.md):
- `/root/HydraX-v2/elite_guard_with_citadel.py` - Signal generation
- `/root/HydraX-v2/webapp_server_optimized.py` - Web interface
- `/root/HydraX-v2/command_router.py` - Fire command routing
- `/root/HydraX-v2/enqueue_fire.py` - Fire command creation

**Configuration**:
- `/root/HydraX-v2/bitten.db` - SQLite database
- `/root/HydraX-v2/.env.master` - Environment variables

---

# 🤖 AGENT MISSION CONFIRMATION

**I, Claude Code, confirm that I understand this mission 100%:**

✅ **I WILL:**
- Always check `/root/ARCHITECTURE.md` first before any modifications
- Respect the LOCKED, STABLE, and FLEXIBLE component boundaries
- Verify running processes with `ps aux` before creating anything new
- Follow the exact architecture as documented, not old documentation
- Ask for permission before modifying STABLE components
- Use the 73+ archived files in LOCKED_ARCHIVE only for reference, never restore

❌ **I WILL NOT:**
- Modify LOCKED components (Elite Guard, ZMQ ports, EA, core trading logic)
- Create duplicate processes or files (280+ already exist)
- Trust outdated documentation over ARCHITECTURE.md
- Add new pattern detectors (all 10 are integrated)
- Restore any files from the LOCKED_ARCHIVE_20250914_FINAL directory
- Change trading parameters without explicit approval

🎯 **MY PRIMARY MISSION:**
- Maintain the BITTEN trading system stability
- Follow ARCHITECTURE.md as the single source of truth
- Execute exactly what is requested, nothing more, nothing less
- Keep the system running with 19 trading pairs at 80-89% auto-fire confidence
- Monitor performance with `bitten-report` command

**ARCHITECTURE.md is my North Star. When in doubt, I consult it first.**

**Mission understood. Ready to execute. 🚀**

---

## ARCHIVED WORK HISTORY

### **August 15, 2025 - Fire Pipeline Repair**:

1. **Root Cause Identified**: Test DEALER process (PID 3311456) was intercepting fire commands since August 13
   - Process was masquerading as COMMANDER_DEV_001
   - Caused apparent "FILLED" status without real MT5 execution
   - Commands never reached actual EA

2. **Invalid Volume Fix**: Lot size rounding added to prevent MT5 rejection
   - Issue: `0.09447600000000202` → MT5 invalid volume error
   - Fix: Round to 2 decimal places (`0.09`)
   - Location: `/root/HydraX-v2/enqueue_fire.py:40`

3. **Complete Pipeline Verified**: End-to-end test successful
   - Signal: ELITE_GUARD_GBPUSD_1755223898
   - Position sizing: 5% risk = 0.09 lots  
   - MT5 execution: Ticket 20813351, Fill 1.35357
   - Confirmation: FILLED status in database

### **CURRENT SYSTEM STATUS (August 15, 2025 02:20 UTC)**

**Critical Processes - ALL ONLINE ✅**:
```
command_router        (PM2) - PID 1635948 - 19m uptime - Routes fire commands
confirm_listener      (PM2) - PID 3187572 - 2D uptime  - Receives EA confirmations  
elite_guard          (PM2) - PID 1555442 - 38m uptime - Signal generation
relay_to_telegram    (PM2) - PID 2993303 - 7h uptime  - Telegram broadcasting
zmq_telemetry_bridge (PM2) - PID 3859    - 12h uptime - Market data feed
```

**EA Status**: 
- Identity: COMMANDER_DEV_001 ✅
- User: 7176191872 ✅  
- Last heartbeat: <30 seconds ✅
- Connection: Fresh and active ✅

**Fire Pipeline Status**: 
- IPC Queue: Operational ✅
- Router forwarding: Working ✅  
- EA execution: Working ✅
- Confirmations: Working ✅
- Lot rounding: Fixed ✅

**Ready for Production Trading** 🚀

## 🔍 ELITE GUARD PATTERN DETECTION ARCHITECTURE - VERIFIED AUG 15, 2025

### **ALL PATTERNS BUILT INTO ELITE GUARD - NO SEPARATE PROCESSES**

**File**: `/root/HydraX-v2/elite_guard_with_citadel.py`
**Verification**: Lines 1273-1301 show complete pattern detection pipeline

**✅ INTEGRATED PATTERN DETECTORS (in execution order):**

```python
# 1. LIQUIDITY SWEEP REVERSAL (Line 445)
def detect_liquidity_sweep_reversal(symbol) -> PatternSignal
# Highest priority - 75 base score
# Pattern: "LIQUIDITY_SWEEP_REVERSAL"

# 2. ORDER BLOCK BOUNCE (Line 783)  
def detect_order_block_bounce(symbol) -> PatternSignal
# Pattern: "ORDER_BLOCK_BOUNCE"

# 3. FAIR VALUE GAP FILL (Line 846)
def detect_fair_value_gap_fill(symbol) -> PatternSignal  
# Pattern: "FAIR_VALUE_GAP_FILL"

# 4. VCB BREAKOUT (Line 911)
def detect_vcb_breakout(symbol) -> PatternSignal
# Pattern: "VCB_BREAKOUT" 
# Volatility Compression Breakout

# 5. SWEEP AND RETURN (Line 991) ⚠️ SRL IS BUILT IN ⚠️
def detect_sweep_and_return(symbol) -> PatternSignal
# Pattern: "SWEEP_RETURN"
# This is the SRL (Sweep-Return-Liquidity) pattern
```

### **🚨 CRITICAL - DO NOT START SEPARATE PATTERN PROCESSES**

**⚠️ STANDALONE PATTERN SERVICES - MUST STAY STOPPED ⚠️**

```bash
# These services MUST remain stopped to prevent conflicts:
pm2 stop srl_guard      # ✅ STOPPED - SRL is in Elite Guard
pm2 stop vcb_guard      # ✅ STOPPED - VCB is in Elite Guard  
pm2 stop [any pattern] # ✅ STOPPED - All patterns in Elite Guard
```

**❌ FORBIDDEN PM2 Services:**
- ❌ `srl_guard` - CAUSES PORT CONFLICTS (SRL built into Elite Guard)
- ❌ `vcb_guard` - CAUSES PORT CONFLICTS (VCB built into Elite Guard)
- ❌ Any separate pattern detectors ending in `_guard`

**Why Centralization is Critical**:
- **Port Conflicts**: Multiple processes binding to ZMQ ports 5556/5560
- **Signal Duplication**: Same patterns detected multiple times
- **Resource Waste**: CPU/memory for redundant processing
- **Data Corruption**: Competing access to market data streams

**🎯 RULE**: Only `elite_guard` (PM2 ID 66) should generate signals**

### **PATTERN EXECUTION FLOW (Lines 1273-1304)**

```python
# Elite Guard processes each symbol through ALL patterns:
for symbol in trading_pairs:
    patterns = []
    
    # Run all 5 pattern detectors
    patterns.append(detect_liquidity_sweep_reversal(symbol))
    patterns.append(detect_order_block_bounce(symbol)) 
    patterns.append(detect_fair_value_gap_fill(symbol))
    patterns.append(detect_vcb_breakout(symbol))
    patterns.append(detect_sweep_and_return(symbol))  # ← SRL HERE
    
    # Apply ML confluence scoring
    # Publish qualified signals
```

### **✅ CRITICAL BREAKTHROUGH - AUG 15, 2025 02:44 UTC - FIXED!**

**🎯 ELITE GUARD PATTERN DETECTION FULLY OPERATIONAL**

**Evidence**:
- ✅ Market data flowing: 731,500+ ticks processed  
- ✅ Elite Guard receiving ticks: All symbols active in logs
- ✅ **PATTERN DETECTION ACTIVE**: "Starting pattern scan cycle" logs confirmed
- ✅ **MAIN LOOP EXECUTING**: Main processing loop operational
- ✅ **Signal GENERATION RESTORED**: Pattern scanning in ASIAN session (1 signal/hour max)

**Root Cause IDENTIFIED & FIXED**: `logger.info()` calls causing deadlock/hang throughout Elite Guard
- **Issue**: Every logger.info() call was blocking indefinitely
- **Solution**: Implemented comprehensive logger bypass with print() statements
- **Scope**: Fixed immortal_main_loop(), start() method, and main_loop() hangs

**Fix Applied**: Logger bypass implemented in `/root/HydraX-v2/elite_guard_with_citadel.py`
- **Lines 1619-1624**: Bypassed start() method logger hangs
- **Lines 1406-1412**: Bypassed main_loop() entry logger hangs  
- **Lines 1436-1445**: Bypassed pattern scan cycle logger hangs
- **Result**: Elite Guard now fully operational and scanning for patterns

**Status**: ✅ **OPERATIONAL** - Elite Guard actively generating signals again**

### **August 12, 2025 - Pattern System Integration**

**Additional Fixes & Deployments**:

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

### **August 12, 2025 - Signal Generation Fixes**

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

---

## 📚 REFERENCE DOCUMENTS

### **PRIMARY DOCUMENTATION**
1. **`/root/ARCHITECTURE.md`** - Complete system architecture (SOURCE OF TRUTH)
2. **`/root/HydraX-v2/LOCKED_ARCHIVE_20250914_FINAL/QUARANTINE.md`** - List of archived files
3. **This file (`CLAUDE.md`)** - Operational status and agent instructions

### **SYSTEM FACTS**
- **45+ PM2 Processes**: All defined in ARCHITECTURE.md
- **25+ Database Tables**: Schema in ARCHITECTURE.md
- **10 Patterns Integrated**: All in Elite Guard, no separate processes
- **19 Trading Pairs**: USDCAD and XAGUSD removed Sept 14
- **280+ Python Files**: Many archived, use what exists
- **ForexVPS Only**: No local MT5 operations

---

## 📈 HISTORICAL NOTES

### **XP Economy System Design** (August 15, 2025)

### **DESIGN PHILOSOPHY**
Based on top-tier gaming systems (CoD, Apex Legends, Valorant) adapted for trading:
- Daily engagement rewards
- Skill-based progression
- Consumable power-ups
- Prestige system for hardcore users
- No pay-to-win, only earn-to-win

### **XP EARNING STRUCTURE**
Based on 5-6 trades per day average:

**Core Actions:**
- **Trade to TP**: 100 XP (hit take profit)
- **Trade to SL**: 0 XP (no penalty for stop loss)
- **Early Close**: 50 XP (half reward for manual close)
- **Daily First Trade**: +25 XP bonus
- **Pattern Variety**: +20 XP (different pattern than last trade)

**Streak Bonuses:**
- 3 wins in a row: +50 XP
- 5 wins in a row: +100 XP
- 10 wins in a row: +250 XP

**Daily Challenges (reset at midnight):**
- Trade 3 different pairs: 75 XP
- Execute 5 trades: 100 XP
- Hit 60% win rate: 150 XP

**Expected Daily XP:**
- Casual (2 trades): ~200 XP
- Regular (5 trades): ~500 XP
- Active (10+ trades): ~1000 XP

### **LEVEL PROGRESSION**
50 levels total with exponential curve:
- **Level 1-10**: 500 XP per level (tutorial phase)
- **Level 11-20**: 1000 XP per level (learning phase)
- **Level 21-30**: 2000 XP per level (competent phase)
- **Level 31-40**: 3500 XP per level (expert phase)
- **Level 41-50**: 5000 XP per level (master phase)
- **Prestige**: Reset to Level 1, keep permanent badge

**Time to Max Level:**
- Casual player: 6 months
- Regular player: 3 months
- Hardcore player: 6 weeks

### **XP SHOP - CONSUMABLE ITEMS**

**Tactical Advantages:**
- **Sniper Shot** (500 XP): One trade with 90% confidence threshold bypass
- **Double Down** (1000 XP): Next trade uses 4% risk instead of 2%
- **Rapid Fire** (750 XP): Remove 15-min cooldown between trades for 1 hour
- **Extra Mag** (300 XP): +1 concurrent position slot for 24 hours
- **Radar Pulse** (200 XP): See next 3 signals before they're published

**Defensive Items:**
- **Armor Plate** (600 XP): Next losing trade refunds 50% XP
- **Smoke Screen** (400 XP): Hide your trades from squad feed for 24h
- **Guardian Angel** (1500 XP): Auto-close at 1% profit if trade goes negative

**Cosmetic/Social:**
- **Custom Callsign Change** (FREE for all users, 7-day cooldown)
- **Kill Card Background** (2000 XP): Custom trade victory display
- **Elite Badge** (5000 XP): Special icon in leaderboards
- **Shadow Protocol** (3000 XP): Anonymous mode for 30 days

**Boosts:**
- **XP Boost** (1000 XP): 2x XP for next 10 trades
- **Squad XP Share** (2000 XP): Your squad gets +10% XP for 24h
- **Weekend Warrior** (1500 XP): 1.5x XP on weekends for a month

### **SPECIAL FEATURES BY LEVEL**

**Level 5**: Unlock XP shop
**Level 10**: Custom callsign available
**Level 15**: Trade history stats unlocked
**Level 20**: Squad creation ability
**Level 25**: Advanced analytics access
**Level 30**: Prestige option available
**Level 35**: Elite trader badge
**Level 40**: Master trader recognition
**Level 45**: Legendary status
**Level 50**: APEX achievement

### **PRESS PASS USERS**
- XP resets daily at midnight (trial mode)
- Cannot purchase from XP shop
- Cannot prestige
- Shows "TRIAL" badge instead of level
- Encourages upgrade to maintain progress

### **Implementation Status**
- XP system design documented but not fully implemented
- Database tables exist for tracking
- Integration points defined in webapp

---

**END OF DOCUMENT**

**Remember: ARCHITECTURE.md is the source of truth. This document provides operational context.**