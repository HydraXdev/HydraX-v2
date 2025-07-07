# 🤖 AI Assistant Quick Reference for BITTEN

## 🎯 What You Need to Know in 30 Seconds

1. **BITTEN** = Forex trading system with military-themed gamification
2. **Signals** = Brief Telegram alerts (2-3 lines) with WebApp button for full details
3. **WebApp Required** = Full signal intelligence opens in Telegram's browser
4. **Bot Token** = `7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ`
5. **Chat ID** = `-1002581996861`

---

## 📍 Most Common Tasks

### Send Test Signal
```bash
# Look at: /root/HydraX-v2/send_proper_signal.py
# BUT you need to set WEBAPP_URL first!
```

### Understand Signal Flow
```bash
# Read: /root/HydraX-v2/SIGNAL_FLOW.md
```

### Check Configuration
```bash
# Bot config: /root/HydraX-v2/.env
# Or: /root/HydraX-v2/config/telegram.py
```

---

## 🚨 Critical Info

### Signal Format (Telegram)
```
✅ CORRECT (Brief):
⚡ **SIGNAL DETECTED**
EUR/USD | BUY | 87%
[🎯 VIEW INTEL]

❌ WRONG (Too Long):
[20+ lines of tactical briefing]
```

### WebApp URL Issue
- **Problem**: WebApp URL not configured
- **Solution**: Need HTTPS URL for webapp server
- **Files**: `webapp_server.py` serves the webapp

---

## 📂 Key Files Map

```
/root/HydraX-v2/
├── CLAUDE.md                    # Project overview
├── SIGNAL_FLOW.md              # Signal flow documentation
├── .env                        # Bot configuration
├── src/bitten_core/
│   ├── signal_alerts.py        # Creates Telegram alerts
│   ├── telegram_router.py      # Handles commands
│   └── signal_display.py       # Formats displays (for webapp)
└── webapp_server.py            # Flask webapp server
```

---

## 🔧 Quick Fixes

### User Says "Signal Too Big"
→ Use brief format from `signal_alerts.py` (2-3 lines only)

### User Wants Test Signal  
→ Need webapp URL first, then use format from `SIGNAL_FLOW.md`

### User Asks About Flow
→ Point to `/root/HydraX-v2/SIGNAL_FLOW.md`

---

## 💡 Key Insight

**Telegram = Brief Alert + Button**  
**WebApp = Full Intelligence Display**

The verbose signal displays in `signal_display.py` are for the WEBAPP, not Telegram!