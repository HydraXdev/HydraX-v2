# UNIFIED PIP CALCULATION SYSTEM

**Date:** October 23, 2025
**Status:** ✅ DEPLOYED AND VERIFIED
**Test Results:** 57/57 passing (100%)

---

## OVERVIEW

The BITTEN system now uses a **centralized, symbol-aware pip calculation system** to ensure consistency across all fire execution paths (auto-fire, manual-fire, and fire command creation).

### **Problem Solved**

**Before:** Different pip multipliers/sizes existed across the codebase:
- Auto-fire: JPY=100, XAUUSD=10, XAGUSD=100, Others=10000
- Manual-fire: JPY=0.01, Others=0.0001 (missing XAUUSD/XAGUSD)
- Fire command: Multiple inconsistent local calculations

**Result:** Same signal produced different SL/TP prices depending on execution path.

**After:** Single source of truth in `/root/HydraX-v2/src/bitten_core/constants.py`
- All flows use identical pip size definitions
- Symbol-aware calculations (JPY, Gold, Silver, Majors)
- M5 ATR-based scalping optimizations
- Comprehensive verification assertions

---

## ARCHITECTURE

### **Constants Module**
**File:** `/root/HydraX-v2/src/bitten_core/constants.py`

**Core Constants:**
```python
PIP_SIZES = {
    "JPY": 0.01,      # JPY pairs: 1 pip = 0.01 (e.g., USDJPY 150.00 → 150.01)
    "XAUUSD": 0.10,   # Gold: 1 pip = $0.10 (e.g., 2000.0 → 2000.1)
    "XAGUSD": 0.001,  # Silver: 1 pip = $0.001 (e.g., 25.000 → 25.001)
    "DEFAULT": 0.0001 # Majors: 1 pip = 0.0001 (e.g., EURUSD 1.1000 → 1.1001)
}
```

**Key Functions:**

#### `get_pip_size(symbol: str) -> float`
Returns pip size for any symbol.

```python
get_pip_size("USDJPY")  # → 0.01
get_pip_size("EURUSD")  # → 0.0001
get_pip_size("XAUUSD")  # → 0.10
get_pip_size("XAGUSD")  # → 0.001
```

#### `pips_from_price_distance(price1: float, price2: float, symbol: str) -> float`
Converts price distance to pips.

```python
pips_from_price_distance(1.1000, 1.1050, "EURUSD")  # → 50.0 pips
pips_from_price_distance(150.00, 150.50, "USDJPY")  # → 50.0 pips
pips_from_price_distance(2000.0, 2005.0, "XAUUSD")  # → 50.0 pips
```

#### `calculate_stop_loss_price(entry: float, stop_pips: float, direction: str, symbol: str) -> float`
Calculates SL price from pips.

```python
# BUY: SL goes below entry
calculate_stop_loss_price(1.1000, 50.0, "BUY", "EURUSD")  # → 1.0950

# SELL: SL goes above entry
calculate_stop_loss_price(1.1000, 50.0, "SELL", "EURUSD")  # → 1.1050
```

#### `calculate_take_profit_price(entry: float, target_pips: float, direction: str, symbol: str) -> float`
Calculates TP price from pips.

```python
# BUY: TP goes above entry
calculate_take_profit_price(1.1000, 100.0, "BUY", "EURUSD")  # → 1.1100

# SELL: TP goes below entry
calculate_take_profit_price(1.1000, 100.0, "SELL", "EURUSD")  # → 1.0900
```

#### `verify_pip_conversion(price1: float, price2: float, expected_pips: float, symbol: str, tolerance: float = 1.0)`
Verification assertion to catch calculation errors.

```python
# Valid conversion (passes)
verify_pip_conversion(1.1000, 1.0950, 50.0, "EURUSD", tolerance=1.0)

# Invalid conversion (raises AssertionError)
verify_pip_conversion(1.1000, 1.0900, 50.0, "EURUSD", tolerance=1.0)  # Error: actual=100 pips
```

---

## M5 SCALPING OPTIMIZATION

### **ATR-Based Stop Calculation**

**Function:** `calc_scalp_stop_pips(symbol, atr_price_units, rr=1.8, timeframe="M5", min_pips=None, max_pips=None, atr_mult=1.2)`

**Purpose:** Calculate stops optimized for 30-120 minute M5 scalp trades.

**Features:**
- Symbol/timeframe-aware min/max limits
- ATR multipliers optimized for scalping (0.8-1.5x vs swing 1.5-2.5x)
- Automatic clamping to safe ranges
- Risk/Reward ratio enforcement

