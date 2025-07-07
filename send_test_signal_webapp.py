#!/usr/bin/env python3
"""Send proper BITTEN test signal with joinbitten.com WebApp integration"""

import asyncio
import json
import time
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.constants import ParseMode

# Configuration
BOT_TOKEN = '7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ'
CHAT_ID = -1002581996861
USER_ID = 7176191872
WEBAPP_URL = 'https://joinbitten.com/hud'

async def send_test_signal():
    """Send a proper BITTEN test signal with WebApp button"""
    bot = Bot(token=BOT_TOKEN)
    
    # Brief signal alert (2-3 lines as per proper format)
    signal_message = """⚡ **SIGNAL DETECTED**
EUR/USD | BUY | 87% confidence
⏰ Expires in 10 minutes"""

    # Signal data for WebApp
    signal_data = {
        'signal_id': f'test_{int(time.time())}',
        'symbol': 'EUR/USD',
        'direction': 'BUY',
        'entry_price': 1.0850,
        'stop_loss': 1.0830,
        'take_profit': 1.0880,
        'confidence': 87,
        'risk_pips': 20,
        'reward_pips': 30,
        'tier_required': 'NIBBLER',
        'expires_at': int(time.time()) + 600,
        'fire_mode': 'ARCADE',
        'operation_name': 'TEST STRIKE'
    }
    
    # Create WebApp button
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
        message = await bot.send_message(
            chat_id=CHAT_ID,
            text=signal_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        print(f"✅ Test signal sent successfully!")
        print(f"Message ID: {message.message_id}")
        print(f"\n📱 Signal Details:")
        print(f"- Brief alert sent to Telegram (3 lines)")
        print(f"- WebApp button links to: {WEBAPP_URL}")
        print(f"- Full intelligence viewable at joinbitten.com")
        print(f"\n👤 User Experience:")
        print(f"1. User sees brief alert in Telegram")
        print(f"2. Clicks 'VIEW INTEL' button")
        print(f"3. Opens full mission briefing at joinbitten.com")
        print(f"4. Sees tier-appropriate analysis and can execute trade")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if "Button_type_invalid" in str(e):
            print("\n⚠️ Note: WebApp buttons require Telegram client support")
            print("Make sure you're testing on mobile or Telegram Desktop v4.0+")

async def send_multiple_signal_types():
    """Send different types of signals to show variety"""
    bot = Bot(token=BOT_TOKEN)
    
    signals = [
        {
            'message': "⚡ **SIGNAL DETECTED**\nGBP/USD | SELL | 92% confidence\n⏰ Expires in 15 minutes",
            'data': {
                'signal_id': f'sniper_{int(time.time())}',
                'symbol': 'GBP/USD',
                'direction': 'SELL',
                'confidence': 92,
                'fire_mode': 'SNIPER',
                'tier_required': 'FANG'
            }
        },
        {
            'message': "🔨 **MIDNIGHT HAMMER EVENT**\nCommunity signal | 96% confidence\n⏰ Window closes in 5 minutes",
            'data': {
                'signal_id': f'hammer_{int(time.time())}',
                'confidence': 96,
                'fire_mode': 'MIDNIGHT_HAMMER',
                'tier_required': 'ALL'
            }
        }
    ]
    
    for signal in signals:
        keyboard = [[
            InlineKeyboardButton(
                "🎯 VIEW INTEL",
                web_app=WebAppInfo(
                    url=f"{WEBAPP_URL}?data={json.dumps(signal['data'])}"
                )
            )
        ]]
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text=signal['message'],
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await asyncio.sleep(2)
    
    print("✅ All signal types sent!")

if __name__ == "__main__":
    print("🚀 BITTEN Test Signal Sender")
    print("=" * 50)
    print(f"Bot Token: {BOT_TOKEN[:20]}...")
    print(f"Chat ID: {CHAT_ID}")
    print(f"WebApp URL: {WEBAPP_URL}")
    print("=" * 50)
    
    print("\nOptions:")
    print("1. Send single test signal")
    print("2. Send multiple signal types")
    
    # For now, just send single signal
    asyncio.run(send_test_signal())