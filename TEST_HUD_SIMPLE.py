import os
#!/usr/bin/env python3
"""Send test signals with regular URL buttons"""

import requests
import json
import urllib.parse
from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
import asyncio

# Bot configuration
BOT_TOKEN = "os.getenv("BOT_TOKEN", "DISABLED_FOR_SECURITY")"
CHAT_ID = "int(os.getenv("CHAT_ID", "-1002581996861"))"

# WebApp URLs
CURRENT_WEBAPP = "http://134.199.204.67:8888"
ENHANCED_WEBAPP = "http://134.199.204.67:8889"

async def send_test_comparison():
    """Send test signal with comparison links"""
    
    bot = Bot(token=BOT_TOKEN)
    
    # Create test signal data
    signal_data = {
        'user_id': 'int(os.getenv("ADMIN_USER_ID", "7176191872"))',
        'signal': {
            'id': 'test_' + datetime.now().strftime('%Y%m%d_%H%M%S'),
            'signal_type': 'PRECISION',
            'symbol': 'EUR/USD',
            'direction': 'BUY',
            'tcs_score': 85,
            'entry': 1.0845,
            'sl': 1.0815,
            'tp': 1.0905,
            'sl_pips': 30,
            'tp_pips': 60,
            'rr_ratio': 2.0,
            'expiry': 600  # 10 minutes
        }
    }
    
    # Encode the data
    encoded_data = urllib.parse.quote(json.dumps(signal_data))
    
    # Create URLs
    current_url = f"{CURRENT_WEBAPP}/hud?data={encoded_data}"
    enhanced_url = f"{ENHANCED_WEBAPP}/hud?data={encoded_data}"
    
    # Create message with direct links
    message = (
        "🎯 **HUD COMPARISON TEST**\n\n"
        f"⭐ **PRECISION SIGNAL**\n"
        f"EUR/USD BUY @ 1.0845\n"
        f"📊 TCS: 85% | R:R 1:2.0\n"
        f"⏰ Expires in 10 minutes\n\n"
        "**Click links below to view:**\n\n"
        f"📱 Current HUD (Clean):\n{current_url}\n\n"
        f"🚀 Enhanced HUD (New Effects):\n{enhanced_url}\n\n"
        "_Open in browser on mobile/desktop to compare!_"
    )
    
    # Send message without inline keyboard
    await bot.send_message(
        chat_id=CHAT_ID,
        text=message,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )
    
    print("✅ Comparison links sent!")
    
    # Send another test with different parameters
    await asyncio.sleep(3)
    
    # High confidence signal
    signal_data2 = {
        'user_id': 'int(os.getenv("ADMIN_USER_ID", "7176191872"))',
        'signal': {
            'id': 'test_high_' + datetime.now().strftime('%H%M%S'),
            'signal_type': 'SNIPER',
            'symbol': 'GBP/USD',
            'direction': 'SELL',
            'tcs_score': 92,
            'entry': 1.2650,
            'sl': 1.2680,
            'tp': 1.2590,
            'sl_pips': 30,
            'tp_pips': 60,
            'rr_ratio': 2.0,
            'expiry': 300
        }
    }
    
    encoded_data2 = urllib.parse.quote(json.dumps(signal_data2))
    current_url2 = f"{CURRENT_WEBAPP}/hud?data={encoded_data2}"
    enhanced_url2 = f"{ENHANCED_WEBAPP}/hud?data={encoded_data2}"
    
    message2 = (
        "🔥 **HIGH CONFIDENCE TEST**\n\n"
        f"🔥 **SNIPER SIGNAL**\n"
        f"GBP/USD SELL @ 1.2650\n"
        f"📊 TCS: 92% | R:R 1:2.0\n"
        f"⏰ Expires in 5 minutes\n\n"
        f"Current: {current_url2}\n\n"
        f"Enhanced: {enhanced_url2}"
    )
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=message2,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )
    
    print("✅ High confidence signal sent!")
    
    # Low confidence signal
    await asyncio.sleep(3)
    
    signal_data3 = {
        'user_id': 'int(os.getenv("ADMIN_USER_ID", "7176191872"))',
        'signal': {
            'id': 'test_low_' + datetime.now().strftime('%H%M%S'),
            'signal_type': 'RISKY',
            'symbol': 'USD/JPY',
            'direction': 'BUY',
            'tcs_score': 72,
            'entry': 148.50,
            'sl': 148.20,
            'tp': 149.10,
            'sl_pips': 30,
            'tp_pips': 60,
            'rr_ratio': 2.0,
            'expiry': 180
        }
    }
    
    encoded_data3 = urllib.parse.quote(json.dumps(signal_data3))
    current_url3 = f"{CURRENT_WEBAPP}/hud?data={encoded_data3}"
    enhanced_url3 = f"{ENHANCED_WEBAPP}/hud?data={encoded_data3}"
    
    message3 = (
        "⚠️ **LOW CONFIDENCE TEST**\n\n"
        f"⚠️ **RISKY SIGNAL**\n"
        f"USD/JPY BUY @ 148.50\n"
        f"📊 TCS: 72% | R:R 1:2.0\n"
        f"⏰ Expires in 3 minutes\n\n"
        f"Current: {current_url3}\n\n"
        f"Enhanced: {enhanced_url3}"
    )
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=message3,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )
    
    print("✅ Low confidence signal sent!")

async def main():
    """Main function"""
    print("🚀 Sending HUD comparison links...")
    
    await send_test_comparison()
    
    print("\n✨ Done! Check Telegram for the test links.")
    print("\nYou can click the links on mobile or desktop to compare both HUD versions!")

if __name__ == "__main__":
    asyncio.run(main())