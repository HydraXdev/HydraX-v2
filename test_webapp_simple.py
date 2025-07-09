#!/usr/bin/env python3
"""Simple test to verify WebApp button functionality"""

import asyncio
import json
import urllib.parse
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.constants import ParseMode

# Configuration
BOT_TOKEN = '7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ'
CHAT_ID = -1002581996861
USER_ID = 7176191872

# Test different URLs
TEST_URLS = [
    'https://joinbitten.com/test',
    'https://joinbitten.com/hud',
    'https://core.telegram.org/bots/webapps',  # Known working example
]

async def test_webapp_button():
    """Test if WebApp button works at all"""
    bot = Bot(token=BOT_TOKEN)
    
    # Very simple test
    for i, url in enumerate(TEST_URLS):
        try:
            keyboard = [[
                InlineKeyboardButton(
                    f"Test {i+1}: {url.split('/')[-1]}",
                    web_app=WebAppInfo(url=url)
                )
            ]]
            
            await bot.send_message(
                chat_id=CHAT_ID,
                text=f"🧪 WebApp Test {i+1}\nTesting URL: {url}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            print(f"✅ Test {i+1} sent successfully: {url}")
            
        except Exception as e:
            print(f"❌ Test {i+1} failed: {e}")
        
        # Small delay between tests
        await asyncio.sleep(1)

async def test_with_data():
    """Test WebApp with data parameter"""
    bot = Bot(token=BOT_TOKEN)
    
    # Simple data
    data = {
        'test': True,
        'signal': 'EUR/USD',
        'time': '2024-07-08'
    }
    
    encoded_data = urllib.parse.quote(json.dumps(data))
    url = f"https://joinbitten.com/hud?data={encoded_data}"
    
    try:
        keyboard = [[
            InlineKeyboardButton(
                "🎯 Test with Data",
                web_app=WebAppInfo(url=url)
            )
        ]]
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text="🔍 Testing WebApp with data parameter",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        print("✅ Data test sent successfully")
        
    except Exception as e:
        print(f"❌ Data test failed: {e}")

async def test_minimal_webapp():
    """Test minimal WebApp implementation"""
    bot = Bot(token=BOT_TOKEN)
    
    try:
        keyboard = [[
            InlineKeyboardButton(
                "🚀 Minimal Test",
                web_app=WebAppInfo(url="https://joinbitten.com/test")
            )
        ]]
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text="🎮 Minimal WebApp Test",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        print("✅ Minimal test sent successfully")
        
    except Exception as e:
        print(f"❌ Minimal test failed: {e}")

async def main():
    print("🚀 Testing WebApp Button Functionality")
    print("=" * 50)
    
    # Test 1: Basic WebApp buttons
    print("\n1. Testing basic WebApp buttons...")
    await test_webapp_button()
    
    # Test 2: WebApp with data
    print("\n2. Testing WebApp with data...")
    await test_with_data()
    
    # Test 3: Minimal WebApp
    print("\n3. Testing minimal WebApp...")
    await test_minimal_webapp()
    
    print("\n✅ All tests completed!")
    print("\nIf all tests succeeded, the WebApp should open without confirmation.")
    print("If any failed, check:")
    print("- Bot is configured in BotFather")
    print("- WebApp URL is set in bot settings")
    print("- HTTPS is working properly")
    print("- Telegram client supports WebApps")

if __name__ == "__main__":
    asyncio.run(main())