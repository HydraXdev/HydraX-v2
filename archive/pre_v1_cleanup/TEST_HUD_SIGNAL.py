import os
#!/usr/bin/env python3
"""Send test signals to both webapp versions for comparison"""

import requests
import json
import urllib.parse
from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
import asyncio

# Bot configuration
BOT_TOKEN = "os.getenv("BOT_TOKEN", "DISABLED_FOR_SECURITY")"
CHAT_ID = "int(os.getenv("CHAT_ID", "-1002581996861"))"

# WebApp URLs
CURRENT_WEBAPP = "http://134.199.204.67:8888"
ENHANCED_WEBAPP = "http://134.199.204.67:8889"

async def send_test_signal():
    """Send a test signal with both webapp versions"""
    
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
    
    # Create message text
    message = (
        "🎯 **TEST SIGNAL COMPARISON**\n"
        f"EUR/USD BUY @ 1.0845\n"
        f"📊 TCS: 85% | R:R 1:2.0\n"
        f"⏰ Expires in 10 minutes\n\n"
        "Click below to compare HUD versions:"
    )
    
    # Create inline keyboard with both versions
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text="📱 Current HUD (v1)",
            web_app=WebAppInfo(url=current_url)
        )],
        [InlineKeyboardButton(
            text="🚀 Enhanced HUD (v2)", 
            web_app=WebAppInfo(url=enhanced_url)
        )]
    ])
    
    # Send message
    await bot.send_message(
        chat_id=CHAT_ID,
        text=message,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    
    print("✅ Test signal sent!")
    print(f"Current HUD: {current_url}")
    print(f"Enhanced HUD: {enhanced_url}")

async def send_multiple_test_signals():
    """Send different types of test signals"""
    
    bot = Bot(token=BOT_TOKEN)
    
    # Different signal scenarios
    test_signals = [
        {
            'type': 'HIGH_CONFIDENCE',
            'symbol': 'GBP/USD',
            'direction': 'SELL',
            'tcs_score': 92,
            'entry': 1.2650,
            'sl': 1.2680,
            'tp': 1.2590,
            'signal_type': 'SNIPER'
        },
        {
            'type': 'MODERATE_CONFIDENCE',
            'symbol': 'USD/JPY',
            'direction': 'BUY',
            'tcs_score': 78,
            'entry': 148.50,
            'sl': 148.20,
            'tp': 149.10,
            'signal_type': 'STANDARD'
        },
        {
            'type': 'LOW_CONFIDENCE',
            'symbol': 'AUD/USD',
            'direction': 'SELL',
            'tcs_score': 72,
            'entry': 0.6420,
            'sl': 0.6450,
            'tp': 0.6360,
            'signal_type': 'RISKY'
        }
    ]
    
    for i, signal in enumerate(test_signals):
        # Calculate pips (simplified)
        if 'JPY' in signal['symbol']:
            multiplier = 100
        else:
            multiplier = 10000
            
        sl_pips = abs(signal['entry'] - signal['sl']) * multiplier
        tp_pips = abs(signal['tp'] - signal['entry']) * multiplier
        rr_ratio = round(tp_pips / sl_pips, 1)
        
        # Create signal data
        signal_data = {
            'user_id': 'int(os.getenv("ADMIN_USER_ID", "7176191872"))',
            'signal': {
                'id': f'test_{i}_{datetime.now().strftime("%H%M%S")}',
                'signal_type': signal['signal_type'],
                'symbol': signal['symbol'],
                'direction': signal['direction'],
                'tcs_score': signal['tcs_score'],
                'entry': signal['entry'],
                'sl': signal['sl'],
                'tp': signal['tp'],
                'sl_pips': round(sl_pips),
                'tp_pips': round(tp_pips),
                'rr_ratio': rr_ratio,
                'expiry': 300 + (i * 120)  # Different expiry times
            }
        }
        
        # Encode the data
        encoded_data = urllib.parse.quote(json.dumps(signal_data))
        
        # Create URLs
        current_url = f"{CURRENT_WEBAPP}/hud?data={encoded_data}"
        enhanced_url = f"{ENHANCED_WEBAPP}/hud?data={encoded_data}"
        
        # Create message
        confidence_emoji = "🔥" if signal['tcs_score'] >= 85 else "⭐" if signal['tcs_score'] >= 75 else "⚠️"
        
        message = (
            f"{confidence_emoji} **{signal['type'].replace('_', ' ')}**\n"
            f"{signal['symbol']} {signal['direction']} @ {signal['entry']}\n"
            f"📊 TCS: {signal['tcs_score']}% | R:R 1:{rr_ratio}\n"
            f"⏰ Expires in {(300 + i * 120) // 60} minutes"
        )
        
        # Create keyboard
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                text="📱 View Current HUD",
                web_app=WebAppInfo(url=current_url)
            )],
            [InlineKeyboardButton(
                text="🚀 View Enhanced HUD", 
                web_app=WebAppInfo(url=enhanced_url)
            )]
        ])
        
        # Send message
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        print(f"✅ Test signal {i+1} sent: {signal['type']}")
        
        # Wait between signals
        await asyncio.sleep(2)

async def main():
    """Main function"""
    print("🚀 Sending test signals to compare HUD versions...")
    
    # Send single test signal
    await send_test_signal()
    
    # Uncomment to send multiple test signals
    # await asyncio.sleep(3)
    # await send_multiple_test_signals()
    
    print("\n✨ Done! Check Telegram for the test signals.")
    print("\nDirect URLs for desktop testing:")
    
    # Generate a test URL for desktop
    test_data = {
        'user_id': 'desktop_test',
        'signal': {
            'id': 'desktop_test_001',
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
            'expiry': 600
        }
    }
    
    encoded = urllib.parse.quote(json.dumps(test_data))
    print(f"\nCurrent HUD: {CURRENT_WEBAPP}/hud?data={encoded}")
    print(f"Enhanced HUD: {ENHANCED_WEBAPP}/hud?data={encoded}")

if __name__ == "__main__":
    asyncio.run(main())