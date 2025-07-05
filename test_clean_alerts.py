#!/usr/bin/env python3
# Test cleaner alert designs

import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
import sys
sys.path.append('/root/HydraX-v2')
from config.telegram import TelegramConfig

# Import templates directly
exec(open('/root/HydraX-v2/src/bitten_core/trade_alert_templates.py').read())

# Get credentials
BOT_TOKEN = TelegramConfig.BOT_TOKEN
CHAT_ID = str(TelegramConfig.MAIN_CHAT_ID)

async def send_clean_alerts():
    """Send cleaner alert designs"""
    
    bot = Bot(token=BOT_TOKEN)
    
    # Test different clean styles
    test_alerts = [
        {
            'name': 'Clean Arcade - Dawn Raid',
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
            },
            'template': TradeAlertTemplates.clean_arcade_alert
        },
        {
            'name': 'Clean Arcade - Wall Defender',
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
            },
            'template': TradeAlertTemplates.tactical_sitrep
        },
        {
            'name': 'Sniper with Crosshair',
            'data': {
                'symbol': 'USDJPY',
                'direction': 'SELL',
                'entry_price': 110.250,
                'take_profit_pips': 35,
                'stop_loss_pips': 15,
                'tcs_score': 94,
                'active_traders': 8,
                'seconds_remaining': 495
            },
            'template': TradeAlertTemplates.sniper_crosshair_alert
        },
        {
            'name': 'Clean Sniper Alternative',
            'data': {
                'symbol': 'XAUUSD',
                'direction': 'BUY',
                'entry_price': 1945.50,
                'take_profit_pips': 30,
                'stop_loss_pips': 18,
                'tcs_score': 91,
                'active_traders': 12,
                'seconds_remaining': 420
            },
            'template': TradeAlertTemplates.sniper_elite
        },
        {
            'name': 'Minimal Arcade - Rocket Ride',
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
            },
            'template': TradeAlertTemplates.mission_alert_compact
        }
    ]
    
    print("📤 Sending cleaner alert designs...")
    
    # Send intro message
    intro = """🎯 **CLEANER ALERT DESIGNS**

Here are the updated alerts with:
• Minimal dividing lines
• Simple borders for arcade alerts
• Different borders for sniper alerts
• Crosshair overlay option for snipers
• Less visual clutter overall"""
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=intro,
        parse_mode=ParseMode.MARKDOWN
    )
    
    await asyncio.sleep(1)
    
    for i, alert in enumerate(test_alerts):
        try:
            message = alert['template'](alert['data'])
            
            # Create appropriate keyboard
            if 'sniper' in alert['name'].lower():
                keyboard = [[
                    InlineKeyboardButton("🎯 EXECUTE", callback_data=f"execute_{i}"),
                    InlineKeyboardButton("🚫 ABORT", callback_data=f"abort_{i}")
                ]]
            else:
                keyboard = [[
                    InlineKeyboardButton("🔫 ENGAGE", callback_data=f"engage_{i}"),
                    InlineKeyboardButton("📊 INTEL", callback_data=f"intel_{i}")
                ]]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Add title
            full_message = f"**{alert['name']}**\n\n{message}"
            
            await bot.send_message(
                chat_id=CHAT_ID,
                text=full_message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
            print(f"✅ Sent: {alert['name']}")
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"❌ Error sending {alert['name']}: {e}")
    
    print("\n✅ Clean designs sent!")

if __name__ == "__main__":
    asyncio.run(send_clean_alerts())