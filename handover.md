# 🚀 BITTEN SYSTEM HANDOVER DOCUMENTATION

## 🎯 CURRENT STATUS (July 9, 2025)

### ✅ COMPLETED IMPLEMENTATIONS
- [x] Option B Hybrid Risk-Velocity Engine deployed successfully
- [x] Mathematical signal classification: ARCADE vs SNIPER working
- [x] Real-time signal generation: EURJPY/GBPJPY 78-81% TCS
- [x] AWS bulletproof agent system: 3.145.84.187 operational
- [x] Forex data bridge: 10-pair coverage via exchangerate-api.com
- [x] Telegram tactical signals: 🔫 RAPID ASSAULT format working

---

## 🚨 CRITICAL PRICING INCONSISTENCIES REQUIRING IMMEDIATE ATTENTION

### 📋 OFFICIAL TIER STRUCTURE (SINGLE SOURCE OF TRUTH)
**Location**: `/root/HydraX-v2/config/payment.py`

**🔰 PRESS PASS: FREE (7-day trial)**
- One-time per email address
- Instant MT5 account setup (no credentials required)
- All NIBBLER permissions except:
  - ❌ No gamer name assignment
  - ❌ XP resets to 0 every midnight
- ⏰ 7-day maximum duration, then MT5 returns to rotation
- 🎯 Purpose: Sneak peek to feel action immediately

**🔰 NIBBLER: $39/month**
- View all signals (🔫 ARCADE + ⚡ SNIPER)
- Execute 🔫 ARCADE signals only
- Full gamer profile + persistent XP

**🦷 FANG+: $89/month**
- View all signals
- Execute ANY signal (🔫 ARCADE + ⚡ SNIPER)
- Manual execution only

**⭐ COMMANDER: $139/month**
- FULL AUTO MODE: 92%+ TCS auto-execution with slot management
- SEMI AUTO MODE: Same as FANG+ manual execution
- Paying for automation convenience

**🏔️ APEX: $188/month**
- (Premium tier with additional features)

### 🚫 PRICING CONFLICTS TO FIX

#### **1. UNAUTHORIZED PROMOTIONAL PRICING**
**Files Affected:**
- `/root/HydraX-v2/templates/emails/press_pass_day14.html`
- `/root/HydraX-v2/templates/emails/press_pass_welcome.html`

**Issues:**
- Shows "$188 crossed out → $141 FOREVER" (25% lifetime discount)
- Promotes APEX pricing in trial context
- **ACTION NEEDED**: Remove unauthorized discounts or get official approval

#### **2. MULTIPLE PRICING SOURCES (VIOLATION OF SINGLE SOURCE)**
**Files with Hardcoded Pricing:**
- `/root/HydraX-v2/src/bitten_core/subscription_manager.py` (quarterly/annual pricing)
- `/root/HydraX-v2/setup_stripe_products.py` (hardcoded cents)
- `/root/HydraX-v2/src/bitten_core/stripe_payment_simple.py` (duplicate pricing dict)
- `/root/HydraX-v2/examples/stripe_frontend_example.html` (old TCS thresholds)
- `/root/HydraX-v2/landing/index.html` (promotional "$0" messaging)

**ACTION NEEDED**: Replace all hardcoded pricing with imports from `config/payment.py`

#### **3. TCS THRESHOLD MISMATCHES**
**Current Frontend Issues:**
- Shows 70% TCS for all tiers (incorrect)
- **CORRECT THRESHOLDS**:
  - PRESS PASS: NIBBLER permissions (70% TCS, ARCADE only)
  - NIBBLER: 70% TCS, ARCADE only
  - FANG+: 85% TCS, ARCADE + SNIPER
  - COMMANDER: 92% TCS auto-execution filter
  - APEX: 91%+ TCS premium threshold

**ACTION NEEDED**: Update all frontend displays to show correct TCS thresholds

