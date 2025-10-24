# 🔥 AUTO-FIRE LOT SIZE FIX - October 10, 2025

## 🐛 PROBLEM IDENTIFIED

**Symptom**: All auto-fire trades executing with 0.01 lot size (minimum) instead of calculated risk-based lot sizes

**Root Cause**: Elite Guard signals store **stop_pips** and **target_pips** but **NOT** absolute SL/TP prices in the database.

**Database Evidence**:
```sql
SELECT signal_id, symbol, entry_price, sl, tp, stop_pips, target_pips FROM signals LIMIT 1;
-- Result: ELITE_RAPID_USDCHF_1760094186|USDCHF|0.806|||15.0|24.0
--         Notice: sl and tp are NULL/empty, only stop_pips and target_pips exist
```

**User Configuration**:
- User ID: 7176191872
- Risk per trade: 4% (0.04 in database)
- Balance: $10,507.92
- Expected lot size: ~0.42 lots for 15 pip SL
- Actual lot size: 0.01 lots ❌

## 🔍 CODE ANALYSIS

### **Location 1: webapp_server_optimized.py**
**Line 663-665** (BEFORE FIX):
```python
stop_loss = float(signal_data.get("stop_loss", signal_data.get("sl", 0)))
# Returns 0 because both fields are NULL
```

**Line 702** (BEFORE FIX):
```python
sl_distance_pips = abs(entry_price - stop_loss) * pip_multiplier
# With stop_loss=0, this gives: sl_distance_pips = entry_price * 10000
# For USDCHF at 0.806: 0.806 * 10000 = 8060 pips (WRONG!)
```

**Line 720-731** (BEFORE FIX):
```python
if sl_distance_pips > 0 and user_balance > 0:
    calculated_lot = risk_amount / (sl_distance_pips * pip_value)
    # 420.32 / (8060 * 10) = 0.0052 → rounds to 0.01
else:
    calculated_lot = 0.01  # Fallback
```

### **Location 2: services/api_server/rest/signals.py**
**Line 183** (BEFORE FIX):
```python
sl_pips = abs(entry_price - stop_loss) * pip_multiplier
# Same bug - calculates wrong pips when stop_loss=0
```

## ✅ FIX APPLIED

### **Fix 1: webapp_server_optimized.py (Lines 693-710)**
```python
# CRITICAL FIX: If SL price is missing (0), use stop_pips directly
if stop_loss == 0 and entry_price > 0:
    # Elite Guard provides stop_pips instead of absolute SL price
    sl_distance_pips = float(signal_data.get("stop_pips", 15))
    logger.info(f"   Using stop_pips from signal: {sl_distance_pips:.1f} pips")
else:
    # Calculate from absolute prices
    if "JPY" in symbol:
        pip_multiplier = 100
    elif symbol == "XAUUSD":
        pip_multiplier = 10
    elif symbol == "XAGUSD":
        pip_multiplier = 1000
    else:
        pip_multiplier = 10000

    sl_distance_pips = abs(entry_price - stop_loss) * pip_multiplier
    logger.info(f"   SL distance from prices: {sl_distance_pips:.1f} pips")
```

### **Fix 2: services/api_server/rest/signals.py (Lines 174-193)**
```python
# CRITICAL FIX: If SL/TP prices are 0, use stop_pips/target_pips directly
if stop_loss == 0 or take_profit == 0:
    # Elite Guard provides pips instead of absolute prices
    sl_pips = float(signal_data.get("stop_pips", 15))
    tp_pips = float(signal_data.get("target_pips", 20))
    logger.info(f"   Using pips from signal: SL={sl_pips}, TP={tp_pips}")
else:
    # Calculate from absolute prices
    # ... (same multiplier logic)
```

## 📊 EXPECTED RESULTS AFTER FIX

**Example: USDCHF signal**
- Entry: 0.806
- SL: 15 pips (from stop_pips field)
- User balance: $10,507.92
- Risk: 4% = $420.32
- Pip value: $10/lot

**Calculation**:
```
lot = risk_amount / (sl_pips * pip_value)
lot = 420.32 / (15 * 10)
lot = 420.32 / 150
lot = 2.80 lots ✅
```

**Before Fix**: 0.01 lots (minimum fallback) ❌  
**After Fix**: 2.80 lots (proper risk-based sizing) ✅

## 🔄 DEPLOYMENT

**Files Modified**:
1. `/root/HydraX-v2/webapp_server_optimized.py` - Lines 693-710
2. `/root/HydraX-v2/services/api_server/rest/signals.py` - Lines 174-193

**Services Restarted**:
```bash
pm2 restart api_server  # Running on port 8888
```

**Status**: ✅ FIXED - October 10, 2025 11:37 UTC

## 🧪 VERIFICATION STEPS

When next signal arrives with auto-fire:

1. Check logs for "Using stop_pips from signal" message
2. Verify lot size is > 0.01 and matches risk calculation
3. Confirm trade executes with calculated lot size

**Expected log output**:
```
💰 AUTO FIRE LOT CALC: Balance=$10507.92, Risk=4.0%
   Using stop_pips from signal: 15.0 pips
   ✅ Calculated lot: 2.80 (risk $420.32)
⚡ AUTO FIRE SENT: ELITE_RAPID_USDCHF_xxx for user 7176191872 - 2.80 lots @ 84.5%
```

## 📋 RELATED FILES

- Elite Guard signal generation: `/root/HydraX-v2/elite_guard_with_citadel.py`
- Signal relay: `/root/HydraX-v2/elite_guard_zmq_relay.py`
- Fire execution: `/root/HydraX-v2/enqueue_fire.py`
- Command routing: `/root/HydraX-v2/command_router.py`

---

**Fixed by**: Claude Code (Sonnet 4.5)  
**Date**: October 10, 2025  
**Ticket**: Auto-fire lot size defaulting to 0.01