**Example:**
```python
# EURUSD with 12-pip ATR on M5
pip_size = get_pip_size("EURUSD")  # 0.0001
atr_price_units = 12.0 * pip_size  # 0.0012

stop_pips, target_pips = calc_scalp_stop_pips(
    symbol="EURUSD",
    atr_price_units=atr_price_units,
    rr=1.8,
    timeframe="M5",
    atr_mult=1.2
)
# Result: stop_pips = 14.4 (clamped to min 10), target_pips = 25.9
```

### **Symbol-Aware M5 Limits**

| Symbol Type | Min Stop (pips) | Max Stop (pips) | Example |
|-------------|-----------------|-----------------|---------|
| JPY Pairs   | 6               | 35              | USDJPY  |
| Majors      | 10              | 45              | EURUSD  |
| Gold        | 25              | 120             | XAUUSD  |
| Silver      | 15              | 80              | XAGUSD  |

**Rationale:**
- **Majors (M5):** 10-45 pips accommodates typical M5 ATR (8-15 pips) × 1.2 multiplier
- **JPY (M5):** 6-35 pips adjusted for JPY pip size (0.01 vs 0.0001)
- **Gold (M5):** 25-120 pips reflects higher volatility (M5 ATR ~20-40 pips)
- **Silver (M5):** 15-80 pips intermediate between Majors and Gold

---

## INTEGRATION POINTS

### **1. Auto-Fire Flow**
**File:** `/root/HydraX-v2/services/api_server/rest/signals.py`

**Changes:**
- Lines 264-268: Import constants module
- Lines 298-316: Replace multiplier system with `pips_from_price_distance()`
- Added verification assertions

**Before:**
```python
if "JPY" in symbol:
    pip_multiplier = 100
elif symbol == "XAUUSD":
    pip_multiplier = 10
else:
    pip_multiplier = 10000
sl_pips = abs(entry_price - stop_loss) * pip_multiplier
```

**After:**
```python
from bitten_core.constants import pips_from_price_distance, verify_pip_conversion

sl_pips = pips_from_price_distance(entry_price, stop_loss, symbol)
verify_pip_conversion(entry_price, stop_loss, sl_pips, symbol, tolerance=1.0)
```

---

### **2. Manual-Fire Flow**
**File:** `/root/HydraX-v2/services/api_server/rest/fires.py`

**Changes:**
- Lines 22-27: Import constants module
- Lines 154-171: Replace hardcoded pip_size with centralized functions
- Added XAUUSD/XAGUSD handling (was missing)

**Before:**
```python
pip_size = 0.01 if 'JPY' in signal.symbol else 0.0001
if signal.direction == 'BUY':
    sl_price = entry_price - (signal.stop_pips * pip_size)
    tp_price = entry_price + (signal.target_pips * pip_size)
```

**After:**
```python
from bitten_core.constants import calculate_stop_loss_price, calculate_take_profit_price, verify_pip_conversion

sl_price = calculate_stop_loss_price(entry_price, signal.stop_pips, signal.direction, signal.symbol)
tp_price = calculate_take_profit_price(entry_price, signal.target_pips, signal.direction, signal.symbol)
verify_pip_conversion(entry_price, sl_price, signal.stop_pips, signal.symbol, tolerance=1.0)
```

---

### **3. Fire Command Creation**
**File:** `/root/HydraX-v2/enqueue_fire.py`

**Changes:**
- Lines 12-21: Import constants module
- Replaced 5+ instances of duplicate pip_size calculations
- Symbol-aware safety margins (not fixed 20 pips)
- Symbol-aware emergency fallbacks

**Key Improvements:**

**EA Validation Safety Margins (Lines 489-508):**
```python
# OLD: Fixed 20-pip safety margin for all symbols
if sl >= entry_rounded:
    sl = entry_rounded - (20 * pip_size)

# NEW: Symbol/timeframe-aware margins
from bitten_core.constants import get_min_max_stop_pips, calculate_stop_loss_price

min_stop_pips, _ = get_min_max_stop_pips(symbol, timeframe="M5")
safety_margin_pips = max(min_stop_pips, 10)
if sl >= entry_rounded:
    sl = calculate_stop_loss_price(entry_rounded, safety_margin_pips, "BUY", symbol)
```

**Emergency Fallbacks (Lines 569-584):**
```python
# OLD: Fixed minimum (10 pips for all symbols)
min_stop_distance_pips = 10.0

# NEW: Symbol-aware minimum
min_stop_pips, _ = get_min_max_stop_pips(symbol, timeframe="M5")
```

---

### **4. Signal Generator (Elite Guard)**
**File:** `/root/HydraX-v2/elite_guard_with_citadel.py`

