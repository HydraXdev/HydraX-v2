import os
#!/usr/bin/env python3
"""Send signal with proper WebApp Mini App integration"""

import asyncio
import sys
sys.path.append('/root/HydraX-v2')
from signal_storage import save_signal

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonWebApp, WebAppInfo
from telegram.constants import ParseMode
import json
import urllib.parse
from datetime import datetime

BOT_TOKEN = "os.getenv("BOT_TOKEN", "DISABLED_FOR_SECURITY")"
CHAT_ID = "int(os.getenv("CHAT_ID", "-1002581996861"))"

async def send_webapp_signal():
    """Send signal with Mini App button"""
    bot = Bot(token=BOT_TOKEN)
    
    # Generate signal data
    signal_id = f"mini_{datetime.now().strftime('%H%M%S')}"
    
    # Signal parameters
    symbol = "GBP/USD"
    direction = "SELL"
    tcs_score = 88
    entry = 1.2650
    sl = 1.2680
    tp = 1.2590
    pattern = "SNIPER_NEST"
    
    # Create webapp data
    webapp_data = {
        'user_id': 'int(os.getenv("ADMIN_USER_ID", "7176191872"))',
        'signal': {
            'id': signal_id,
            'pattern': pattern,
            'symbol': symbol,
            'direction': direction,
            'tcs_score': tcs_score,
            'entry': entry,
            'sl': sl,
            'tp': tp,
            'sl_pips': 30,
            'tp_pips': 60,
            'rr_ratio': 2.0,
            'expiry': 600
        }
    
    # Save signal to storage for webapp access
    if 'signal' in webapp_data:
        save_signal(webapp_data['user_id'], webapp_data['signal'])
    elif 'user_id' in webapp_data:
        # Extract signal data from webapp_data
        signal_data = {k: v for k, v in webapp_data.items() if k != 'user_id'}
        save_signal(webapp_data['user_id'], signal_data)

    }
    
    # Encode data for URL with start parameter
    encoded_data = urllib.parse.quote(json.dumps(webapp_data))
    
    # Try different WebApp URL formats
    webapp_urls = [
        f"https://joinbitten.com/hud?data={encoded_data}",
        f"https://joinbitten.com/hud#{encoded_data}",
        f"https://joinbitten.com/hud?startapp={signal_id}"
    ]
    
    # Create the signal message
    message = (
        f"🎯 *{pattern.replace('_', ' ')}*\n"
        f"{symbol} | {direction} | {tcs_score}%\n"
        f"⏰ Expires in 10 minutes"
    )
    
    # Method 1: Try WebApp with full URL
    try:
        print("🔧 Method 1: WebApp button with data in URL...")
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                text="🎮 OPEN MISSION",
                web_app=WebAppInfo(url=webapp_urls[0])
            )]
        ])
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message + "\n\n_Method 1: Full URL_",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
        print("✅ Sent Method 1")
        
    except Exception as e:
        print(f"❌ Method 1 failed: {e}")
    
    await asyncio.sleep(2)
    
    # Method 2: Try with startapp parameter
    try:
        print("\n🔧 Method 2: Using startapp parameter...")
        
        # Store signal data server-side and use signal_id as reference
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                text="🎮 LAUNCH INTEL",
                web_app=WebAppInfo(url=webapp_urls[2])
            )]
        ])
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message + "\n\n_Method 2: startapp_",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
        print("✅ Sent Method 2")
        
    except Exception as e:
        print(f"❌ Method 2 failed: {e}")
    
    await asyncio.sleep(2)
    
    # Method 3: Simple WebApp button to base URL
    try:
        print("\n🔧 Method 3: Simple WebApp to base URL...")
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                text="🎮 VIEW INTEL",
                web_app=WebAppInfo(url="https://joinbitten.com/hud")
            )]
        ])
        
        # Include signal data in message
        signal_text = (
            f"🎯 *{pattern.replace('_', ' ')}*\n"
            f"{symbol} | {direction} | {tcs_score}%\n"
            f"Entry: {entry} | SL: {sl} | TP: {tp}\n"
            f"Risk: {30} pips | Reward: {60} pips\n"
            f"⏰ Signal ID: `{signal_id}`"
        )
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text=signal_text + "\n\n_Method 3: Base URL_",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
        print("✅ Sent Method 3")
        
    except Exception as e:
        print(f"❌ Method 3 failed: {e}")
    
    print("\n📊 Testing complete!")
    print("\n🔍 Check which method opens without confirmation")
    print("\n💡 If all still show confirmation:")
    print("1. Clear Telegram cache")
    print("2. Make sure bot username matches BotFather config")
    print("3. Try on different device/client")

async def check_webapp_config():
    """Check current webapp configuration"""
    bot = Bot(token=BOT_TOKEN)
    
    try:
        # Get bot info
        bot_info = await bot.get_me()
        print(f"\n🤖 Bot Info:")
        print(f"Username: @{bot_info.username}")
        print(f"Has Main Web App: {bot_info.has_main_web_app}")
        
        # Get webhook info
        webhook_info = await bot.get_webhook_info()
        print(f"\n🔗 Webhook Info:")
        print(f"URL: {webhook_info.url or 'Not set'}")
        
    except Exception as e:
        print(f"❌ Error checking config: {e}")

async def main():
    print("🚀 Testing WebApp Mini App Integration")
    print("=====================================")
    
    # First check configuration
    await check_webapp_config()
    
    print("\n📤 Sending test signals...")
    await send_webapp_signal()

if __name__ == "__main__":
    asyncio.run(main())