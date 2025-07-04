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

### ✅ Completed
- Core BITTEN controller (`src/bitten_core/bitten_core.py`)
- Fire modes and tier system (`src/bitten_core/fire_modes.py`)
- Telegram routing (`src/bitten_core/telegram_router.py`)
- Signal display formatting (`src/bitten_core/signal_display.py`)
- All filters (Master, Arcade, Sniper)
- Rank access system
- Trade tagging and XP logging
- Strategy base implementations

### 🔄 In Progress
- Fire mode execution logic
- Position management integration
- Risk calculations per tier
- Telegram command handlers

### 📋 Todo
- News event detection system
- Drawdown protection (-7% daily limit)
- Cooldown timer enforcement
- Unity bonus for Midnight Hammer
- Complete testing framework
- Production deployment

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