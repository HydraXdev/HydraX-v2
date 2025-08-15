# 🚨 BITTEN Signal Flow Documentation

## Quick Start: What Happens When a Signal is Detected

### 1. Signal Detection → 2. Brief Alert → 3. WebApp Button → 4. Full Intel in WebApp

---

## 📍 Complete Signal Flow (Step by Step)

### 1️⃣ **Signal Detection**
- Trading system detects a signal meeting criteria
- Signal data includes: symbol, direction, entry, TP, SL, confidence score

### 2️⃣ **Signal Alert Creation** 
```python
# Location: src/bitten_core/signal_alerts.py
# Creates brief 2-3 line alert with WebApp button

Alert Format:
⚡ **SIGNAL DETECTED**
EUR/USD | BUY | 87% confidence  
⏰ Expires in 10 minutes
[🎯 VIEW INTEL] <- WebApp button
```

### 3️⃣ **Telegram Message**
- Bot sends brief alert to Telegram chat/user
- Includes WebApp button that opens full intelligence

### 4️⃣ **WebApp Opens**
- User clicks "VIEW INTEL" button
- Opens webapp in Telegram's built-in browser
- Shows full mission briefing based on user tier

---

## 🔧 Configuration Required

### Set WebApp URL
```python
# In your initialization code:
WEBAPP_URL = "https://your-domain.com/hud"  # MUST BE HTTPS!

# When creating components:
signal_alerts = SignalAlertSystem(
    bot_token=BOT_TOKEN,
    hud_webapp_url=WEBAPP_URL
)
```

### Start WebApp Server
```bash
# Run the Flask webapp server
python webapp_server.py
# Default runs on port 5000
```

---

## 📝 Signal Message Formats

### ✅ CORRECT Format (Brief Alert)
```
⚡ **SIGNAL DETECTED**
EUR/USD | BUY | 87% confidence
⏰ Expires in 10 minutes
[🎯 VIEW INTEL]
```

### ❌ WRONG Format (Too Verbose)
```
🎯 **TACTICAL SIGNAL DETECTED**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔥 **OPERATION: DAWN RAID**
📍 Asset: EUR/USD
... (20 more lines)
```

---

## 🔑 Key Files & Their Roles

| File | Purpose | Key Functions |
|------|---------|---------------|
| `src/bitten_core/signal_alerts.py` | Creates brief alerts with WebApp buttons | `send_signal_alert()` |
| `webapp_server.py` | Serves the WebApp interface | Flask routes for `/hud` |
| `src/bitten_core/telegram_router.py` | Routes commands and button callbacks | `handle_signal_command()` |
| `src/bitten_core/signal_display.py` | Formats signals (NOT for Telegram alerts!) | Used in WebApp display |

---

## 🚀 Quick Test

```python
# Test signal with WebApp button
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

async def test_signal():
    bot = Bot(token=YOUR_BOT_TOKEN)
    
    # Brief alert
    message = "⚡ **SIGNAL DETECTED**\nEUR/USD | BUY | 87%\n⏰ Expires in 10 min"
    
    # WebApp button
    keyboard = [[
        InlineKeyboardButton(
            "🎯 VIEW INTEL",
            web_app=WebAppInfo(url=f"{WEBAPP_URL}?signal_id=test123")
        )
    ]]
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
```

---

## ⚠️ Common Issues

1. **WebApp Button Not Working**
   - Ensure URL is HTTPS (required by Telegram)
   - Check webapp server is running
   - Verify URL is accessible

2. **Signal Too Long**
   - Keep Telegram alert to 2-3 lines
   - Full details go in WebApp, not Telegram

3. **Missing Button**
   - Check `hud_webapp_url` is configured
   - Ensure using `WebAppInfo` not just `url`

---

## 📊 Signal Data Flow

```
Trading System
    ↓
Signal Detection
    ↓
SignalAlertSystem.send_signal_alert()
    ↓
Brief Telegram Message (2-3 lines)
    ↓
User Clicks WebApp Button
    ↓
webapp_server.py renders full intel
    ↓
User sees complete mission briefing
```

---

## 🎯 For AI/Developers

**To send a test signal:** Look at `/root/HydraX-v2/SIGNAL_FLOW.md` section "Quick Test"

**To understand the flow:** Start with `signal_alerts.py` → follow to `webapp_server.py`

**Key insight:** Telegram shows brief alerts, WebApp shows full intelligence