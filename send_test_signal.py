#!/usr/bin/env python3
"""Send test signal to BITTEN Telegram"""

import asyncio
from datetime import datetime
from telegram import Bot
from telegram.constants import ParseMode

# Your configuration
BOT_TOKEN = '7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ'
CHAT_ID = -1002581996861
USER_ID = 7176191872

async def send_test_signal():
    """Send a formatted test signal"""
    bot = Bot(token=BOT_TOKEN)
    
    # Test signal with BITTEN tactical formatting
    signal_message = """🎯 **TACTICAL SIGNAL DETECTED**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔥 **OPERATION: TEST STRIKE**
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
💬 _"Test signal for display adjustment"_

#TestSignal #BITTEN"""

    try:
        message = await bot.send_message(
            chat_id=CHAT_ID,
            text=signal_message,
            parse_mode=ParseMode.MARKDOWN
        )
        print(f"✅ Test signal sent successfully!")
        print(f"Message ID: {message.message_id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Sending test signal to BITTEN Telegram...")
    print(f"Chat ID: {CHAT_ID}")
    print(f"User ID: {USER_ID}")
    asyncio.run(send_test_signal())