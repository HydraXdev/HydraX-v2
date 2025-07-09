#!/usr/bin/env python3
"""Send test signal for Commander Bit interface"""

import asyncio
from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
import urllib.parse
import json

BOT_TOKEN = '7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ'
CHAT_ID = -1002581996861

async def send_commander_bit_signal():
    bot = Bot(token=BOT_TOKEN)
    
    # Create a high-confidence signal
    signal = {
        'id': f'CMD-{int(datetime.now().timestamp())}',
        'symbol': 'GBPUSD',
        'direction': 'SELL',
        'tcs_score': 89,
        'signal_type': 'PRECISION',
        'entry': 1.2650,
        'sl': 1.2675,
        'tp': 1.2590,
        'sl_pips': 25,
        'tp_pips': 60,
        'rr_ratio': 2.4,
        'timestamp': datetime.now().isoformat(),
        'expiry': 600
    }
    
    # Clean military message
    message = f"""⚡ **TACTICAL ALERT**

**GBP/USD** | **SELL** | **89% CONFIDENCE**
Commander Bit: "Target acquired. Engage at your discretion."

⏰ Window closes in 10 minutes
"""
    
    # Create webapp data
    webapp_data = {
        'mission_id': signal['id'],
        'signal': signal,
        'timestamp': int(datetime.now().timestamp())
    }
    
    # URL encode the data
    encoded_data = urllib.parse.quote(json.dumps(webapp_data))
    
    # Create webapp button
    webapp_button = InlineKeyboardButton(
        "📍 VIEW INTEL",
        url=f"http://134.199.204.67:8893/hud?data={encoded_data}"
    )
    
    keyboard = InlineKeyboardMarkup([[webapp_button]])
    
    # Send message
    try:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
        print("✅ Commander Bit signal sent!")
        print("🎖️ WebApp URL: http://134.199.204.67:8893")
        print("\n📋 This interface features:")
        print("- Clean military design")
        print("- Colorblind-optimized colors")
        print("- Commander Bit as battle-hardened leader")
        print("- Simple, focused trading execution")
        print("- Combat journal for reflection")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(send_commander_bit_signal())