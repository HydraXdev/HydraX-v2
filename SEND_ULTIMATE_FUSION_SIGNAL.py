#!/usr/bin/env python3
"""Send test signal for Ultimate Fusion interface"""

import asyncio
from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
import urllib.parse
import json

BOT_TOKEN = '7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ'
CHAT_ID = -1002581996861

async def send_ultimate_fusion_signal():
    bot = Bot(token=BOT_TOKEN)
    
    # Create a high-confidence signal
    signal = {
        'id': f'FUSION-{int(datetime.now().timestamp())}',
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'tcs_score': 91,
        'signal_type': 'SNIPER',
        'entry': 1.0945,
        'sl': 1.0920,
        'tp': 1.1005,
        'sl_pips': 25,
        'tp_pips': 60,
        'rr_ratio': 2.4,
        'timestamp': datetime.now().isoformat(),
        'expiry': 600
    }
    
    # Clean military message with stats teaser
    message = f"""⚡ **TACTICAL ALERT**

**EUR/USD** | **BUY** | **91% CONFIDENCE**
45% of soldiers have engaged • Win rate today: 71%

Commander Bit: "High-value target. Check your stats before engaging."

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
        "📊 VIEW FULL INTEL",
        url=f"http://134.199.204.67:8894/hud?data={encoded_data}"
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
        print("✅ Ultimate Fusion signal sent!")
        print("🎯 WebApp URL: http://134.199.204.67:8894")
        print("\n📋 This interface features:")
        print("- Personal stats bar with XP, profit, last 5 trades")
        print("- Tribe stats (45% engaged, win rates, etc)")
        print("- Money calculations under pips")
        print("- Live execution feed from other traders")
        print("- Quick profile access and navigation links")
        print("- Personal reflection prompts")
        print("- Commander Bit addressing you directly")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(send_ultimate_fusion_signal())