#### **4. CONFLICTING BILLING CYCLES**
**Issues:**
- `subscription_manager.py` contains quarterly/annual pricing not in official config
- `docs/STRIPE_SETUP_GUIDE.md` shows different annual pricing structure

**ACTION NEEDED**: Standardize billing cycles or remove unauthorized options

#### **5. BACKUP CONTAMINATION**
**Files:**
- `/root/HydraX-v2/backups/20250708_005951/` (multiple pricing conflicts)

**ACTION NEEDED**: Clean backup files to prevent accidental restoration of old pricing

---

## 🛠️ TODO LIST FOR NEXT AI SESSION

### **HIGH PRIORITY - PRICING STANDARDIZATION**
- [ ] **TASK 1**: Centralize all pricing to reference `config/payment.py` only
- [ ] **TASK 2**: Remove unauthorized promotional pricing from email templates
- [ ] **TASK 3**: Update frontend TCS thresholds to match tier requirements
- [ ] **TASK 4**: Standardize PRESS PASS logic across all files (7-day free trial)
- [ ] **TASK 5**: Clean backup files to remove pricing conflicts
- [ ] **TASK 6**: Audit all hardcoded dollar amounts and replace with config imports

### **MEDIUM PRIORITY - SYSTEM OPTIMIZATION**
- [ ] **TASK 7**: Monitor SNIPER signal generation (currently 0 signals at 85%+ TCS)
- [ ] **TASK 8**: Optimize TCS thresholds if SNIPER signals too rare
- [ ] **TASK 9**: Test COMMANDER auto-execution logic (92%+ filter)
- [ ] **TASK 10**: Implement proper PRESS PASS MT5 rotation system

### **LOW PRIORITY - DOCUMENTATION**
- [ ] **TASK 11**: Update all tier documentation to reflect PRESS PASS clarification
- [ ] **TASK 12**: Create pricing consistency validation script
- [ ] **TASK 13**: Document quarterly/annual pricing approval process

---

## 🔧 TECHNICAL ARCHITECTURE NOTES

### **LIVE SYSTEMS STATUS**
- ✅ Hybrid Risk-Velocity Engine: `/root/HydraX-v2/hybrid_risk_velocity_engine.py` 
- ✅ Production Signal Engine: Generating 10 signals/cycle every 2 minutes
- ✅ Forex Data Bridge: Real-time updates every 60 seconds
- ✅ AWS Bulletproof Agents: Triple redundancy at 3.145.84.187
- ✅ Telegram Integration: Tactical format working (🔫 RAPID ASSAULT)

### **SIGNAL CLASSIFICATION LOGIC**
**ARCADE Criteria (3/4 required):**
- Risk Efficiency > 4.0
- Market Velocity > 15 pips/hour
- TCS ≥ 70%
- Risk/Reward: 1:1-1:2

**SNIPER Criteria (3/4 required):**
- Absolute Profit ≥ 40 pips
- TCS ≥ 85%
- Risk/Reward ≥ 1:3
- Risk Efficiency: 1.5-4.0

### **CURRENT PERFORMANCE**
- EURJPY: 180 pips/hour velocity (qualifying for ARCADE)
- GBPJPY: 210 pips/hour velocity (qualifying for ARCADE)
- Signal quality: 78-81% TCS range
- Classification success: 100% ARCADE, 0% SNIPER (as designed)

---

## 🚨 NEXT AI SESSION PRIORITY

**START HERE**: Address pricing inconsistencies before any new feature development. The system currently has conflicting pricing information that could cause billing issues, user confusion, and legal problems.

**Primary Focus**: Ensure single source of truth for all pricing across entire codebase.

**Secondary Focus**: Monitor and potentially adjust SNIPER thresholds if premium signals are too rare for FANG+ value proposition.

---

*Document updated: July 9, 2025 23:24 UTC*
*System Status: LIVE and operational with pricing cleanup required*