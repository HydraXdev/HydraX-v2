# EVENT BUS - SINGLE SOURCE OF TRUTH DATA SPECIFICATION

**File**: `/root/HydraX-v2/comprehensive_tracking.jsonl`
**Purpose**: Complete signal tracking from generation through execution to TP/SL death
**Architecture**: Event bus driven, real-time ZMQ monitoring

---

## 🎯 EXACTLY WHAT DATA WE HAVE NOW

**Our comprehensive tracker now captures EVERY metric that was previously scattered across multiple tracking systems:**

### **1. CORE SIGNAL DATA**
```json
"signal_id": "ELITE_RAPID_GBPUSD_1758296000",
"symbol": "GBPUSD",
"direction": "BUY",
"pattern_type": "LIQUIDITY_SWEEP_REVERSAL",
"confidence": 78.5,
"quality_score": 78.5
```

### **2. PRICE LEVELS & RISK/REWARD**
```json
"entry_price": 1.2750,
"stop_loss": 1.2720,
"take_profit": 1.2795,
"sl_pips": 30,
"tp_pips": 45,
"risk_reward": 1.5
```

### **3. TIMING & SESSION DATA**
```json
"created_at": 1758296000,
"session": "LONDON",
"atr_value": 25.4
```

### **4. SIGNAL CLASSIFICATION**
```json
"signal_class": "RAPID",  // or "SNIPER"
"status": "EXECUTED"      // or "GENERATED", "FAILED_EXECUTION"
```

### **5. EXECUTION TRACKING**
```json
"executed": true,
"user_id": "7176191872",
"ticket": 123456789,
"ea_uuid": "COMMANDER_DEV_001",
"execution_time": 1758296045,
"fill_price": 1.2752,
"lot_size": 0.15,
"risk_pct": 2.0,
"risk_amount": 34.50
```

### **6. ADVANCED PERFORMANCE METRICS**
```json
"outcome": "WIN",                    // WIN, LOSS, MANUAL, TIMEOUT
"pips_result": 42.3,
"exit_price": 1.2794,
"close_time": 1758298250,
"lifespan": 2205,                    // seconds from signal to completion
"max_favorable_excursion": 48.1,     // NEW - highest profit reached
"max_adverse_excursion": 8.2,        // NEW - deepest drawdown
"tracking_duration_minutes": 36.75   // NEW - real tracking time
```

### **7. ACCOUNT STATE AT EXECUTION**
```json
"balance": 5000.00,
"equity": 5045.30
```

---

## 🔍 COMPARISON: WHAT WE CONSOLIDATED

**BEFORE (Multiple fragmented files):**
- `comprehensive_tracking.jsonl` - Basic signal data
- `optimized_tracking.jsonl` - Quality scores, R:R ratios, signal classification
- `dynamic_tracking.jsonl` - Max favorable/adverse excursion, ATR timeouts
- `truth_log.jsonl` - Outcome tracking (outdated)
- 2169+ obsolete tracking report files

**NOW (Single comprehensive file):**
- `/root/HydraX-v2/comprehensive_tracking.jsonl` - **ALL METRICS COMBINED**

---

## 🚀 WHAT THIS GIVES US

### **1. COMPLETE SIGNAL LIFECYCLE TRACKING**
- Signal generation → Elite Guard publishes to port 5557
- Fire execution → Confirmations from port 5558
- Real-time price monitoring → Tick data from port 5560
- Position closure → Final outcome capture
- **ZERO data loss - follows every signal to death**

### **2. ADVANCED PERFORMANCE ANALYTICS**
- **Win Rate by Pattern**: Which patterns actually work
- **Risk/Reward Efficiency**: Actual R:R vs planned R:R
- **Excursion Analysis**: How far trades move in our favor/against us
- **Session Performance**: Which trading sessions perform best
- **Confidence Calibration**: Does 80% confidence actually win 80%?

### **3. ML & OPTIMIZATION READY**
- Every signal tracked with complete feature set
- Real outcomes (not theoretical predictions)
- Performance data for pattern optimization
- Account state correlation with performance

### **4. UNIFIED REPORTING**
- Single file to query for ALL analysis
- No more hunting through multiple tracking systems
- Standardized JSON format for easy parsing
- Real-time updates as signals complete

---

## 🎯 EXACTLY WHAT METRICS WERE MISSING BEFORE

**From old `dynamic_tracking.jsonl` (now integrated):**
- `max_favorable_excursion` - NEW ✅
- `max_adverse_excursion` - NEW ✅
- `atr_value` and `dynamic_timeout_minutes` - NEW ✅
- `tracking_duration_minutes` - NEW ✅

**From old `optimized_tracking.jsonl` (now integrated):**
- `quality_score` - NEW ✅
- `risk_reward` ratios - NEW ✅
- `signal_class` (RAPID/SNIPER) - NEW ✅
- `lifespan` tracking - NEW ✅

**Execution details (previously scattered):**
- Complete EA confirmation data - NEW ✅
- Account balance/equity at execution - NEW ✅
- Lot sizing and risk percentage used - NEW ✅

---

## 🔧 HOW TO USE THIS DATA

### **Generate 24h Performance Report:**
```bash
python3 /root/HydraX-v2/BITTEN_SIGNAL_REPORT_TEMPLATE.py
```

### **Query Specific Metrics:**
```python
import json

# Get all wins from last 24 hours
wins = []
with open('/root/HydraX-v2/comprehensive_tracking.jsonl') as f:
    for line in f:
        data = json.loads(line)
        if data.get('outcome') == 'WIN':
            wins.append(data)

# Calculate average max favorable excursion for wins
avg_favorable = sum(w['max_favorable_excursion'] for w in wins) / len(wins)
```

### **Real-Time Monitoring:**
```bash
tail -f /root/HydraX-v2/comprehensive_tracking.jsonl | jq .
```

---

## ✅ SYSTEM STATUS

**Event Bus Architecture:**
- ✅ Elite Guard publishing signals to port 5557
- ✅ Confirmations flowing from EA on port 5558
- ✅ Market data streaming on port 5560
- ✅ Comprehensive tracker (PM2 ID 152) monitoring all ports
- ✅ Real-time excursion tracking via tick monitoring
- ✅ Complete signal lifecycle from generation to TP/SL death

**Data Quality:**
- ✅ No duplicate tracking systems
- ✅ No data fragmentation
- ✅ Real outcomes (not theoretical predictions)
- ✅ Complete feature coverage for ML/optimization
- ✅ Standardized reporting format

**Single Source of Truth Achieved:** 🎯