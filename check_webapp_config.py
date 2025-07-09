#!/usr/bin/env python3
"""Check if WebApp is properly configured and accessible"""

import asyncio
import json
import urllib.parse
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.constants import ParseMode
import requests

# Configuration
BOT_TOKEN = '7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ'
CHAT_ID = -1002581996861
WEBAPP_URL = 'https://joinbitten.com/hud'
TEST_ENDPOINTS = [
    'https://joinbitten.com/',
    'https://joinbitten.com/test',
    'https://joinbitten.com/hud',
    'https://joinbitten.com/hud?data=test'
]

def check_webapp_accessibility():
    """Check if webapp endpoints are accessible"""
    print("🔍 Checking WebApp Accessibility...")
    print("-" * 40)
    
    for endpoint in TEST_ENDPOINTS:
        try:
            response = requests.get(endpoint, timeout=10)
            status = "✅ ACCESSIBLE" if response.status_code == 200 else f"❌ ERROR {response.status_code}"
            print(f"{status} - {endpoint}")
            
            # Check for Telegram WebApp script
            if 'telegram-web-app.js' in response.text:
                print(f"  ✅ Contains Telegram WebApp script")
            else:
                print(f"  ⚠️  Missing Telegram WebApp script")
                
        except Exception as e:
            print(f"❌ FAILED - {endpoint} - {str(e)}")
    
    print()

async def check_bot_info():
    """Check bot information"""
    print("🤖 Checking Bot Information...")
    print("-" * 40)
    
    try:
        bot = Bot(token=BOT_TOKEN)
        bot_info = await bot.get_me()
        
        print(f"✅ Bot Name: {bot_info.first_name}")
        print(f"✅ Bot Username: @{bot_info.username}")
        print(f"✅ Bot ID: {bot_info.id}")
        print(f"✅ Can Join Groups: {bot_info.can_join_groups}")
        print(f"✅ Can Read Messages: {bot_info.can_read_all_group_messages}")
        
        # Check if bot supports WebApps
        if hasattr(bot_info, 'supports_inline_queries'):
            print(f"✅ Supports Inline Queries: {bot_info.supports_inline_queries}")
        
    except Exception as e:
        print(f"❌ Bot check failed: {e}")
    
    print()

async def test_webapp_button():
    """Test if WebApp button works"""
    print("🎯 Testing WebApp Button...")
    print("-" * 40)
    
    try:
        bot = Bot(token=BOT_TOKEN)
        
        # Simple test data
        test_data = {
            'test': True,
            'timestamp': '2024-07-08',
            'source': 'config_check'
        }
        
        encoded_data = urllib.parse.quote(json.dumps(test_data))
        url = f"{WEBAPP_URL}?data={encoded_data}"
        
        keyboard = [[
            InlineKeyboardButton(
                "🧪 WebApp Test",
                web_app=WebAppInfo(url=url)
            )
        ]]
        
        message = await bot.send_message(
            chat_id=CHAT_ID,
            text="🧪 **WebApp Configuration Test**\n\nIf you see this message, click the button below to test WebApp functionality.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        print(f"✅ WebApp button test sent successfully!")
        print(f"✅ Message ID: {message.message_id}")
        print(f"✅ If this worked, WebApp is properly configured!")
        
    except Exception as e:
        print(f"❌ WebApp button test failed: {e}")
        
        if "Button_type_invalid" in str(e):
            print("\n🚨 ISSUE DETECTED: Bot not configured for WebApps")
            print("\n📝 To fix this:")
            print("1. Open Telegram and search for @BotFather")
            print("2. Send /mybots to BotFather")
            print("3. Select your bot")
            print("4. Choose 'Bot Settings'")
            print("5. Select 'Configure Mini App'")
            print(f"6. Set Mini App URL to: {WEBAPP_URL}")
            print("7. Save the settings")
            print("8. Run this test again")
    
    print()

async def test_fallback_url_button():
    """Test fallback URL button"""
    print("🔗 Testing Fallback URL Button...")
    print("-" * 40)
    
    try:
        bot = Bot(token=BOT_TOKEN)
        
        test_data = {
            'fallback_test': True,
            'timestamp': '2024-07-08'
        }
        
        encoded_data = urllib.parse.quote(json.dumps(test_data))
        url = f"{WEBAPP_URL}?data={encoded_data}"
        
        keyboard = [[
            InlineKeyboardButton(
                "🔗 Fallback Test",
                url=url
            )
        ]]
        
        message = await bot.send_message(
            chat_id=CHAT_ID,
            text="🔗 **Fallback URL Test**\n\nThis uses regular URL button (shows confirmation but always works)",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        print(f"✅ Fallback URL button test sent successfully!")
        print(f"✅ Message ID: {message.message_id}")
        print(f"✅ This should always work (but shows confirmation)")
        
    except Exception as e:
        print(f"❌ Fallback URL button test failed: {e}")
    
    print()

def print_configuration_summary():
    """Print configuration summary"""
    print("📋 Configuration Summary")
    print("=" * 50)
    print(f"Bot Token: {BOT_TOKEN[:20]}...")
    print(f"Chat ID: {CHAT_ID}")
    print(f"WebApp URL: {WEBAPP_URL}")
    print(f"Test Endpoints: {len(TEST_ENDPOINTS)} URLs")
    print()

def print_next_steps():
    """Print next steps"""
    print("🚀 Next Steps")
    print("=" * 50)
    print("1. ✅ Check all tests above passed")
    print("2. 🔧 If WebApp button failed, configure in BotFather")
    print("3. 📱 Test buttons in Telegram mobile app")
    print("4. 🖥️  Test buttons in Telegram Desktop")
    print("5. 🌐 Verify webapp opens without confirmation")
    print("6. 🚀 Deploy production signals")
    print()
    
    print("📚 Documentation:")
    print("- Setup Guide: /root/HydraX-v2/WEBAPP_SETUP_GUIDE.md")
    print("- Fallback Signals: python3 send_signal_fallback.py")
    print("- WebApp Signals: python3 send_signal_webapp_fixed.py")
    print()

async def main():
    print("🔧 BITTEN WebApp Configuration Check")
    print("=" * 50)
    print()
    
    # Print configuration
    print_configuration_summary()
    
    # Check webapp accessibility
    check_webapp_accessibility()
    
    # Check bot info
    await check_bot_info()
    
    # Test WebApp button
    await test_webapp_button()
    
    # Test fallback URL button
    await test_fallback_url_button()
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    asyncio.run(main())