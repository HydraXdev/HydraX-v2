#!/usr/bin/env python3
import os

import telebot

# Get bot token
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7247085683:AAFOd25veZFLRHCvhGBiLuDQb3tKnAlQYOo")
USER_ID = 7176191872

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN, skip_pending=True)

# The alert message
message = """🚨 ELITE GUARD SIGNAL 🚨

Mission ID: ELITE_GUARD_EURUSD_1754828514

📊 EURUSD BUY
━━━━━━━━━━━━━━━━━━━━━━

📍 Entry: 1.095
🛡️ Stop Loss: 1.094 (-10 pips)
🎯 Take Profit: 1.097 (+20 pips)

💪 Confidence: 85%
🛡️ CITADEL Score: 7.5/10
📈 Pattern: LIQUIDITY_SWEEP_REVERSAL

━━━━━━━━━━━━━━━━━━━━━━
👤 YOUR DATA (COMMANDER)

💰 Position: 0.02 lots
⚠️ Risk: $200 (2%)
🎯 Win: $400
✨ XP: 255

━━━━━━━━━━━━━━━━━━━━━━

To execute this signal:
/fire ELITE_GUARD_EURUSD_1754828514

Open Mission HUD:
http://134.199.204.67:8888/hud?signal=ELITE_GUARD_EURUSD_1754828514

━━━━━━━━━━━━━━━━━━━━━━
⏰ Expires: 2 hours
━━━━━━━━━━━━━━━━━━━━━━"""

try:
    result = bot.send_message(USER_ID, message)
    print(f"✅ Alert sent successfully!")
    print(f"Message ID: {result.message_id}")
    print(f"To: {USER_ID}")
except Exception as e:
    print(f"❌ Failed to send: {e}")
    print(f"Token used: {BOT_TOKEN[:20]}...")
