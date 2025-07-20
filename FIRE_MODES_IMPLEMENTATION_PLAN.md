# 🔫 BITTEN Fire Modes Implementation Plan

**Date**: July 15, 2025  
**Critical Rule**: Users NEVER adjust risk - all risk is system-controlled

---

## 🎯 Fire Mode Definitions

### 1. MANUAL Mode (Currently Working)
- User clicks to execute each trade
- Full conscious decision for each signal
- Available to all tiers

### 2. SEMI_AUTO Mode (COMMANDER/APEX)
**Concept**: Assisted execution with safety confirmation
- System prepares complete trade setup
- Shows all calculations (risk is fixed, not adjustable)
- Displays potential outcomes
- One-click confirmation required
- Reduces decision fatigue while maintaining control

**Implementation**:
```python
# When signal arrives for SEMI_AUTO user:
1. Prepare trade with system-defined risk (2% fixed)
2. Calculate and display:
   - Entry price
   - Stop loss (system calculated)
   - Take profit (based on signal RR ratio)
   - Dollar risk amount
   - Potential profit
3. Show confirmation dialog
4. If confirmed within 60 seconds, execute
5. If timeout, signal expires
```

### 3. FULL_AUTO Mode (COMMANDER/APEX)
**Concept**: Autonomous slot-based execution
- User sets ONLY max concurrent positions (slots)
- System handles everything else
- No risk adjustment allowed

**Implementation**:
```python
# User configuration (one-time setup):
- Max slots: 1-3 positions (user choice)
- TCS threshold: System defined per tier
- Risk per trade: 2% (fixed, not adjustable)

# Execution flow:
1. Signal arrives with TCS >= tier threshold
2. Check if slot available
3. If yes: Auto-execute with 2% risk
4. Track open positions
5. When position closes, slot becomes available
```

### 4. CHAINGUN Mode (Special Reward)
**Concept**: Progressive risk ladder with safety net
- One-time use special weapon
- Earned through XP, badges, or gifts
- SNIPER OPS signals only

**Unique Features**:
- **Progressive Risk**: 2% → 4% → 6% → 8% (system controlled)
- **Golden Parachute**: Exit anytime with NO XP loss
- **Single Trade Count**: All shots count as 1 trade
- **Badge Rewards**: 3-shot, 5-shot, 7-shot achievements

**Implementation**:
```python
class ChaingunMode:
    def __init__(self):
        self.risk_ladder = [0.02, 0.04, 0.06, 0.08]
        self.current_shot = 0
        self.golden_parachute_available = True
    
    def fire_next_shot(self):
        if self.current_shot >= len(self.risk_ladder):
            return "Max shots reached"
        
        risk = self.risk_ladder[self.current_shot]
        # Execute with progressive risk
        
    def deploy_parachute(self):
        # Close all positions
        # No XP penalty
        # End chaingun session
```

---

## 🏗️ Implementation Architecture

### Database Schema
```sql
-- User fire mode settings
CREATE TABLE user_fire_modes (
    user_id INTEGER PRIMARY KEY,
    current_mode TEXT DEFAULT 'MANUAL',
    max_slots INTEGER DEFAULT 1,
    slots_in_use INTEGER DEFAULT 0,
    chaingun_inventory INTEGER DEFAULT 0,
    last_mode_change TIMESTAMP
);

-- Chaingun sessions
CREATE TABLE chaingun_sessions (
    session_id INTEGER PRIMARY KEY,
    user_id INTEGER,
    start_time TIMESTAMP,
    current_shot INTEGER,
    total_profit DECIMAL,
    parachute_deployed BOOLEAN,
    end_time TIMESTAMP
);
```

### Mode Validation
```python
def validate_fire_mode(user_tier, requested_mode):
    allowed_modes = {
        'NIBBLER': ['MANUAL'],
        'FANG': ['MANUAL'],
        'COMMANDER': ['MANUAL', 'SEMI_AUTO', 'FULL_AUTO'],
        'APEX': ['MANUAL', 'SEMI_AUTO', 'FULL_AUTO']
    }
    return requested_mode in allowed_modes.get(user_tier, ['MANUAL'])
```

---

## 🎮 User Interface

### Telegram Bot Commands
```
/mode - View current fire mode
/mode MANUAL - Switch to manual mode
/mode SEMI - Switch to semi-auto (COMMANDER+)
/mode AUTO - Switch to full auto (COMMANDER+)
/slots [1-3] - Set max slots for AUTO mode
/chaingun - View chaingun inventory
/parachute - Deploy golden parachute (during chaingun)
```

### WebApp UI
- Mode selector dropdown (filtered by tier)
- Slot configuration for AUTO mode
- Chaingun inventory display
- Golden parachute button (visible during chaingun)
- Current mode indicator in header

---

## 🛡️ Safety Features

### All Modes
- Risk ALWAYS system-controlled (2% standard)
- Daily trade limits enforced
- TCS thresholds respected
- Emergency stop available

### SEMI_AUTO Specific
- 60-second confirmation timeout
- Clear risk display (not adjustable)
- Cancel button prominent

### FULL_AUTO Specific
- Max 3 concurrent positions
- Automatic stop if daily loss hit
- Mode auto-disables on tilt detection

### CHAINGUN Specific
- Only SNIPER OPS signals
- Max 8% risk ceiling
- Golden parachute always available
- Auto-ends on stop loss hit

---

## 📊 Tracking & Analytics

### Metrics to Track
- Mode usage by tier
- SEMI_AUTO confirmation rates
- AUTO mode slot utilization
- Chaingun session lengths
- Golden parachute usage rate
- Badge achievements earned

### Performance Comparison
- Win rate by mode
- Average profit by mode
- Risk-adjusted returns
- User retention by mode preference

---

## 🚀 Implementation Priority

1. **Phase 1**: SEMI_AUTO Mode
   - Simplest to implement
   - High value for COMMANDER users
   - Good stepping stone to AUTO

2. **Phase 2**: Mode Switching System
   - Database schema
   - Bot commands
   - WebApp UI

3. **Phase 3**: FULL_AUTO Mode
   - Slot management
   - Queue system
   - Safety validations

4. **Phase 4**: CHAINGUN Mode
   - Inventory system
   - Progressive risk calculator
   - Badge achievements
   - Golden parachute mechanism

---

## ⚠️ Critical Reminders

1. **NO USER RISK ADJUSTMENT** - Ever. Period.
2. **Risk is always 2%** (except chaingun progression)
3. **Tier validation** on every mode change
4. **Safety first** - All modes respect limits
5. **Clear communication** - Users must understand what each mode does

---

**Note**: This is a gamification layer on top of trading. The goal is to make trading feel like a game while maintaining strict risk controls. Users get the illusion of control through mode selection, but actual risk is always system-managed.