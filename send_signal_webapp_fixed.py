#!/usr/bin/env python3
"""Fixed BITTEN test signal sender with proper WebApp integration"""

import asyncio
import json
import time
import urllib.parse
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.constants import ParseMode

# Configuration
BOT_TOKEN = '7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ'
CHAT_ID = -1002581996861
USER_ID = 7176191872
WEBAPP_URL = 'https://joinbitten.com/hud'

async def send_webapp_signal():
    """Send a signal with proper WebApp integration"""
    bot = Bot(token=BOT_TOKEN)
    
    # Brief signal alert (2-3 lines as per proper format)
    signal_message = """⚡ **SIGNAL DETECTED**
EUR/USD | BUY | 87% confidence
⏰ Expires in 10 minutes"""

    # Signal data for WebApp - properly structured
    signal_data = {
        'signal': {
            'id': f'sig_{int(time.time())}',
            'symbol': 'EUR/USD',
            'direction': 'BUY',
            'entry': 1.0850,
            'sl': 1.0830,
            'tp': 1.0880,
            'tcs_score': 87,
            'sl_pips': 20,
            'tp_pips': 30,
            'rr_ratio': 1.5,
            'expiry': 600,
            'signal_type': 'ARCADE',
            'fire_mode': 'ARCADE',
            'operation_name': 'TEST STRIKE'
        },
        'user_id': str(USER_ID),
        'tier_required': 'NIBBLER'
    }
    
    # Encode data properly for URL
    encoded_data = urllib.parse.quote(json.dumps(signal_data))
    webapp_url = f"{WEBAPP_URL}?data={encoded_data}"
    
    # Create WebApp button
    keyboard = [[
        InlineKeyboardButton(
            "🎯 VIEW INTEL",
            web_app=WebAppInfo(url=webapp_url)
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
        print(f"✅ WebApp signal sent successfully!")
        print(f"Message ID: {message.message_id}")
        print(f"\n📱 WebApp Details:")
        print(f"- URL: {WEBAPP_URL}")
        print(f"- Data encoded and passed via URL parameter")
        print(f"- WebApp should open directly without confirmation")
        print(f"\n🔍 Debug Info:")
        print(f"- Full URL length: {len(webapp_url)} chars")
        print(f"- Make sure webapp includes Telegram WebApp JS")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if "Button_type_invalid" in str(e):
            print("\n⚠️ WebApp buttons require:")
            print("1. Telegram client that supports WebApps")
            print("2. HTTPS URL")
            print("3. Valid WebAppInfo object")

async def send_minimal_test():
    """Send minimal test signal to verify WebApp works"""
    bot = Bot(token=BOT_TOKEN)
    
    # Very simple message
    message = "🚀 Quick Signal Test"
    
    # Minimal data
    data = {'test': True, 'time': int(time.time())}
    encoded = urllib.parse.quote(json.dumps(data))
    
    keyboard = [[
        InlineKeyboardButton(
            "Open WebApp",
            web_app=WebAppInfo(url=f"{WEBAPP_URL}?data={encoded}")
        )
    ]]
    
    try:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        print("✅ Minimal test sent!")
    except Exception as e:
        print(f"❌ Error in minimal test: {e}")

async def test_webapp_data_response():
    """Test receiving data back from WebApp"""
    bot = Bot(token=BOT_TOKEN)
    
    # Signal with callback data
    signal_message = """🎯 **LIVE SIGNAL**
GBP/USD | SELL | 92% confidence
⏰ Act fast - 5 minutes!"""
    
    signal_data = {
        'signal': {
            'id': f'live_{int(time.time())}',
            'symbol': 'GBP/USD',
            'direction': 'SELL',
            'entry': 1.2650,
            'sl': 1.2670,
            'tp': 1.2610,
            'tcs_score': 92,
            'sl_pips': 20,
            'tp_pips': 40,
            'rr_ratio': 2.0,
            'expiry': 300
        },
        'callback_enabled': True
    }
    
    encoded_data = urllib.parse.quote(json.dumps(signal_data))
    
    keyboard = [[
        InlineKeyboardButton(
            "⚡ OPEN MISSION BRIEF",
            web_app=WebAppInfo(url=f"{WEBAPP_URL}?data={encoded_data}")
        )
    ]]
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=signal_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    print("✅ WebApp data response test sent!")

async def send_production_ready_signal():
    """Send production-ready signal matching exact requirements"""
    bot = Bot(token=BOT_TOKEN)
    
    # Production format
    signal_text = """⚡ **SIGNAL ACTIVE**
XAU/USD | BUY | 94% confidence
Entry Zone: 2333.XX - 2334.XX"""
    
    # Full production data structure
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
            'expiry': 900,  # 15 minutes
            'signal_type': 'SNIPER',
            'pattern': 'WALL_BREACH'
        },
        'user_id': str(USER_ID),
        'tier_required': 'FANG',
        'timestamp': int(time.time())
    }
    
    # Encode and create URL
    encoded = urllib.parse.quote(json.dumps(signal_data))
    
    # Single button as per requirements
    keyboard = [[
        InlineKeyboardButton(
            "🎯 VIEW INTEL",
            web_app=WebAppInfo(url=f"{WEBAPP_URL}?data={encoded}")
        )
    ]]
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=signal_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    print("✅ Production-ready signal sent!")
    print("\n📊 Signal Details:")
    print(f"- Symbol: XAU/USD")
    print(f"- Direction: BUY")
    print(f"- TCS Score: 94%")
    print(f"- Risk/Reward: 1:1.9")
    print(f"- Pattern: WALL BREACH")
    print(f"\n🌐 WebApp Integration:")
    print(f"- Opens directly in Telegram")
    print(f"- No confirmation dialog")
    print(f"- Full signal details in webapp")

async def main():
    """Main menu for testing"""
    print("🚀 BITTEN WebApp Signal Tester")
    print("=" * 50)
    print(f"Bot Token: {BOT_TOKEN[:20]}...")
    print(f"Chat ID: {CHAT_ID}")
    print(f"WebApp URL: {WEBAPP_URL}")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. Send standard WebApp signal")
        print("2. Send minimal test")
        print("3. Test data response")
        print("4. Send production-ready signal")
        print("5. Send all tests")
        print("0. Exit")
        
        choice = input("\nSelect option: ")
        
        if choice == '1':
            await send_webapp_signal()
        elif choice == '2':
            await send_minimal_test()
        elif choice == '3':
            await test_webapp_data_response()
        elif choice == '4':
            await send_production_ready_signal()
        elif choice == '5':
            print("\n🔄 Running all tests...")
            await send_webapp_signal()
            await asyncio.sleep(2)
            await send_minimal_test()
            await asyncio.sleep(2)
            await test_webapp_data_response()
            await asyncio.sleep(2)
            await send_production_ready_signal()
            print("\n✅ All tests completed!")
        elif choice == '0':
            break
        else:
            print("Invalid option")

if __name__ == "__main__":
    asyncio.run(main())