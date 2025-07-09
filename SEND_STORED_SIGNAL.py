#!/usr/bin/env python3
"""Send signal with server-side storage for menu button access"""

import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
import json
import urllib.parse
from datetime import datetime
import random
from signal_storage import save_signal

BOT_TOKEN = "7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ"
CHAT_ID = "-1002581996861"

# Pattern configurations
PATTERNS = {
    'LONDON_RAID': {'emoji': '🌅', 'name': 'LONDON RAID'},
    'WALL_BREACH': {'emoji': '🧱', 'name': 'WALL BREACH'},
    'SNIPER_NEST': {'emoji': '🎯', 'name': "SNIPER'S NEST"},
    'AMBUSH_POINT': {'emoji': '🪤', 'name': 'AMBUSH POINT'},
    'SUPPLY_DROP': {'emoji': '📦', 'name': 'SUPPLY DROP'},
    'PINCER_MOVE': {'emoji': '🦾', 'name': 'PINCER MOVE'}
}

async def send_stored_signal():
    """Send signal and store it for menu button access"""
    bot = Bot(token=BOT_TOKEN)
    
    # User ID (would get from message context in real implementation)
    user_id = '7176191872'
    
    # Generate signal data
    signal_id = f"sig_{datetime.now().strftime('%H%M%S')}"
    
    # Random pattern
    pattern_key = random.choice(list(PATTERNS.keys()))
    pattern = PATTERNS[pattern_key]
    
    # Signal parameters
    pairs = ['EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD']
    symbol = random.choice(pairs)
    direction = random.choice(['BUY', 'SELL'])
    tcs_score = random.randint(75, 92)
    
    # Calculate entry/SL/TP
    if symbol == 'EUR/USD':
        base = 1.0850
    elif symbol == 'GBP/USD':
        base = 1.2650
    elif symbol == 'USD/JPY':
        base = 148.50
    else:
        base = 0.6750
        
    entry = round(base + random.uniform(-0.0020, 0.0020), 5)
    
    if direction == 'BUY':
        sl = round(entry - 0.0030, 5)
        tp = round(entry + 0.0060, 5)
    else:
        sl = round(entry + 0.0030, 5)
        tp = round(entry - 0.0060, 5)
    
    # Create signal data
    signal_data = {
        'id': signal_id,
        'pattern': pattern_key,
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
    
    # Store signal for user
    save_signal(user_id, signal_data)
    print(f"💾 Signal stored for user {user_id}")
    
    # Create webapp data for direct link
    webapp_data = {
        'user_id': user_id,
        'signal': signal_data
    }
    
    # Encode data for URL
    encoded_data = urllib.parse.quote(json.dumps(webapp_data))
    webapp_url = f"https://joinbitten.com/hud?data={encoded_data}"
    
    # Determine signal strength
    if tcs_score >= 90:
        strength = "🔥🔥"
    elif tcs_score >= 85:
        strength = "🔥"
    elif tcs_score >= 80:
        strength = "⭐"
    else:
        strength = "⚡"
    
    # Create message
    message = (
        f"{strength} *{pattern['name']}* {pattern['emoji']}\n"
        f"`{symbol}` | {direction} | {tcs_score}%\n"
        f"⏰ Expires in 10 minutes\n\n"
        f"_Access via:_\n"
        f"• Button below (1 confirm)\n"
        f"• 📎 Menu → BITTEN HUD (instant)"
    )
    
    # Create keyboard
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text="🎯 VIEW MISSION INTEL",
            url=webapp_url
        )]
    ])
    
    # Send the signal
    await bot.send_message(
        chat_id=CHAT_ID,
        text=message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )
    
    print(f"✅ Signal sent and stored!")
    print(f"📊 {symbol} | {direction} | {tcs_score}%")
    print(f"🎯 Pattern: {pattern['name']}")
    print(f"💫 Entry: {entry} | SL: {sl} | TP: {tp}")
    print(f"\n📱 Users can now:")
    print("1. Click signal button for direct access")
    print("2. Use menu button to see latest signal")

async def main():
    print("🚀 Sending Signal with Storage")
    print("==============================\n")
    
    await send_stored_signal()
    
    print("\n✨ Test the menu button:")
    print("1. Click 📎 in Telegram")
    print("2. Select 'BITTEN HUD'")
    print("3. Latest signal loads automatically!")

if __name__ == "__main__":
    asyncio.run(main())