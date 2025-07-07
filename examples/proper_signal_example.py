#!/usr/bin/env python3
"""
PROPER SIGNAL EXAMPLE - This is how signals should work!

Signal Flow:
1. Brief alert to Telegram (2-3 lines)
2. WebApp button for full details
3. User clicks to see complete intelligence
"""

import asyncio
import json
import time
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.constants import ParseMode

# ⚠️ CONFIGURATION - Must be set!
BOT_TOKEN = '7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ'
CHAT_ID = -1002581996861

# ⚠️ WEBAPP URL - Replace with your actual webapp URL!
# This MUST be HTTPS for Telegram WebApp to work
WEBAPP_URL = "https://your-webapp-domain.com/hud"  # <-- CHANGE THIS!

async def send_proper_bitten_signal():
    """This is the CORRECT way to send a BITTEN signal"""
    
    bot = Bot(token=BOT_TOKEN)
    
    # ✅ CORRECT: Brief signal (2-3 lines max)
    signal_alert = """⚡ **SIGNAL DETECTED**
EUR/USD | BUY | 87% confidence
⏰ Expires in 10 minutes"""
    
    # Signal data for webapp
    signal_data = {
        'signal_id': f'sig_{int(time.time())}',
        'symbol': 'EUR/USD',
        'direction': 'BUY',
        'entry_price': 1.0850,
        'stop_loss': 1.0830,
        'take_profit': 1.0880,
        'confidence': 87,
        'tier_required': 'NIBBLER',
        'expires_in': 600  # seconds
    }
    
    # Create webapp button
    keyboard = [[
        InlineKeyboardButton(
            "🎯 VIEW INTEL",
            web_app=WebAppInfo(
                url=f"{WEBAPP_URL}?data={json.dumps(signal_data)}"
            )
        )
    ]]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        # Send the signal
        message = await bot.send_message(
            chat_id=CHAT_ID,
            text=signal_alert,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        
        print("✅ Signal sent successfully!")
        print(f"Message ID: {message.message_id}")
        print("\n📝 What happens next:")
        print("1. User sees brief alert in Telegram")
        print("2. User clicks 'VIEW INTEL' button")
        print("3. WebApp opens with full mission briefing")
        print("4. User sees detailed analysis based on their tier")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if "Button_type_invalid" in str(e):
            print("\n⚠️ WebApp URL must be HTTPS!")
            print("Please set a valid WEBAPP_URL in this script")

# ❌ WRONG: This is TOO verbose for Telegram
async def wrong_signal_example():
    """This is the WRONG way - too much info in Telegram"""
    
    # Don't send this to Telegram!
    wrong_signal = """🎯 **TACTICAL SIGNAL DETECTED**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔥 **OPERATION: DAWN RAID**
📍 Asset: EUR/USD
💹 Direction: BUY
🎯 Entry: 1.0850

📊 **TACTICAL DATA**
• Stop Loss: 1.0830 (-20 pips)
• Take Profit: 1.0890 (+40 pips)
• Risk/Reward: 1:2
• Confidence: 85%

⏰ **MISSION TIMER**
Signal expires in: 30:00
[████████████████████] 100%

⚡ **FIRE MODE: ARCADE**
🎖️ Authorized for: All Tiers

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💬 _"Strike fast, strike true"_ - CDR"""
    
    print("❌ This is WRONG - too verbose for Telegram!")
    print("This detailed view belongs in the WebApp, not Telegram chat")

if __name__ == "__main__":
    print("🚀 BITTEN Signal Example")
    print("=" * 50)
    print(f"Bot Token: {BOT_TOKEN[:20]}...")
    print(f"Chat ID: {CHAT_ID}")
    print(f"WebApp URL: {WEBAPP_URL}")
    print("=" * 50)
    
    if WEBAPP_URL == "https://your-webapp-domain.com/hud":
        print("\n⚠️ WARNING: You need to set your actual WEBAPP_URL!")
        print("The WebApp button won't work without a valid HTTPS URL")
        print("\nWould you like to:")
        print("1. See the CORRECT signal format anyway")
        print("2. See what NOT to do (wrong format)")
    else:
        asyncio.run(send_proper_bitten_signal())