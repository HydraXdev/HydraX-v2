#!/usr/bin/env python3
# Simple test of integrated alerts

import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
import sys
sys.path.append('/root/HydraX-v2')

# Import just the templates directly
exec(open('/root/HydraX-v2/src/bitten_core/trade_alert_templates.py').read())

BOT_TOKEN = "7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ"
CHAT_ID = "-1002581996861"

async def test_integration():
    """Test the integrated alert formats"""
    
    bot = Bot(token=BOT_TOKEN)
    
    print("📤 Testing integrated alerts...")
    
    # Test arcade alert
    arcade_data = {
        'callsign': '🌅 DAWN RAID',
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'entry_price': 1.08450,
        'take_profit_pips': 15,
        'stop_loss_pips': 10,
        'tcs_score': 82,
        'active_traders': 17,
        'seconds_remaining': 272
    }
    
    message = TradeAlertTemplates.arcade_alert_final(arcade_data)
    keyboard = [[
        InlineKeyboardButton("⚡ EXECUTE", callback_data="execute"),
        InlineKeyboardButton("📊 INTEL", callback_data="intel")
    ]]
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    print("✅ Sent arcade alert")
    await asyncio.sleep(1)
    
    # Test sniper alert
    sniper_data = {
        'symbol': 'USDJPY',
        'direction': 'SELL',
        'entry_price': 110.250,
        'take_profit_pips': 35,
        'stop_loss_pips': 15,
        'tcs_score': 94,
        'active_traders': 8,
        'seconds_remaining': 495
    }
    
    message = TradeAlertTemplates.sniper_compact(sniper_data)
    keyboard = [[
        InlineKeyboardButton("🎯 EXECUTE", callback_data="execute"),
        InlineKeyboardButton("📊 INTEL", callback_data="intel")
    ]]
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    print("✅ Sent sniper alert")
    await asyncio.sleep(1)
    
    # Test Midnight Hammer
    hammer_border = "⚡🔨⚡🔨⚡🔨⚡🔨⚡🔨⚡🔨⚡🔨⚡🔨⚡🔨⚡"
    hammer_msg = f"""{hammer_border}
🔨 MIDNIGHT HAMMER EVENT 🔨
💥 LEGENDARY SETUP DETECTED 💥
{hammer_border}

XAUUSD BUY @ 1948.75
+100 / -50 (5% RISK)

COMMUNITY POWER: ████████ 96%
WARRIORS READY: 147 ⚔️
UNITY BONUS: +15% XP 🎯

EXPIRES: 04:32 ⏰

{hammer_border}"""
    
    keyboard = [[
        InlineKeyboardButton("🔨 JOIN THE HAMMER", callback_data="hammer")
    ]]
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=hammer_msg,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    print("✅ Sent Midnight Hammer")
    
    print("\n✅ Integration test complete!")

if __name__ == "__main__":
    asyncio.run(test_integration())