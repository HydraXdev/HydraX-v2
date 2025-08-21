# BITTEN PRODUCTION SYSTEM - ACTUAL STATE

**Last Updated**: August 19, 2025 23:25 UTC  
**Agent**: Claude Code (Default Model)  
**Session**: AI Excellence System Deployed - Comprehensive Tracking Active

## 🎯 AI EXCELLENCE SYSTEM DEPLOYED - AUGUST 19, 2025 🎯

### **COMPREHENSIVE UPGRADES IMPLEMENTED TODAY:**

#### **1. EXPECTANCY-BASED PATTERN ELIMINATION (Not Just Win Rate)**
- **Location**: `/root/HydraX-v2/expectancy_calculator.py`
- **Formula**: EV = (Win% × AvgWin) - (Loss% × AvgLoss)
- **Protection**: Keeps profitable low-win-rate patterns (e.g., 35% win at 3:1 RR = +0.40 EV)
- **Safety Zone**: ±5% of breakeven prevents variance-based elimination
- **Rolling Windows**: 50-100 signal analysis prevents hasty decisions

#### **2. TWO-STAGE QUARANTINE SYSTEM**
- **Location**: `/root/HydraX-v2/pattern_quarantine_manager.py`
- **Stage 1**: QUARANTINE - Demo-only mode after 50 signals with negative EV
- **Stage 2**: KILL - Full elimination after 100 signals if still negative
- **Recovery Path**: Patterns can return from quarantine if performance improves
- **Status File**: `pattern_quarantine_status.json`

#### **3. CONVERGENCE TRACKER (Multi-Pattern Boost)**
- **Location**: `/root/HydraX-v2/convergence_tracker.py`
- **Function**: Detects when 2+ patterns align on same pair within 60 seconds
- **Boost**: +10% confidence per additional pattern
- **Output**: `convergence_signals.jsonl`
- **Impact**: High-conviction trades often have the highest edge

#### **4. DYNAMIC OUTCOME RESOLUTION (ATR-Based)**
- **Location**: `/root/HydraX-v2/dynamic_outcome_tracker.py`
- **Change**: Replaces fixed 60min checks with volatility-based horizons
- **Tracking**: Until TP/SL hit OR 3x expected time (max 4 hours)
- **Benefit**: Prevents misclassifying slow-burn winners as failures

#### **5. CONFIDENCE CALIBRATION LAYER**
- **Location**: `/root/HydraX-v2/confidence_calibrator.py`
- **Function**: Audits if 80% confidence actually wins 80% of time
- **Buckets**: 70-75%, 75-80%, 80-85%, 85-90%
- **Adjustment**: If 80% signals only win 62%, adjusts future scores down by 18%
- **Output**: `confidence_calibration.json`

#### **6. MARKET REGIME AWARENESS**
- **Location**: `/root/HydraX-v2/regime_analyzer.py`
- **Tags**: TREND/RANGE (ADX), HIGH/LOW_VOL (ATR), Session
- **Analysis**: Expectancy calculated PER REGIME not globally
- **Insight**: Pattern might fail in Asian range but print in London trend
- **Output**: `regime_performance.json`

#### **7. ADAPTIVE REVIEW SCHEDULER**
- **Location**: `/root/HydraX-v2/adaptive_review_scheduler.py`
- **Fast Patterns**: Review every 24-48 hours (5+ signals/day)
- **Medium Patterns**: Review every 3-5 days (1-5 signals/day)
- **Slow Patterns**: Review weekly (<1 signal/day)
- **Output**: `review_schedule.json`

#### **8. COMPREHENSIVE TRACKING SYSTEM**
- **Location**: `/root/HydraX-v2/comprehensive_signal_tracker.py`
- **Tracks**: EVERY signal at 70%+ confidence (not just fired ones)
- **Logging**: `comprehensive_tracking.jsonl`
- **Counterfactual**: Records what WOULD have happened if traded
- **Dashboard**: Real-time HTML on port 8890

#### **9. MASTER CONTROL SYSTEM**
- **Location**: `/root/HydraX-v2/pattern_elimination_master.py`
- **Function**: Coordinates all 8 services seamlessly
- **Features**: Real-time monitoring, integrated reports, graceful shutdown
- **Status**: Running and analyzing patterns continuously

### **THRESHOLD ADJUSTMENTS**
- **Signal Generation**: Lowered to 70% (from 75%) to collect more data
- **Auto-Fire**: Raised to 90% (from 80%) for safety during testing
- **Impact**: Capturing more signals for analysis while keeping auto-execution conservative

