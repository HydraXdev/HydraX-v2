#!/usr/bin/env python3
"""Send test signal for BITTEN Ultimate experience"""

import asyncio
import sys
from datetime import datetime
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from bitten_core.signal_display import format_single_tier_signal

BOT_TOKEN = '7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ'
CHAT_ID = -1002581996861

async def send_bitten_ultimate_signal():
    bot = Bot(token=BOT_TOKEN)
    
    # Create a SNIPER-tier signal for maximum narrative impact
    signal = {
        'id': f'BIT-{int(datetime.now().timestamp())}',
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'tcs_score': 92,  # SNIPER shot
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
    
    # Format signal with narrative
    message = f"""🐈‍⬛ **BITTEN SIGNAL DETECTED**

*Norman whispers: "This pattern... I've seen it before. Bit's fur is standing up."*

{format_single_tier_signal(signal, 'nibbler')}

*Bit chirps excitedly, amber eyes fixed on the chart*

⏰ Signal expires in 10 minutes
"""
    
    # Create webapp button for BITTEN Ultimate
    webapp_data = {
        'mission_id': signal['id'],
        'signal': signal,
        'timestamp': int(datetime.now().timestamp()),
        'narrative': 'chapter_2',
        'bit_mood': 'excited'
    }
    
    webapp_button = InlineKeyboardButton(
        "🎮 ENTER BITTEN WORLD",
        url=f"http://134.199.204.67:8892/hud?data={webapp_data}"
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
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(send_bitten_ultimate_signal())