#!/usr/bin/env python3
"""Fallback signal sender using regular inline buttons + URL until WebApp is configured"""

import asyncio
import json
import time
import urllib.parse
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

# Configuration
BOT_TOKEN = '7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ'
CHAT_ID = -1002581996861
USER_ID = 7176191872
WEBAPP_URL = 'https://joinbitten.com/hud'

async def send_signal_with_url_button():
    """Send signal with regular URL button (will show preview but works immediately)"""
    bot = Bot(token=BOT_TOKEN)
    
    # Signal message
    signal_message = """⚡ **SIGNAL DETECTED**
EUR/USD | BUY | 87% confidence
⏰ Expires in 10 minutes

*Click button below to view full intelligence*"""

    # Signal data
    signal_data = {
        'signal': {
            'id': f'fallback_{int(time.time())}',
            'symbol': 'EUR/USD',
            'direction': 'BUY',
            'entry': 1.0850,
            'sl': 1.0830,
            'tp': 1.0880,
            'tcs_score': 87,
            'sl_pips': 20,
            'tp_pips': 30,
            'rr_ratio': 1.5,
            'expiry': 600
        },
        'user_id': str(USER_ID)
    }
    
    # Create URL with data
    encoded_data = urllib.parse.quote(json.dumps(signal_data))
    full_url = f"{WEBAPP_URL}?data={encoded_data}"
    
    # Regular URL button (will work but shows preview)
    keyboard = [[
        InlineKeyboardButton(
            "🎯 VIEW INTEL",
            url=full_url
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
        print(f"✅ Fallback signal sent successfully!")
        print(f"Message ID: {message.message_id}")
        print(f"\n📝 Note: This uses regular URL button")
        print(f"- Will show link preview/confirmation")
        print(f"- Works immediately without BotFather config")
        print(f"- User can still access full webapp")
        print(f"\n🔧 To remove confirmation:")
        print(f"1. Configure bot in BotFather")
        print(f"2. Set Mini App URL to: {WEBAPP_URL}")
        print(f"3. Then use WebApp buttons instead")
        
    except Exception as e:
        print(f"❌ Error: {e}")

async def send_multiple_signal_formats():
    """Send different signal formats to test"""
    bot = Bot(token=BOT_TOKEN)
    
    signals = [
        {
            'message': """🔥 **HIGH CONFIDENCE SIGNAL**
GBP/USD | SELL | 94% confidence
Entry: 1.2650 | SL: 1.2670 | TP: 1.2610
⏰ 15 minutes remaining""",
            'data': {
                'signal': {
                    'id': f'high_{int(time.time())}',
                    'symbol': 'GBP/USD',
                    'direction': 'SELL',
                    'entry': 1.2650,
                    'sl': 1.2670,
                    'tp': 1.2610,
                    'tcs_score': 94,
                    'sl_pips': 20,
                    'tp_pips': 40,
                    'rr_ratio': 2.0,
                    'expiry': 900
                },
                'user_id': str(USER_ID)
            }
        },
        {
            'message': """⚡ **SNIPER SIGNAL**
XAU/USD | BUY | 96% confidence
London session breakout detected
⏰ Act fast - 5 minutes!""",
            'data': {
                'signal': {
                    'id': f'sniper_{int(time.time())}',
                    'symbol': 'XAU/USD',
                    'direction': 'BUY',
                    'entry': 2335.50,
                    'sl': 2330.00,
                    'tp': 2345.00,
                    'tcs_score': 96,
                    'sl_pips': 55,
                    'tp_pips': 95,
                    'rr_ratio': 1.7,
                    'expiry': 300
                },
                'user_id': str(USER_ID)
            }
        }
    ]
    
    for i, signal in enumerate(signals):
        try:
            encoded_data = urllib.parse.quote(json.dumps(signal['data']))
            url = f"{WEBAPP_URL}?data={encoded_data}"
            
            keyboard = [[
                InlineKeyboardButton(
                    "🎯 VIEW INTEL",
                    url=url
                )
            ]]
            
            await bot.send_message(
                chat_id=CHAT_ID,
                text=signal['message'],
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            print(f"✅ Signal {i+1} sent successfully")
            
        except Exception as e:
            print(f"❌ Signal {i+1} failed: {e}")
        
        # Small delay between signals
        await asyncio.sleep(2)

async def send_production_style_signal():
    """Send production-style signal matching requirements"""
    bot = Bot(token=BOT_TOKEN)
    
    # Production signal format
    signal_text = """⚡ **SIGNAL ACTIVE**
XAU/USD | BUY | 94% confidence
Entry Zone: 2333.XX - 2334.XX

*Tap button for full mission briefing*"""
    
    # Production data
    signal_data = {
        'signal': {
            'id': f'prod_{int(time.time())}',
            'symbol': 'XAU/USD',
            'direction': 'BUY',
            'entry': 2333.50,
            'sl': 2328.00,
            'tp': 2344.00,
            'tcs_score': 94,
            'sl_pips': 55,
            'tp_pips': 105,
            'rr_ratio': 1.9,
            'expiry': 900,
            'signal_type': 'SNIPER',
            'pattern': 'WALL_BREACH'
        },
        'user_id': str(USER_ID),
        'tier_required': 'FANG',
        'timestamp': int(time.time())
    }
    
    # Create URL
    encoded_data = urllib.parse.quote(json.dumps(signal_data))
    url = f"{WEBAPP_URL}?data={encoded_data}"
    
    # Button
    keyboard = [[
        InlineKeyboardButton(
            "🎯 VIEW INTEL",
            url=url
        )
    ]]
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=signal_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    print("✅ Production signal sent!")
    print("\n📊 Signal Details:")
    print(f"- Symbol: XAU/USD")
    print(f"- Direction: BUY")
    print(f"- TCS Score: 94%")
    print(f"- Risk/Reward: 1:1.9")
    print(f"- Pattern: WALL BREACH")
    print(f"\n🔗 URL Button:")
    print(f"- Will show confirmation dialog")
    print(f"- But provides full webapp access")
    print(f"- Works immediately without bot config")

async def main():
    print("🚀 BITTEN Fallback Signal Sender")
    print("=" * 50)
    print("This uses regular URL buttons that work immediately")
    print("(Shows confirmation dialog until WebApp is configured)")
    print("=" * 50)
    
    print("\n1. Sending basic signal...")
    await send_signal_with_url_button()
    
    print("\n2. Sending multiple signal formats...")
    await send_multiple_signal_formats()
    
    print("\n3. Sending production-style signal...")
    await send_production_style_signal()
    
    print("\n✅ All fallback signals sent!")
    print("\n📝 Next Steps:")
    print("1. Test the buttons in Telegram")
    print("2. Verify webapp opens correctly")
    print("3. Configure bot in BotFather for WebApp")
    print("4. Switch to WebApp buttons to remove confirmation")

if __name__ == "__main__":
    asyncio.run(main())