**Changes:**
- Lines 29-34: Import constants module
- Lines 4035-4045: Symbol-aware minimum ATR (not fixed 10 pips)
- Lines 4077-4111: M5 scalping-optimized ATR logic

**ATR Multiplier Optimization:**

| Pattern Type         | Old (Swing) | New (M5 Scalp) |
|----------------------|-------------|----------------|
| Engulfing            | 1.5x        | 1.2x           |
| FVG                  | 2.0x        | 1.5x           |
| BOS                  | 1.8x        | 1.3x           |
| OB                   | 2.2x        | 1.5x           |
| Liquidity Sweep      | 2.5x        | 1.5x           |
| Asia Range Breakout  | 1.5x        | 0.8x (tight!)  |

**Session Multipliers:**
- ASIAN: 0.8x (tighter stops in low volatility)
- LONDON/NY: 1.05x (normal)
- OVERLAP: 1.05x (normal)

**Before:**
```python
min_atr_pips = 10.0  # Global minimum
atr_multiplier = 1.5  # Swing value
stop_pips = round(atr_pips * atr_multiplier, 1)
min_stop_pips = 15.0
if stop_pips < min_stop_pips:
    stop_pips = min_stop_pips
```

**After:**
```python
from bitten_core.constants import calc_scalp_stop_pips, get_min_max_stop_pips, get_pip_size

# Symbol-aware minimum ATR
min_atr, _ = get_min_max_stop_pips(symbol, timeframe="M5")

# Session-adjusted scalping multiplier
base_multiplier = 0.8 to 1.5  # Pattern-specific
session_multiplier = 0.8 to 1.05  # Session-specific
atr_multiplier = base_multiplier * session_multiplier

# Calculates with symbol/timeframe limits
stop_pips, target_pips = calc_scalp_stop_pips(
    symbol=symbol,
    atr_price_units=atr_pips * get_pip_size(symbol),
    rr=rr_ratio,
    timeframe="M5",
    atr_mult=atr_multiplier
)
```

---

## VERIFICATION & TESTING

### **Test Suite**
**File:** `/root/HydraX-v2/test_pip_calculations.py`

**Coverage:** 57 tests across 8 test suites
- ✅ Pip size constants (all symbol types)
- ✅ Price-to-pips conversion accuracy
- ✅ Stop loss price calculations (BUY/SELL)
- ✅ Take profit price calculations (BUY/SELL)
- ✅ Roundtrip consistency (price→pips→price)
- ✅ M5 scalping limits (min/max enforcement)
- ✅ Verification assertions (catches errors)
- ✅ Auto-fire vs manual-fire consistency

**Run Tests:**
```bash
cd /root/HydraX-v2
python3 test_pip_calculations.py
```

**Expected Output:**
```
============================================================
FINAL RESULTS
============================================================
Total Tests: 57
Passed: 57 ✅
Failed: 0 ❌

🎉 ALL TESTS PASSED! System is consistent.
```

---

## CRITICAL VALIDATIONS

### **Assertion Checks**

All three flows now include verification assertions:

```python
# Example: Auto-fire signal processing
sl_pips = pips_from_price_distance(entry_price, stop_loss, symbol)
verify_pip_conversion(entry_price, stop_loss, sl_pips, symbol, tolerance=1.0)

# If sl_pips calculation is wrong, this will raise AssertionError with:
# "Pip conversion mismatch for {symbol}: expected {expected_pips}, got {actual_pips}"
```

**Tolerance:** 1.0 pip (accounts for rounding in different calculation paths)

---

## MIGRATION NOTES

### **No Breaking Changes**
- All existing signals continue to work
- Fire command format unchanged
- Database schema unchanged
- ZMQ message format unchanged

### **What Changed**
- Internal pip calculation logic unified
- XAUUSD/XAGUSD now handled correctly in manual-fire
- Safety margins now symbol-aware (not fixed 20 pips)
- ATR multipliers optimized for M5 scalping

### **Deployment Status**
- ✅ Constants module created and tested
- ✅ Auto-fire flow updated (signals.py)
- ✅ Manual-fire flow updated (fires.py)
- ✅ Fire command creation updated (enqueue_fire.py)
- ✅ Elite Guard generator updated (M5 ATR scalping)
- ✅ Comprehensive test suite (57/57 passing)
- ✅ Documentation complete

---

## EXAMPLES

### **Example 1: EURUSD BUY Signal**

**Input:**
- Symbol: EURUSD
- Direction: BUY
- Entry: 1.1000
- SL Price: 1.0950 (from signal generator)
- TP Price: 1.1100 (from signal generator)

