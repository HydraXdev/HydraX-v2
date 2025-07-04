# BITTEN Development Context for Claude

## Project Overview
BITTEN is a forex trading system with Telegram integration, implementing tiered subscriptions and automated trading signals.

## 🔥 **B.I.T.T.E.N.** — your tactical trading system — is more than just a name. It's an acronym:

---

### 🧠 **B.I.T.T.E.N. =**

> **Bot-Integrated Tactical Trading Engine / Network**

---

### 🔍 Broken Down:

| Letter | Meaning        | Purpose                                                    |
| ------ | -------------- | ---------------------------------------------------------- |
| **B**  | **Bot**        | Autonomous execution, always watching                      |
| **I**  | **Integrated** | Unified system across MT5, Telegram, XP, and fire control  |
| **T**  | **Tactical**   | High-precision logic, trailing SLs, session filters        |
| **T**  | **Trading**    | The core function: real trade execution, real results      |
| **E**  | **Engine**     | The decision core: TOC, Shadow Spotter, XP system          |
| **N**  | **Network**    | Community layer: XP tiers, observer mode, group engagement |

---

### 🧨 Tagline (optional usage):

> *"You've been B.I.T.T.E.N. — now prove you belong."*  
> *"The Engine is watching. The Network is evolving."*

---

## Key Documents
- **THE LAW**: `/docs/bitten/RULES_OF_ENGAGEMENT.md` - This is the FINAL AUTHORITY on all fire modes and tier capabilities
- **Blueprint**: `/docs/blueprint/` - Contains system architecture and world lore
- **Strategies**: `/docs/bitten/strategy-improvements-*.md` - Trading strategy documentation

## Current Implementation Status

### ✅ Completed (~40% of Blueprint)
- Core BITTEN controller (`src/bitten_core/bitten_core.py`)
- Fire modes and tier system (`src/bitten_core/fire_modes.py`)
- Fire mode validator (`src/bitten_core/fire_mode_validator.py`)
- Fire router with execution logic (`src/bitten_core/fire_router.py`)
- Telegram routing (`src/bitten_core/telegram_router.py`)
- Signal display formatting (`src/bitten_core/signal_display.py`)
- All filters (Master, Arcade, Sniper)
- Rank access system
- Trade tagging and XP logging
- Strategy base implementations
- Risk management calculations
- Cooldown timer enforcement
- Drawdown protection (-7% daily limit)
- Unity bonus for Midnight Hammer
- Stealth mode mutations
- PsyOps system with 110% psychological warfare capabilities
- Bot control system with disclaimer and toggle controls
- Telegram bot controls (/disclaimer, /bots, /toggle, /immersion, /settings)

### 📋 Comprehensive Todo List (Prioritized by Phase)

#### 🔴 HIGH PRIORITY - Core Safety & Functionality (Weeks 1-2)
1. Complete MT5 bridge result parser
2. Implement trade confirmation to Telegram
3. Create news event detection and auto-pause
4. Build -7% daily drawdown protection (enforcement)
5. Implement emergency stop functionality
6. Create /start command onboarding tree
7. Build MT5 connection walkthrough
8. Implement upgrade_router.py for tier transitions
9. Create subscription_manager.py

#### 🟡 MEDIUM PRIORITY - Enhanced Experience (Weeks 3-6)
10. Build kill card visual generator
11. Implement XP calculation engine
12. Create daily mission system
13. Build referral reward system
14. Implement /gear command with inventory
15. Create perk unlock system
16. Build DrillBot personality with message trees
17. Build MedicBot personality with emotion engine
18. Build RecruiterBot for network features
19. Create emotion-based trigger system
20. Implement loss streak support responses
21. Build trauma/journal system with scar tracking
22. Create squad/network chat system
23. Build infection tree visualization
24. Implement performance metrics tracking
25. Create kill streak detection system
26. Build narrative chapter unlock triggers
27. Implement CHAINGUN progressive risk mode
28. Build AUTO-FIRE autonomous trading

#### 🟢 LOW PRIORITY - Advanced Features (Weeks 7-10)
29. Create STEALTH mode randomization (enhanced)
30. Implement MIDNIGHT HAMMER unity events
31. Build multi-user license control panel
32. Create anti-screenshot watermarking
33. Build SCP deploy auto-packer
34. Implement AR mode foundations
35. Create corruption stage visual effects
36. Build heartbeat and pulse effects
37. Implement mobile touch interactions
38. Create PostgreSQL database migration
39. Implement Redis caching layer
40. Build Prometheus + Grafana monitoring

### 📊 Implementation Progress Tracker
- **Total Features**: 40 major components
- **Completed**: 8 features (20%)
- **In Progress**: 0 features
- **Remaining**: 32 features (80%)

### 🎯 Current Focus Areas
1. **Safety Systems**: MT5 bridge, news detection, emergency stops
2. **User Onboarding**: /start flow, MT5 setup, first trade
3. **Core Trading**: Trade confirmations, result parsing
4. **Tier Management**: Upgrades, downgrades, subscriptions

## Important Rules
1. **Always follow RULES_OF_ENGAGEMENT.md** - It's THE LAW
2. Tier pricing: Nibbler $39, Fang $89, Commander $139, APEX $188
3. TCS requirements: 70%/85%/91%/91% by tier
4. Risk is always 2% except Chaingun/Midnight Hammer
5. Never execute trades below tier TCS minimums

## Development Commands
- Run tests: `python -m pytest tests/`
- Start bot: `python start_bitten.py`
- Test signals: `python trigger_test_signals.py`
- Simulate: `python simulate_signals.py`
- Test alerts: `python test_trade_alerts.py`

## Telegram Configuration
- Bot Token: 7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ
- Main Chat ID: -1002581996861
- Admin User ID: 7176191872
- Config stored in: `.env` and `config/telegram.py`

## Git Workflow
All work is in the main branch. Changes are automatically saved to disk but remember to:
1. `git add -A` to stage changes
2. `git commit -m "descriptive message"` 
3. `git push origin main` to save to GitHub

## Next Priority
1. Complete fire execution in fire_router.py
2. Implement risk management calculations
3. Add cooldown timers
4. Test Telegram integration end-to-end