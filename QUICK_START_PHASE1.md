# 🚀 B.I.T.T.E.N. Quick Start - Phase 1 Implementation

## 🎯 Immediate Actions (Do These First!)

### 1. Complete Fire Execution (fire_router.py)
```python
# Add to fire_router.py after line 50

class CooldownManager:
    """Manages cooldowns between shots"""
    def __init__(self):
        self.last_shot_times = {}  # user_id: timestamp
        self.cooldown_seconds = 1800  # 30 minutes
    
    def can_fire(self, user_id: int) -> Tuple[bool, int]:
        """Check if user can fire, return (can_fire, seconds_remaining)"""
        now = time.time()
        last_shot = self.last_shot_times.get(user_id, 0)
        elapsed = now - last_shot
        
        if elapsed >= self.cooldown_seconds:
            return True, 0
        else:
            remaining = int(self.cooldown_seconds - elapsed)
            return False, remaining
    
    def record_shot(self, user_id: int):
        """Record shot timestamp"""
        self.last_shot_times[user_id] = time.time()
```

### 2. Add Risk Calculator
```python
# Create new file: src/bitten_core/risk_calculator.py

from typing import Dict, Tuple
from dataclasses import dataclass

@dataclass
class RiskCalculation:
    """Risk calculation result"""
    position_size: float
    risk_amount: float
    risk_percentage: float
    stop_loss_pips: int

class RiskCalculator:
    """Calculate position sizes based on 2% risk rule"""
    
    def __init__(self):
        self.risk_percentage = 0.02  # 2% fixed risk
        self.pip_values = {
            'GBPUSD': 10.0,
            'EURUSD': 10.0,
            'USDJPY': 0.1,
            'GBPJPY': 0.1,
            'USDCAD': 10.0
        }
    
    def calculate_position_size(
        self, 
        account_balance: float,
        symbol: str,
        stop_loss_pips: int
    ) -> RiskCalculation:
        """Calculate position size for 2% risk"""
        risk_amount = account_balance * self.risk_percentage
        pip_value = self.pip_values.get(symbol, 10.0)
        
        # Position size = Risk Amount / (Stop Loss Pips × Pip Value)
        position_size = risk_amount / (stop_loss_pips * pip_value)
        
        # Round to 0.01 lots
        position_size = round(position_size, 2)
        
        return RiskCalculation(
            position_size=position_size,
            risk_amount=risk_amount,
            risk_percentage=self.risk_percentage * 100,
            stop_loss_pips=stop_loss_pips
        )
```

### 3. Implement Drawdown Protection
```python
# Create new file: src/bitten_core/drawdown_protection.py

from typing import Dict, List
from datetime import datetime, timedelta

class DrawdownProtection:
    """Monitor and protect against excessive drawdown"""
    
    def __init__(self):
        self.daily_results = {}  # user_id: [trade_results]
        self.max_daily_drawdown = 0.07  # 7%
        self.locked_users = {}  # user_id: lock_until_timestamp
    
    def record_trade_result(self, user_id: int, pnl_percentage: float):
        """Record trade result"""
        today = datetime.now().date()
        
        if user_id not in self.daily_results:
            self.daily_results[user_id] = {}
        
        if today not in self.daily_results[user_id]:
            self.daily_results[user_id][today] = []
        
        self.daily_results[user_id][today].append(pnl_percentage)
        
        # Check drawdown
        daily_total = sum(self.daily_results[user_id][today])
        if daily_total <= -self.max_daily_drawdown:
            self._lock_user(user_id)
    
    def _lock_user(self, user_id: int):
        """Lock user until next trading day"""
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_start = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0)
        self.locked_users[user_id] = tomorrow_start.timestamp()
    
    def is_locked(self, user_id: int) -> Tuple[bool, str]:
        """Check if user is locked"""
        if user_id not in self.locked_users:
            return False, ""
        
        lock_until = self.locked_users[user_id]
        now = datetime.now().timestamp()
        
        if now >= lock_until:
            del self.locked_users[user_id]
            return False, ""
        
        unlock_time = datetime.fromtimestamp(lock_until)
        return True, f"Locked until {unlock_time.strftime('%Y-%m-%d %H:%M')}"
```

