#!/usr/bin/env python3
# Final alert design with EXECUTE buttons

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

async def send_final_alerts():
    """Send final alert designs with EXECUTE buttons"""
    
    bot = Bot(token=BOT_TOKEN)
    
    # Test data
    arcade_trades = [
        {
            'name': '🌅 DAWN RAID',
            'data': {
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
        },
        {
            'name': '🏰 WALL DEFENDER',
            'data': {
                'callsign': '🏰 WALL DEFENDER',
                'symbol': 'GBPUSD',
                'direction': 'SELL',
                'entry_price': 1.27850,
                'take_profit_pips': 20,
                'stop_loss_pips': 12,
                'tcs_score': 78,
                'active_traders': 23,
                'seconds_remaining': 347
            }
        },
        {
            'name': '🚀 ROCKET RIDE',
            'data': {
                'callsign': '🚀 ROCKET RIDE',
                'symbol': 'AUDUSD',
                'direction': 'BUY',
                'entry_price': 0.65420,
                'take_profit_pips': 22,
                'stop_loss_pips': 14,
                'tcs_score': 85,
                'active_traders': 31,
                'seconds_remaining': 180
            }
        },
        {
            'name': '🎯 RUBBER BAND',
            'data': {
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
        }
    ]
    
    sniper_trades = [
        {
            'symbol': 'USDJPY',
            'direction': 'SELL',
            'entry_price': 110.250,
            'take_profit_pips': 35,
            'stop_loss_pips': 15,
            'tcs_score': 94,
            'active_traders': 8,
            'seconds_remaining': 495
        },
        {
            'symbol': 'XAUUSD',
            'direction': 'BUY',
            'entry_price': 1945.50,
            'take_profit_pips': 40,
            'stop_loss_pips': 20,
            'tcs_score': 91,
            'active_traders': 12,
            'seconds_remaining': 600
        }
    ]
    
    print("📤 Sending final alert designs...")
    
    # Send intro
    intro = """🎯 **FINAL ALERT DESIGNS**

• EXECUTE button for all (⚡ arcade, 🎯 sniper)
• INTEL button for both types
• No ABORT button (less clutter)
• Tier restrictions apply"""
    
    await bot.send_message(chat_id=CHAT_ID, text=intro, parse_mode=ParseMode.MARKDOWN)
    await asyncio.sleep(1)
    
    # Send arcade alerts
    for trade in arcade_trades:
        try:
            message = TradeAlertTemplates.arcade_alert_final(trade['data'])
            
            # Arcade buttons with lightning bolt
            keyboard = [[
                InlineKeyboardButton("⚡ EXECUTE", callback_data=f"execute_{trade['name']}"),
                InlineKeyboardButton("📊 INTEL", callback_data=f"intel_{trade['name']}")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await bot.send_message(
                chat_id=CHAT_ID,
                text=message,
                reply_markup=reply_markup
            )
            
            print(f"✅ Sent: {trade['name']}")
            await asyncio.sleep(1.5)
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Send sniper alerts
    for i, trade in enumerate(sniper_trades):
        try:
            message = TradeAlertTemplates.sniper_compact(trade)
            
            # Sniper buttons with bullseye
            keyboard = [[
                InlineKeyboardButton("🎯 EXECUTE", callback_data=f"execute_sniper_{i}"),
                InlineKeyboardButton("📊 INTEL", callback_data=f"intel_sniper_{i}")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await bot.send_message(
                chat_id=CHAT_ID,
                text=message,
                reply_markup=reply_markup
            )
            
            print(f"✅ Sent: Sniper {i+1}")
            await asyncio.sleep(1.5)
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Send tier restriction note
    note = """📌 **TIER RESTRICTIONS:**

**Arcade Signals:**
• Nibbler ($39) - Can EXECUTE
• All tiers can view INTEL

**Sniper Signals:** 
• Only Fang+ ($89+) can EXECUTE
• Lower tiers see "Upgrade Required"
• All tiers can view INTEL"""
    
    await bot.send_message(chat_id=CHAT_ID, text=note, parse_mode=ParseMode.MARKDOWN)
    
    print("\n✅ Final designs sent!")

if __name__ == "__main__":
    asyncio.run(send_final_alerts())