#!/usr/bin/env python3
"""
Test WebApp Button Fix
This script tests different webapp button implementations to ensure they work correctly
"""

import os
import sys
import asyncio
import json
import logging
from datetime import datetime
import urllib.parse
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '-1002581996861')
WEBAPP_BASE_URL = os.getenv('WEBAPP_URL', 'https://joinbitten.com')


async def test_webapp_buttons():
    """Test different webapp button implementations"""
    bot = Bot(BOT_TOKEN)
    
    # Test signal data
    signal_data = {
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'entry': 1.0900,
        'sl': 1.0850,
        'tp': 1.0950,
        'tcs': 87
    }
    
    # Mission briefing data
    mission_data = {
        'mission_id': f'MSN-{int(datetime.now().timestamp())}',
        'user_tier': 'NIBBLER',
        'timestamp': int(datetime.now().timestamp()),
        'signal': signal_data,
        'view': 'mission_brief'
    }
    
    print("\n🧪 Testing WebApp Button Implementations...\n")
    
    # Test 1: Direct WebApp button with full data
    print("1️⃣ Testing Direct WebApp Button...")
    try:
        encoded_data = urllib.parse.quote(json.dumps(mission_data))
        webapp_url = f"{WEBAPP_BASE_URL}/hud?data={encoded_data}"
        
        keyboard1 = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "🎯 VIEW INTEL (WebApp)",
                web_app=WebAppInfo(url=webapp_url)
            )]
        ])
        
        message1 = f"""
⚡ **TEST 1: WebApp Button** ⚡

**EURUSD** | **BUY** | 87% 🔥

This button should open the WebApp directly in Telegram.
"""
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message1,
            parse_mode='Markdown',
            reply_markup=keyboard1
        )
        print("✅ WebApp button sent successfully")
        
    except Exception as e:
        print(f"❌ WebApp button failed: {e}")
    
    await asyncio.sleep(2)
    
    # Test 2: Simplified WebApp URL
    print("\n2️⃣ Testing Simplified WebApp URL...")
    try:
        # Use shorter URL with just mission ID
        simple_url = f"{WEBAPP_BASE_URL}/hud?mission={mission_data['mission_id']}"
        
        keyboard2 = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "🎯 VIEW INTEL (Simple)",
                web_app=WebAppInfo(url=simple_url)
            )]
        ])
        
        message2 = f"""
⚡ **TEST 2: Simplified URL** ⚡

**EURUSD** | **BUY** | 87% 🔥

Shorter URL with just mission ID.
Mission: `{mission_data['mission_id']}`
"""
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message2,
            parse_mode='Markdown',
            reply_markup=keyboard2
        )
        print("✅ Simplified WebApp button sent")
        
    except Exception as e:
        print(f"❌ Simplified button failed: {e}")
    
    await asyncio.sleep(2)
    
    # Test 3: Fallback URL button
    print("\n3️⃣ Testing Fallback URL Button...")
    try:
        keyboard3 = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "🎯 VIEW INTEL (URL)",
                url=f"{WEBAPP_BASE_URL}/hud?mission={mission_data['mission_id']}"
            )]
        ])
        
        message3 = f"""
⚡ **TEST 3: URL Button Fallback** ⚡

**EURUSD** | **BUY** | 87% 🔥

Regular URL button (opens in browser).
"""
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message3,
            parse_mode='Markdown',
            reply_markup=keyboard3
        )
        print("✅ URL button sent")
        
    except Exception as e:
        print(f"❌ URL button failed: {e}")
    
    await asyncio.sleep(2)
    
    # Test 4: Hybrid approach with both buttons
    print("\n4️⃣ Testing Hybrid Approach...")
    try:
        # Try WebApp first, fallback to URL
        buttons = []
        
        # Try to add WebApp button
        try:
            webapp_btn = InlineKeyboardButton(
                "🎯 VIEW IN APP",
                web_app=WebAppInfo(url=f"{WEBAPP_BASE_URL}/hud?mission={mission_data['mission_id']}")
            )
            buttons.append(webapp_btn)
        except:
            pass
        
        # Always add URL button as fallback
        url_btn = InlineKeyboardButton(
            "🌐 VIEW IN BROWSER",
            url=f"{WEBAPP_BASE_URL}/hud?mission={mission_data['mission_id']}"
        )
        buttons.append(url_btn)
        
        keyboard4 = InlineKeyboardMarkup([buttons])
        
        message4 = f"""
⚡ **TEST 4: Hybrid Approach** ⚡

**EURUSD** | **BUY** | 87% 🔥

Both WebApp and URL buttons for maximum compatibility.
"""
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message4,
            parse_mode='Markdown',
            reply_markup=keyboard4
        )
        print("✅ Hybrid buttons sent")
        
    except Exception as e:
        print(f"❌ Hybrid approach failed: {e}")
    
    await asyncio.sleep(2)
    
    # Test 5: Production-style signal with all features
    print("\n5️⃣ Testing Production Signal Format...")
    try:
        # Create production-style message
        prod_message = f"""
⚡ **SIGNAL DETECTED** ⚡

**EUR/USD** | **BUY** | 87% confidence 🔥

Entry: `1.09000`
SL: `1.08500` (-50 pips)
TP: `1.09500` (+50 pips)

Risk/Reward: 1:1
Expected Duration: ~15 min

⏰ Expires in 10 minutes
Mission ID: `{mission_data['mission_id']}`
"""
        
        # Create keyboard with webapp and fire button
        prod_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "🎯 VIEW INTEL",
                web_app=WebAppInfo(url=f"{WEBAPP_BASE_URL}/hud?mission={mission_data['mission_id']}")
            )],
            [InlineKeyboardButton(
                "🔫 FIRE (Coming Soon)",
                callback_data=f"fire_disabled_{mission_data['mission_id']}"
            )]
        ])
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text=prod_message,
            parse_mode='Markdown',
            reply_markup=prod_keyboard
        )
        print("✅ Production signal sent")
        
    except Exception as e:
        print(f"❌ Production signal failed: {e}")
    
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    print("\nPlease check your Telegram to see which buttons work correctly.")
    print("\nNOTES:")
    print("- WebApp buttons require Telegram Desktop 4.0+ or mobile app")
    print("- If WebApp button shows URL, update your Telegram client")
    print("- URL buttons always work but open in external browser")
    print("- The hybrid approach provides best compatibility")
    
    # Send final instructions
    await bot.send_message(
        chat_id=CHAT_ID,
        text="""
📋 **WebApp Button Test Complete**

Please test each button above and note:

1. **WebApp buttons** should open inside Telegram
2. **URL buttons** will open in your browser
3. If WebApp shows only URL, update Telegram

Which implementation works best for you?
""",
        parse_mode='Markdown'
    )


async def main():
    """Run tests"""
    try:
        await test_webapp_buttons()
    except Exception as e:
        logger.error(f"Test failed: {e}")


if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════╗
    ║      WebApp Button Test Suite v1.0       ║
    ╚══════════════════════════════════════════╝
    """)
    
    asyncio.run(main())