### 4. Quick Onboarding Update
```python
# Update telegram_router.py _cmd_start method

def _cmd_start(self, user_id: int, username: str) -> CommandResult:
    """Enhanced start command with onboarding"""
    user_rank = self.rank_access.get_user_rank(user_id)
    
    # Add user if not exists
    if not self.rank_access.get_user_info(user_id):
        self.rank_access.add_user(user_id, username)
        # First time user - show onboarding
        welcome_msg = f"""🤖 **Welcome to B.I.T.T.E.N.**
**Bot-Integrated Tactical Trading Engine / Network**

*"You've been B.I.T.T.E.N. — now prove you belong."*

🎯 **Quick Setup Guide:**

1️⃣ **Connect MT5** 
   → Open MT5 on your VPS
   → Load the HydraX EA
   → Check connection status with `/status`

2️⃣ **Understand Fire Modes**
   → SINGLE SHOT: Manual trades (all tiers)
   → CHAINGUN: Progressive risk (Fang+)
   → AUTO-FIRE: 24/7 automation (Commander+)

3️⃣ **Your Current Tier: {user_rank.name}**
   → Daily shots: {self._get_daily_shots(user_rank)}
   → TCS requirement: {self._get_tcs_requirement(user_rank)}%
   
Ready? Type `/help` to see your available commands!"""
    else:
        # Existing user - normal welcome
        welcome_msg = f"""🤖 **B.I.T.T.E.N. Trading Operations Center**
        
... (existing welcome message) ..."""
    
    return CommandResult(True, welcome_msg)
```

### 5. Add Visual Kill Card
```python
# Add to signal_display.py

def create_kill_card(self, trade_result: Dict) -> str:
    """Create visual kill card for successful trades"""
    pips = trade_result.get('pips', 0)
    profit = trade_result.get('profit', 0)
    symbol = trade_result.get('symbol', 'UNKNOWN')
    
    if pips >= 50:  # Legendary kill
        card = f"""
🔥🔥🔥 **LEGENDARY KILL** 🔥🔥🔥
╔═══════════════════════════════╗
║   💀 {symbol} ELIMINATED 💀    ║
║   +{pips} PIPS | ${profit:.2f}       ║
║   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓      ║
║   PRECISION: SURGICAL         ║
╚═══════════════════════════════╝
*"The Engine claims another victim."*"""
    
    elif pips >= 30:  # Epic kill
        card = f"""
⚡ **EPIC KILL** ⚡
┏━━━━━━━━━━━━━━━━━━━━┓
┃ 🎯 {symbol} DOWN   
┃ +{pips} pips | ${profit:.2f}
┃ ████████████░░░    
┗━━━━━━━━━━━━━━━━━━━━┛"""
    
    else:  # Standard kill
        card = f"""
✅ **KILL CONFIRMED**
{symbol}: +{pips} pips | ${profit:.2f}
Keep firing, soldier!"""
    
    return card
```

---

## 🔥 Implementation Checklist

### Today (Day 1):
- [ ] Add CooldownManager to fire_router.py
- [ ] Create risk_calculator.py
- [ ] Test 2% position sizing

### Tomorrow (Day 2):
- [ ] Create drawdown_protection.py
- [ ] Integrate with fire execution
- [ ] Test -7% lockout

### This Week:
- [ ] Update /start onboarding
- [ ] Add kill card visuals
- [ ] Create news_monitor.py stub
- [ ] Test all safety systems

### Next Week:
- [ ] Full fire mode testing
- [ ] Performance optimization
- [ ] Begin Phase 2 (UX)

---

## 🧪 Testing Commands

```python
# Test cooldown
/fire GBPUSD buy 0.1 85
# Wait 1 minute
/fire GBPUSD buy 0.1 85
# Should show: "❌ Cooldown active. Wait 29 minutes"

# Test risk calculator
/test_risk 10000 GBPUSD 20
# Should show: "Position: 1.00 lots (2% risk = $200)"

# Test drawdown protection  
/test_drawdown -8
# Should show: "❌ Daily limit reached. Locked until tomorrow"
```

---

## 📝 Notes

1. Start with cooldowns - easiest win
2. Risk calculator prevents overexposure
3. Drawdown protection saves accounts
4. Visual feedback keeps users engaged
5. Test everything in paper mode first!

---

*Remember: THE LAW must be followed. These are safety features, not suggestions.*