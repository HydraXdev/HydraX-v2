#!/usr/bin/env python3
"""Send test signal for BITTEN Ultimate experience - Simple version"""

import asyncio
from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
import urllib.parse
import json

BOT_TOKEN = '7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ'
CHAT_ID = -1002581996861

async def send_bitten_ultimate_signal():
    bot = Bot(token=BOT_TOKEN)
    
    # Create a SNIPER-tier signal
    signal = {
        'id': f'BIT-{int(datetime.now().timestamp())}',
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'tcs_score': 92,
        'signal_type': 'SNIPER',
        'entry': 1.0925,
        'sl': 1.0905,
        'tp': 1.0975,
        'sl_pips': 20,
        'tp_pips': 50,
        'rr_ratio': 2.5,
        'timestamp': datetime.now().isoformat(),
        'expiry': 600
    }
    
    # Format narrative signal
    message = f"""🐈‍⬛ **BITTEN SIGNAL DETECTED**

*Norman whispers: "This pattern... I've seen it before."*

💎 **EUR/USD** | **BUY** | **92% TCS**
📍 Entry: 1.0925
🛡️ SL: 1.0905 (-20 pips)
🎯 TP: 1.0975 (+50 pips)
📊 R:R: 1:2.5

*Bit's amber eyes glow with excitement*

⏰ Chapter 2 Signal - Expires in 10 minutes
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
        "🎮 ENTER BITTEN WORLD",
        url=f"http://134.199.204.67:8892/hud?data={encoded_data}"
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
        print("✅ BITTEN Ultimate signal sent!")
        print("🎮 WebApp URL: http://134.199.204.67:8892")
        print("🐈‍⬛ Bit is watching...")
        print("\n📖 This interface integrates the full BITTEN lore:")
        print("- Norman's narrative voice guides your trades")
        print("- Bit's presence reacts to your performance")
        print("- Gaming RPG aesthetics with achievements")
        print("- Story progression through trading chapters")
        print("- AAA-quality immersive experience")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(send_bitten_ultimate_signal())