### **EARLY PERFORMANCE INSIGHTS (Limited Data)**
- **ORDER_BLOCK_BOUNCE**: 100% win rate, +37.5 EV (2 signals)
- **VCB_BREAKOUT**: 100% win rate, +45.0 EV (1 signal)
- **LIQUIDITY_SWEEP_REVERSAL**: 50% win rate, +7.5 EV (2 signals)
- **FAIR_VALUE_GAP_FILL**: 0% win rate, -25.0 EV (1 signal - quarantine candidate)

## 🚀 ML INTEGRATION COMPLETE - AUGUST 15, 2025 END OF DAY 🚀

### **MAJOR CHANGES IMPLEMENTED PREVIOUSLY:**

#### **1. ML Filter Integrated Directly Into Elite Guard**
- **Location**: `/root/HydraX-v2/elite_guard_with_citadel.py`
- **Method**: `apply_ml_filter()` at line 1545
- **Function**: Filters every pattern through tiered system before publishing
- **Performance Tracking**: `update_performance_outcome()` at line 1545

#### **2. Tiered Signal System Active**
```python
TIER_1_AUTO_FIRE: {
    EURUSD_VCB_BREAKOUT: 80% threshold (lowered from 85%)
    GBPUSD_VCB_BREAKOUT: 80% threshold (lowered from 87%)
    Max hourly: 3 for EURUSD, 2 for GBPUSD
}
TIER_2_TESTING: Track only, no auto-fire
TIER_3_PROBATION: ASIAN session, XAUUSD (high thresholds)
```

#### **3. Sunday Testing Configuration**
- **Auto-Fire Threshold**: 80% (lowered from 85%)
- **Pattern Quality Filter**: 72% (lowered from 78%)
- **Risk/Reward Ratio**: 1:1.25 (changed from 1:1 for quick profits)
- **Target Pairs**: EURUSD, GBPUSD only (proven winners)

#### **4. Complete Tracking System (NO TIMEOUTS)**
- **Signal Outcome Monitor**: Enhanced to track EVERY signal to TP/SL
- **ML Feedback Loop**: Outcomes automatically update performance history
- **Tracking Files**:
  - `/root/HydraX-v2/truth_log.jsonl` - All signals
  - `/root/HydraX-v2/signal_outcomes.jsonl` - Outcomes
  - `/root/HydraX-v2/ml_performance_tracking.jsonl` - ML data

#### **5. Performance Features**
- Auto-disables patterns below 40% win rate after 10 trades
- Auto-promotes patterns above 70% win rate after 20 trades
- Tracks runtime duration, max favorable/adverse moves
- Full data logging: pattern, confidence, session, R:R, outcome

### **MONDAY EXPANSION PLAN:**
- Currently limited to EURUSD/GBPUSD for testing
- Monday: Can add USDJPY, EURJPY, USDCAD to Tier 2
- Monitor win rates per pair/pattern combo
- ML system will auto-optimize based on results

## 🎯 COMPLETE FIRE PIPELINE ARCHITECTURE - AUGUST 15, 2025 🎯

### **VERIFIED WORKING END-TO-END FLOW**

```
[Signal Generation] → [Database] → [Webapp/Engine] → [Fire Command] → [IPC Queue] → [Command Router] → [EA] → [MT5] → [Confirmation] → [Database Update]
```

**Last Successful Test**: August 15, 2025 02:18 UTC
- **Signal**: ELITE_GUARD_GBPUSD_1755223898 (SELL)
- **Fire ID**: ELITE_GUARD_GBPUSD_1755223898
- **MT5 Ticket**: 20813351
- **Fill Price**: 1.35357
- **Lot Size**: 0.09 (5% risk, properly rounded)
- **Status**: FILLED ✅

### **🔧 CRITICAL FIX APPLIED**

**Issue**: Invalid volume format causing MT5 trade failures
**Root Cause**: Lot sizes like `0.09447600000000202` invalid for MT5
**Fix**: Added lot size rounding in `/root/HydraX-v2/enqueue_fire.py:40`
```python
# Round lot size to 2 decimal places for MT5 compatibility
lot = round(lot, 2)
```

### **⚡ PRODUCTION EA ARCHITECTURE**

**EA**: `/root/HydraX-v2/BITTEN_Universal_EA_v2.05_PRODUCTION.mq5`
- **Connection**: ZMQ DEALER socket with identity "COMMANDER_DEV_001"
- **Server**: tcp://134.199.204.67:5555 (command router)
- **Heartbeat**: Every 30 seconds
- **Confirmation**: Port 5558 with fire_id tracking

**Fire Command Format (EXACT):**
```json
{
  "type": "fire",
  "fire_id": "ELITE_GUARD_GBPUSD_1755223898",
  "target_uuid": "COMMANDER_DEV_001", 
  "symbol": "GBPUSD",
  "direction": "SELL",
  "entry": 1.35386,
  "sl": 1.35636,
  "tp": 1.34886,
  "lot": 0.09,
  "user_id": "7176191872"
}
```

