#!/usr/bin/env python3
"""Send compact test signal to BITTEN Telegram"""

import asyncio
from datetime import datetime
from telegram import Bot
from telegram.constants import ParseMode

# Configuration
BOT_TOKEN = '7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ'
CHAT_ID = -1002581996861

async def send_compact_signals():
    """Send different compact signal formats"""
    bot = Bot(token=BOT_TOKEN)
    
    # Compact format 1 - Minimal
    minimal_signal = """🎮 **ROCKET RIDE** - EUR/USD
→ BUY @ 1.0850
→ +30 pips | TCS: 87%
[🔫 FIRE]"""

    # Compact format 2 - One-liner
    oneliner_signal = """⚡ EUR/USD BUY 1.0850 | +30p | TCS: 87% | [🔫 FIRE]"""

    # Compact format 3 - Essential info only
    essential_signal = """⚡ **SCALP ALERT**
EUR/USD BUY @ 1.0850
Target: +30 pips
[🔫 EXECUTE]"""

    # Compact format 4 - Alert style from signal_display.py
    alert_style = """⚡ **ALPHA-1** | SCALP
━━━━━━━━━━━━━━━━━━━━━
📍 EUR/USD BUY
💯 TCS: 87% | ⏱️ 10m
👥 12 traders active"""

    signals = [
        ("Minimal Format:", minimal_signal),
        ("One-liner Format:", oneliner_signal),
        ("Essential Format:", essential_signal),
        ("Alert Format:", alert_style)
    ]

    try:
        for title, signal in signals:
            await bot.send_message(
                chat_id=CHAT_ID,
                text=f"**{title}**\n\n{signal}",
                parse_mode=ParseMode.MARKDOWN
            )
            await asyncio.sleep(1)  # Small delay between messages
            
        print(f"✅ All compact test signals sent!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Sending compact test signals...")
    asyncio.run(send_compact_signals())