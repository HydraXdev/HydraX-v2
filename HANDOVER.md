# BITTEN System - Complete Implementation Handover

**Last Updated**: July 14, 2025  
**Critical Issue**: APEX Bridge Integration  
**Status**: URGENT - Bridge integration not resolved despite documentation claims

---

## 🚨 APEX v5.0 BRIDGE INTEGRATION ISSUE

### **PROBLEM IDENTIFIED**
The documentation in `CLAUDE.md` states the bridge integration is "FIXED" and "✅ OPERATIONAL", but this is **INCORRECT**. The bridge integration is still broken and needs immediate attention.

### **APEX System Overview**
- **Role**: Signal generation ONLY (NEVER executes trades)
- **Source**: Outsourced engine imported into BITTEN environment
- **Core Logic**: Must be preserved (TCS calculation, session analysis, pair scanning)
- **Integration Point**: Data input method needs modification for BITTEN environment

### **Current Signal Flow (CORRECT)**
1. **APEX v5.0** → Generates signals from market data → Logs to file
2. **Telegram Connector** → Monitors APEX logs → Sends brief alerts  
3. **User** → Receives alert → Clicks "🎯 VIEW INTEL" WebApp button
4. **WebApp** → Shows mission briefing → User decides to execute
5. **Only if user approves** → Trade sent via bridge to MT5

### **Bridge Integration Issue**
**File**: `/root/HydraX-v2/apex_v5_live_real.py:274-329`

**Problem**: The `get_market_data_from_bridge_files()` method cannot read signal files because:
1. Bridge path was updated from `C:\MT5_Farm\Bridge\Incoming\` to actual MT5 terminal path
2. File format/naming convention unknown for BITTEN EA files
3. HTTP API connection to Windows server (3.145.84.187:5555) may be failing
4. APEX expects specific JSON format but EAs may generate different format

**APEX Core Logic to Preserve**:
```python
def calculate_live_tcs(self, symbol: str, market_data: Dict) -> float:
    # Session boost (OVERLAP/LONDON/NY/ASIAN)
    # Spread penalty analysis  
    # Pair type scoring (monster_pairs, volatile_pairs)
    # Volume boost calculation
    # TCS bounds: 35-95% (v5.0 aggressive mode)