## 🚨 TROUBLESHOOTING GUIDE FOR NEXT AGENT 🚨

### **QUICK HEALTH CHECK COMMANDS**

```bash
# 1. Check all critical processes
pm2 list | grep -E "command_router|elite_guard|confirm_listener|webapp"

# 2. Check ZMQ port bindings
ss -tulpen | grep -E ":(5555|5556|5557|5558|8888)"

# 3. Check EA connection freshness 
sqlite3 /root/HydraX-v2/bitten.db "SELECT target_uuid, user_id, (strftime('%s','now') - last_seen) AS age_seconds FROM ea_instances WHERE target_uuid = 'COMMANDER_DEV_001';"

# 4. Check recent fire executions
sqlite3 /root/HydraX-v2/bitten.db "SELECT fire_id, status, ticket, price FROM fires ORDER BY created_at DESC LIMIT 5;"

# 5. Test fire command pipeline
python3 /root/HydraX-v2/test_webapp_fire_path.py
```

### **COMMON ISSUES & FIXES**

#### **🔥 Fire Commands Not Reaching MT5**

**Symptoms**: 
- Fire status = "SENT" (not "FILLED")
- No MT5 ticket number
- Error code 4756

**Debug Steps**:
1. **Check EA Connection**: Age should be <120 seconds
2. **Check Router Logs**: `pm2 logs command_router --lines 10`
3. **Check for Test Processes**: Look for old DEALER test processes intercepting commands
   ```bash
   ps aux | grep -E "test.*dealer|dealer.*test"
   # Kill any found: kill [PID]
   ```

#### **🎯 Invalid Volume Errors**

**Symptoms**:
- Fire status = "FAILED" 
- Ticket = 0, Price = 0
- EA logs show volume errors

**Root Cause**: Lot sizes not properly rounded (e.g., `0.09447600000000202`)
**Fix**: Already applied in `/root/HydraX-v2/enqueue_fire.py:40`

#### **📡 Signal Generation Issues**

**Symptoms**: 
- No new signals in database
- Empty signal lists in webapp

**Debug Steps**:
1. **Check Elite Guard**: `pm2 logs elite_guard --lines 10`
2. **Check Market Data**: `pm2 logs zmq_telemetry_bridge --lines 10`
3. **Check Signal Database**: 
   ```sql
   SELECT signal_id, symbol, created_at FROM signals WHERE created_at > strftime('%s', 'now', '-1 hour');
   ```

### **CRITICAL PROCESS DEPENDENCIES**

**Required for Fire Execution**:
1. ✅ `command_router` (PM2) - Routes commands to EA
2. ✅ `confirm_listener` (PM2) - Receives EA confirmations  
3. ✅ EA process - Must be connected with fresh heartbeat
4. ✅ `enqueue_fire.py` - Must have lot rounding fix

**Required for Signal Generation**:
1. ✅ `elite_guard` (PM2) - Generates SMC signals
2. ✅ `zmq_telemetry_bridge` (PM2) - Market data feed
3. ✅ `relay_to_telegram` (PM2) - Signal broadcasting

### **ARCHITECTURE VERIFICATION FLOW**

If fire pipeline broken, test each stage:

```python
# Stage 1: Test IPC Queue
python3 /root/HydraX-v2/test_fire_queue.py

# Stage 2: Check Router Processing  
pm2 logs command_router --lines 5

# Stage 3: Check EA Response
pm2 logs confirm_listener --lines 5

# Stage 4: Check Database Update
sqlite3 /root/HydraX-v2/bitten.db "SELECT fire_id, status, ticket FROM fires ORDER BY created_at DESC LIMIT 1;"
```

### **EA CONNECTION TROUBLESHOOTING**

**EA Identity**: Must be exactly "COMMANDER_DEV_001"
**User Mapping**: Must map to user "7176191872"  
**Heartbeat**: Every 30 seconds via ZMQ DEALER to port 5555
**Confirmation**: Sends results to port 5558

**If EA appears disconnected**:
1. Check if test processes are intercepting (kill them)
2. Verify EA is running on correct MT5 terminal
3. Check ZMQ library availability in MT5
4. Restart command_router if identity mapping broken

## WORK COMPLETED - AUGUST 15, 2025

### **Critical Fire Pipeline Repair**:

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

---

## 🎮 XP ECONOMY SYSTEM PLAN - AUGUST 15, 2025

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

### **IMPLEMENTATION NOTES**
- All XP stored in database with transaction log
- Shop purchases logged with expiry timestamps
- Consumables checked before each trade execution
- Daily challenges generated algorithmically
- Streak tracking per user in real-time

### **ANTI-ABUSE MEASURES**
- Max 20 trades per day count for XP
- Minimum trade duration 60 seconds for XP
- Same pair within 5 minutes = no variety bonus
- Suspicious patterns trigger manual review