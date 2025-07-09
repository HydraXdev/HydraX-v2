#!/usr/bin/env python3
"""Send clean signal with instant redirect approach"""

import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
import json
import urllib.parse
from datetime import datetime
import random

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

async def send_clean_signal():
    """Send signal with clean formatting"""
    bot = Bot(token=BOT_TOKEN)
    
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
    
    # Calculate entry/SL/TP based on current market sim
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
    
    # Create webapp data
    webapp_data = {
        'user_id': '7176191872',
        'signal': {
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
    
    # Create clean signal message
    message = (
        f"{strength} *{pattern['name']}* {pattern['emoji']}\n"
        f"`{symbol}` | {direction} | {tcs_score}%\n"
        f"⏰ Expires in 10 minutes"
    )
    
    # Create keyboard with instant URL
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
    
    print(f"✅ Signal sent!")
    print(f"📊 {symbol} | {direction} | {tcs_score}%")
    print(f"🎯 Pattern: {pattern['name']}")
    print(f"💫 Entry: {entry} | SL: {sl} | TP: {tp}")
    
    # Send follow-up tip after 3 seconds
    await asyncio.sleep(3)
    
    tip_message = (
        "💡 *Quick Access Tip:*\n\n"
        "Click the 📎 menu button (bottom left) → Select '🎮 BITTEN HUD'\n"
        "This opens the HUD instantly without any confirmation!\n\n"
        "_Menu button configured for instant access_"
    )
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=tip_message,
        parse_mode=ParseMode.MARKDOWN
    )

async def main():
    print("🚀 Sending Clean Signal Format")
    print("==============================\n")
    
    await send_clean_signal()
    
    print("\n✨ Signal sent successfully!")
    print("\n📱 Users have two options:")
    print("1. Click signal button (requires one confirmation)")
    print("2. Use 📎 menu → BITTEN HUD (instant access)")

if __name__ == "__main__":
    asyncio.run(main())