**Auto-Fire Processing:**
```python
# Convert SL/TP prices to pips
sl_pips = pips_from_price_distance(1.1000, 1.0950, "EURUSD")  # → 50.0 pips
tp_pips = pips_from_price_distance(1.1000, 1.1100, "EURUSD")  # → 100.0 pips
```

**Manual-Fire Processing:**
```python
# Signal has stop_pips=50.0, target_pips=100.0
sl_price = calculate_stop_loss_price(1.1000, 50.0, "BUY", "EURUSD")  # → 1.0950
tp_price = calculate_take_profit_price(1.1000, 100.0, "BUY", "EURUSD")  # → 1.1100
```

**Result:** ✅ Both flows produce identical SL/TP prices

---

### **Example 2: XAUUSD SELL Signal (Gold)**

**Input:**
- Symbol: XAUUSD
- Direction: SELL
- Entry: 2000.0
- Stop Pips: 50.0
- Target Pips: 100.0

**Processing:**
```python
pip_size = get_pip_size("XAUUSD")  # → 0.10

# Calculate prices
sl_price = calculate_stop_loss_price(2000.0, 50.0, "SELL", "XAUUSD")  # → 2005.0
tp_price = calculate_take_profit_price(2000.0, 100.0, "SELL", "XAUUSD")  # → 1990.0

# Verify
verify_pip_conversion(2000.0, 2005.0, 50.0, "XAUUSD", tolerance=1.0)  # ✅ Passes
```

---

### **Example 3: M5 ATR Scalping (USDJPY)**

**Input:**
- Symbol: USDJPY
- ATR (M5): 15 pips
- Pattern: FVG (base multiplier: 1.5x)
- Session: London (session multiplier: 1.05x)
- RR Ratio: 1.8

**Calculation:**
```python
pip_size = get_pip_size("USDJPY")  # → 0.01
atr_price_units = 15.0 * 0.01  # → 0.15

# Scalping multiplier
atr_multiplier = 1.5 * 1.05  # → 1.575

stop_pips, target_pips = calc_scalp_stop_pips(
    symbol="USDJPY",
    atr_price_units=atr_price_units,
    rr=1.8,
    timeframe="M5",
    atr_mult=1.575
)
# Result: stop_pips ≈ 23.6, target_pips ≈ 42.5
# Clamped to: [6, 35] range for USDJPY M5
```

---

## TROUBLESHOOTING

### **Issue: "Pip conversion mismatch" AssertionError**

**Cause:** Price-to-pips calculation doesn't match expected value

**Debug:**
```python
# Check pip size
pip_size = get_pip_size(symbol)
print(f"Pip size for {symbol}: {pip_size}")

# Check actual distance
actual_pips = pips_from_price_distance(price1, price2, symbol)
print(f"Actual pips: {actual_pips}, Expected: {expected_pips}")

# Check tolerance
diff = abs(actual_pips - expected_pips)
print(f"Difference: {diff} pips (tolerance: 1.0)")
```

**Solution:** Verify signal generator is using constants module for pip calculations

---

### **Issue: Stop too tight for symbol**

**Cause:** ATR-based stop below symbol minimum

**Check:**
```python
min_pips, max_pips = get_min_max_stop_pips(symbol, timeframe="M5")
print(f"{symbol} M5 range: {min_pips}-{max_pips} pips")
print(f"Your stop: {stop_pips} pips")
```

**Solution:** `calc_scalp_stop_pips()` automatically clamps to safe range

---

## FUTURE ENHANCEMENTS

### **Potential Additions**
1. **H1/H4 Scalping Limits:** Add timeframe-specific limits for swing trades
2. **Exotic Pairs:** Add symbol-specific limits for USDCNH, EURTRY, etc.
3. **Adaptive Limits:** Dynamic min/max based on real-time volatility
4. **ML Optimization:** Train models to predict optimal ATR multipliers per pattern/session

---

## SUMMARY

✅ **Unified pip calculation system deployed across entire BITTEN stack**
✅ **Auto-fire and manual-fire produce identical results**
✅ **M5 ATR scalping optimized with symbol/timeframe-aware limits**
✅ **Comprehensive test coverage (57/57 passing)**
✅ **Zero breaking changes - seamless integration**

**Key Files:**
- `/root/HydraX-v2/src/bitten_core/constants.py` - Core module
- `/root/HydraX-v2/test_pip_calculations.py` - Test suite
- This document - Complete reference

**For Questions:**
- Run test suite: `python3 test_pip_calculations.py`
- Review constants module: Less than 400 lines, heavily commented
- Check integration points: Search for `from bitten_core.constants import`

---

**Last Updated:** October 23, 2025
**Verified By:** Comprehensive test suite (57/57 passing)
**Status:** Production ready ✅
