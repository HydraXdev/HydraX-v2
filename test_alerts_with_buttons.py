#!/usr/bin/env python3
# Test alerts with inline buttons

import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
import sys
sys.path.append('/root/HydraX-v2')
from config.telegram import TelegramConfig

# Import templates
exec(open('/root/HydraX-v2/src/bitten_core/trade_alert_templates.py').read())

BOT_TOKEN = TelegramConfig.BOT_TOKEN
CHAT_ID = str(TelegramConfig.MAIN_CHAT_ID)

async def send_alerts_with_buttons():
    """Send alerts with inline buttons"""
    
    bot = Bot(token=BOT_TOKEN)
    
    # Test data
    arcade_trades = [
        {
            'callsign': '🌅 DAWN RAID',
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'entry_price': 1.08450,
            'take_profit_pips': 15,
            'stop_loss_pips': 10,
            'tcs_score': 82,
            'active_traders': 17,
            'seconds_remaining': 272
        },
        {
            'callsign': '🏰 WALL DEFENDER',
            'symbol': 'GBPUSD',
            'direction': 'SELL',
            'entry_price': 1.27850,
            'take_profit_pips': 20,
            'stop_loss_pips': 12,
            'tcs_score': 78,
            'active_traders': 23,
            'seconds_remaining': 347
        },
        {
            'callsign': '🚀 ROCKET RIDE',
            'symbol': 'AUDUSD',
            'direction': 'BUY',
            'entry_price': 0.65420,
            'take_profit_pips': 22,
            'stop_loss_pips': 14,
            'tcs_score': 85,
            'active_traders': 31,
            'seconds_remaining': 180
        },
        {
            'callsign': '🎯 RUBBER BAND',
            'symbol': 'EURJPY',
            'direction': 'SELL',
            'entry_price': 145.250,
            'take_profit_pips': 18,
            'stop_loss_pips': 10,
            'tcs_score': 72,
            'active_traders': 14,
            'seconds_remaining': 420
        }
    ]
    
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
    
    print("📤 Sending alerts with buttons...")
    
    # Send arcade alerts
    for i, trade in enumerate(arcade_trades):
        try:
            # Use the cleaner arcade format
            message = TradeAlertTemplates.arcade_alert_final(trade)
            
            # Arcade buttons
            keyboard = [[
                InlineKeyboardButton("🔫 FIRE", callback_data=f"fire_{i}"),
                InlineKeyboardButton("📊 INTEL", callback_data=f"intel_{i}")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await bot.send_message(
                chat_id=CHAT_ID,
                text=message,
                reply_markup=reply_markup
            )
            
            print(f"✅ Sent: {trade['callsign']}")
            await asyncio.sleep(1.5)
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Send sniper alert
    try:
        message = TradeAlertTemplates.sniper_compact(sniper_data)
        
        # Sniper buttons
        keyboard = [[
            InlineKeyboardButton("🎯 EXECUTE", callback_data="execute_sniper"),
            InlineKeyboardButton("🚫 ABORT", callback_data="abort_sniper")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            reply_markup=reply_markup
        )
        
        print("✅ Sent: Sniper alert")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n✅ All alerts sent with buttons!")

if __name__ == "__main__":
    asyncio.run(send_alerts_with_buttons())