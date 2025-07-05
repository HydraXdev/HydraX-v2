#!/usr/bin/env python3
# Test tactical compact alerts

import asyncio
from telegram import Bot
from telegram.constants import ParseMode
import sys
sys.path.append('/root/HydraX-v2')
from config.telegram import TelegramConfig

# Import templates
exec(open('/root/HydraX-v2/src/bitten_core/trade_alert_templates.py').read())

BOT_TOKEN = TelegramConfig.BOT_TOKEN
CHAT_ID = str(TelegramConfig.MAIN_CHAT_ID)

async def send_tactical_alerts():
    """Send compact tactical alerts without buttons"""
    
    bot = Bot(token=BOT_TOKEN)
    
    # Test data
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
    
    print("📤 Sending tactical compact alerts...")
    
    # Send different styles
    alerts = [
        ("STYLE 1: Ultra Compact", TradeAlertTemplates.tactical_compact(arcade_data)),
        ("STYLE 2: Military Brief", TradeAlertTemplates.military_brief(arcade_data)),
        ("STYLE 3: Radio Transmission", TradeAlertTemplates.radio_transmission(arcade_data)),
        ("STYLE 4: Sniper Compact", TradeAlertTemplates.sniper_compact(sniper_data)),
        
        # Multiple arcade examples
        ("", ""),  # Separator
        ("ARCADE EXAMPLES:", ""),
        ("", TradeAlertTemplates.tactical_compact({
            'callsign': '🏰 WALL DEFENDER',
            'symbol': 'GBPUSD',
            'direction': 'SELL',
            'entry_price': 1.27850,
            'take_profit_pips': 20,
            'stop_loss_pips': 12,
            'tcs_score': 78,
            'active_traders': 23,
            'seconds_remaining': 347
        })),
        ("", TradeAlertTemplates.tactical_compact({
            'callsign': '🚀 ROCKET RIDE',
            'symbol': 'AUDUSD',
            'direction': 'BUY',
            'entry_price': 0.65420,
            'take_profit_pips': 22,
            'stop_loss_pips': 14,
            'tcs_score': 85,
            'active_traders': 31,
            'seconds_remaining': 180
        })),
        ("", TradeAlertTemplates.tactical_compact({
            'callsign': '🎯 RUBBER BAND',
            'symbol': 'EURJPY',
            'direction': 'SELL',
            'entry_price': 145.250,
            'take_profit_pips': 18,
            'stop_loss_pips': 10,
            'tcs_score': 72,
            'active_traders': 14,
            'seconds_remaining': 420
        }))
    ]
    
    # Send alerts
    for title, alert in alerts:
        try:
            if title and alert:
                message = f"**{title}**\n\n{alert}"
            elif title:
                message = f"**{title}**"
            elif alert:
                message = alert
            else:
                continue
                
            await bot.send_message(
                chat_id=CHAT_ID,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            
            if title:
                print(f"✅ Sent: {title}")
            
            await asyncio.sleep(1.5)
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Send comparison message
    comparison = """📊 **DESIGN NOTES:**

• No boxes or borders
• No inline buttons
• Fits mobile screens
• Military terminology
• Essential info only
• Clear hierarchy

Reply with which style works best!"""
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=comparison,
        parse_mode=ParseMode.MARKDOWN
    )
    
    print("\n✅ Tactical alerts sent!")

if __name__ == "__main__":
    asyncio.run(send_tactical_alerts())