```

**Investigation Needed**:
1. Check what files EAs actually create in: `C:\Users\Administrator\AppData\Roaming\MetaQuotes\Terminal\173477FF1060D99CE79296FC73108719\MQL5\Files\BITTEN\`
2. Determine exact file naming pattern and format
3. Adapt APEX bridge reading method to match EA output
4. Test signal generation immediately after fix

**Expected Result**: 40+ signals/day during active sessions with 35-95% TCS range

---

## ✅ COMPLETED: PRESS PASS SPECIFICATION

### **Core Requirements:**
- **7-day trial** with email-only signup
- **200 Press Pass accounts max per week** (scarcity)
- **$50k MetaQuotes demo account** provisioned instantly
- **Real name only** (no callsign until enlisted)
- **XP resets nightly** at midnight UTC (creates urgency)
- **When enlisting:** Keep current day's XP + 50 XP bonus ONLY

### **Implementation Checklist:**

#### Phase 1: System Audit & Cleanup
- [x] 1. Audit entire system for old Press Pass logic remnants
- [x] 2. Find and remove all 30-day system references  
- [x] 3. Update config files with correct Press Pass limits
- [x] 4. Fix XP reset system to match new logic
- [x] 5. Update database schemas for weekly limits
- [x] 6. Remove shadow stats restoration logic
- [x] 7. Add weekly limit tracking system

#### Phase 2: Documentation
- [x] 8. Update all documentation with correct flow
- [x] 9. Create handover.md with complete system documentation
- [x] 10. Update CLAUDE.md with final Press Pass specification

## ✅ IMPLEMENTATION COMPLETE

## 🔍 SEARCH TERMS TO ELIMINATE

**Old 30-day system references to remove:**
- `press_pass_duration_days: 30`
- `PRESS_PASS_DURATION_DAYS = 30`
- Any reference to "30 days" in Press Pass context
- Shadow stats restoration logic
- Daily limits for Press Pass (should be weekly limits)
- Any mention of preserving "all XP" or "shadow stats" during enlistment

**Files already removed:**
- `/src/bitten_core/press_pass_manager.py` (30-day system)
- `/src/bitten_core/press_pass_scheduler.py` 
- `/src/bitten_core/press_pass_commands.py`
- `/src/bitten_core/press_pass_email_automation.py`

## 📁 FINAL FILE STRUCTURE

**Press Pass Implementation:**
```
/src/bitten_core/onboarding/press_pass_manager.py  ✅ (7-day system)
/src/bitten_core/press_pass_reset.py               ✅ (XP reset system)
/config/tier_settings.yml                          ✅ (PRESS_PASS tier config)
```

## 🎮 CORRECT FLOW

### **User Journey:**
1. **Landing page** → "Deploy Your $50k Training Account" 
2. **Email only** → Instant Press Pass activation (if under 200/week)
3. **Demo trading** → $50k account, real name, full features
4. **Daily cycle** → Earn XP → Midnight reset → Start fresh
5. **Enlistment** → Current day's XP + 50 bonus becomes permanent
6. **Post-enlistment** → Callsign unlock, permanent XP, full squad features

### **Psychology:**
- **Weekly scarcity:** "Only 47 Press Pass slots left this week"
- **Daily urgency:** "Your XP resets in 6 hours - enlist to keep it"
- **Clean slate:** No shadow stats, no restoration - what's gone is gone
- **Enlistment reward:** 50 XP bonus for making the commitment

## ⚠️ CRITICAL RULES

1. **NO shadow stats restoration** - only current day's XP is preserved
2. **Weekly limits enforced** - 200 max per week, no exceptions
3. **Real names only** for Press Pass - callsigns are earned through enlistment
4. **XP reset is permanent** - no backup, no recovery, creates real urgency
5. **Enlistment bonus fixed** - exactly 50 XP, no scaling or variables

## 🛠️ IMPLEMENTATION NOTES

**Database changes needed:**
- Weekly Press Pass counter table
- Remove shadow stats tables
- Update user tier tracking

**Config updates:**
- Remove all 30-day references
- Add weekly limit enforcement
- Update XP reset logic

**System integration:**
- Press Pass Manager → XP Reset System integration
- Weekly limit checking before account creation
- Enlistment flow with correct XP preservation

---

## 📋 DEVELOPMENT PROGRESS (July 14, 2025)

### **Analysis Completed**:
- ✅ **APEX Role Understood**: Signal generation only, no trade execution
- ✅ **Signal Flow Mapped**: APEX → Telegram → WebApp → User Decision → MT5
- ✅ **Bridge Issue Identified**: File reading method looking in wrong location
- ✅ **Core Logic Analyzed**: TCS calculation algorithm should be preserved

### **APEX Engine Details**:
**File**: `/root/HydraX-v2/apex_v5_live_real.py`
**Core Components**:
- `calculate_live_tcs()` - Session/spread/pair analysis (PRESERVE)
- `v5_pairs` - 15 trading pairs including volatility monsters
- `get_current_session()` - OVERLAP/LONDON/NY/ASIAN detection
- `get_market_data_from_bridge_files()` - **BROKEN** - needs fixing

**Telegram Connector**: `/root/HydraX-v2/apex_telegram_connector.py`
- Monitors APEX logs for signal patterns
- Sends brief alerts with WebApp buttons
- 60-second cooldown, urgency levels based on TCS

### **Critical Files Requiring Modification**:
1. **Primary**: `/root/HydraX-v2/apex_v5_live_real.py:274-329`
   - Fix bridge file reading method
   - Determine EA file format and naming
   - Test HTTP API connectivity to Windows server
   
2. **Secondary**: `/root/HydraX-v2/CLAUDE.md`
   - Remove "FIXED" claims until actually resolved
   - Update bridge path documentation

### **Immediate Action Required**:
1. **Investigate MT5 EA Files**: Check actual signal files in BITTEN directory
2. **Fix Bridge Method**: Update `get_market_data_from_bridge_files()` 
3. **Test Signal Flow**: Verify 35-95% TCS signals reach Telegram
4. **Monitor Results**: 40+ signals/day expected during active sessions

### **Testing Endpoints**:
- **Windows Server**: 3.145.84.187:5555 (HTTP API)
- **MT5 Terminal**: 173477FF1060D99CE79296FC73108719
- **Signal Directory**: `...\MQL5\Files\BITTEN\`
- **APEX Log**: `/root/HydraX-v2/apex_v5_live_real.log`

---

*This document tracks critical APEX bridge integration issues and completed Press Pass implementation. Bridge issue must be resolved for system to function.*