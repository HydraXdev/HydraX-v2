#!/usr/bin/env python3
# test_trade_alerts.py
# Test script to send trade alert mockups to Telegram

import asyncio
import os
from datetime import datetime
import time
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
import sys
sys.path.append('/root/HydraX-v2')
from config.telegram import TelegramConfig

# Import templates directly to avoid module issues
exec(open('/root/HydraX-v2/src/bitten_core/trade_alert_templates.py').read())

# Get credentials from config
BOT_TOKEN = TelegramConfig.BOT_TOKEN
CHAT_ID = str(TelegramConfig.MAIN_CHAT_ID)

async def send_alert_mockups():
    """Send all alert style mockups to Telegram"""
    
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        return
    
    bot = Bot(token=BOT_TOKEN)
    
    # Test data for different scenarios
    test_trades = [
        {
            'name': 'Arcade - Dawn Raid (London Breakout)',
            'data': {
                'callsign': '🌅 DAWN RAID',
                'symbol': 'EURUSD',
                'direction': 'BUY',
                'entry_price': 1.08450,
                'take_profit_pips': 15,
                'stop_loss_pips': 10,
                'tcs_score': 82,
                'active_traders': 17,
                'seconds_remaining': 272  # 4:32
            },
            'template': TradeAlertTemplates.tactical_sitrep
        },
        {
            'name': 'Arcade - Wall Defender (S/R Bounce)',
            'data': {
                'callsign': '🏰 WALL DEFENDER',
                'symbol': 'GBPUSD',
                'direction': 'SELL',
                'entry_price': 1.27850,
                'take_profit_pips': 20,
                'stop_loss_pips': 12,
                'tcs_score': 78,
                'active_traders': 23,
                'seconds_remaining': 347  # 5:47
            },
            'template': TradeAlertTemplates.tactical_sitrep
        },
        {
            'name': 'Arcade - Rocket Ride (Momentum)',
            'data': {
                'callsign': '🚀 ROCKET RIDE',
                'symbol': 'USDJPY',
                'direction': 'BUY',
                'entry_price': 110.250,
                'take_profit_pips': 25,
                'stop_loss_pips': 15,
                'tcs_score': 85,
                'active_traders': 31,
                'seconds_remaining': 420  # 7:00
            },
            'template': TradeAlertTemplates.tactical_hud_display
        },
        {
            'name': 'Arcade - Rubber Band (Mean Reversion)',
            'data': {
                'callsign': '🎯 RUBBER BAND',
                'symbol': 'AUDUSD',
                'direction': 'SELL',
                'entry_price': 0.65420,
                'take_profit_pips': 18,
                'stop_loss_pips': 10,
                'tcs_score': 72,
                'active_traders': 14,
                'seconds_remaining': 180  # 3:00
            },
            'template': TradeAlertTemplates.mission_alert_compact
        },
        {
            'name': 'Sniper Elite',
            'data': {
                'symbol': 'USDJPY',
                'direction': 'SELL',
                'entry_price': 110.250,
                'take_profit_pips': 35,
                'stop_loss_pips': 15,
                'tcs_score': 94,
                'active_traders': 8,
                'seconds_remaining': 495  # 8:15
            },
            'template': TradeAlertTemplates.sniper_elite
        },
        {
            'name': 'HUD Display - Dawn Raid',
            'data': {
                'callsign': '🌅 DAWN RAID',
                'symbol': 'XAUUSD',
                'direction': 'BUY',
                'entry_price': 1945.50,
                'take_profit_pips': 18,
                'stop_loss_pips': 12,
                'tcs_score': 88,
                'active_traders': 42,
                'seconds_remaining': 360  # 6:00
            },
            'template': TradeAlertTemplates.tactical_hud_display
        },
        {
            'name': 'Radar Sweep - Wall Defender',  
            'data': {
                'callsign': '🏰 WALL DEFENDER',
                'symbol': 'EURJPY',
                'direction': 'SELL',
                'entry_price': 145.250,
                'take_profit_pips': 22,
                'stop_loss_pips': 15,
                'tcs_score': 76,
                'active_traders': 19,
                'seconds_remaining': 240  # 4:00
            },
            'template': TradeAlertTemplates.radar_sweep_alert
        },
        {
            'name': 'Heat Map - Rocket Ride',
            'data': {
                'callsign': '🚀 ROCKET RIDE',
                'symbol': 'BTCUSD',
                'direction': 'BUY', 
                'entry_price': 42150.00,
                'take_profit_pips': 30,
                'stop_loss_pips': 20,
                'tcs_score': 91,
                'active_traders': 67,
                'seconds_remaining': 480  # 8:00
            },
            'template': TradeAlertTemplates.heat_map_alert
        }
    ]
    
    print("📤 Sending trade alert mockups to Telegram...")
    
    for i, test in enumerate(test_trades):
        try:
            # Generate alert message
            message = test['template'](test['data'])
            
            # Create inline keyboard
            if 'sniper' in test['name'].lower():
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
            
            # Send message
            await bot.send_message(
                chat_id=CHAT_ID,
                text=f"**Test Alert #{i+1}: {test['name']}**\n\n{message}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
            print(f"✅ Sent: {test['name']}")
            
            # Wait between messages
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"❌ Error sending {test['name']}: {e}")
    
    # Send an expired alert example
    print("\n📤 Sending expired alert example...")
    try:
        # Create an active alert first
        active_data = test_trades[0]['data'].copy()
        active_alert = TradeAlertTemplates.tactical_sitrep(active_data)
        
        # Convert to expired
        active_data['total_engaged'] = 47
        expired_alert = TradeAlertTemplates.expired_alert(active_alert, active_data)
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"**Test Alert #5: Expired (Social Proof)**\n\n{expired_alert}",
            parse_mode=ParseMode.MARKDOWN
        )
        print("✅ Sent: Expired alert example")
        
    except Exception as e:
        print(f"❌ Error sending expired alert: {e}")
    
    print("\n✅ All mockups sent! Check your Telegram group.")

async def test_countdown_animation():
    """Test countdown timer animation"""
    
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        return
    
    bot = Bot(token=BOT_TOKEN)
    
    # Create initial alert
    trade_data = {
        'callsign': 'ROGUE WAVE',
        'symbol': 'AUDUSD',
        'direction': 'BUY',
        'entry_price': 0.65420,
        'take_profit_pips': 18,
        'stop_loss_pips': 12,
        'tcs_score': 75,
        'active_traders': 12,
        'seconds_remaining': 60  # 1 minute for quick demo
    }
    
    # Send initial message
    message_text = TradeAlertTemplates.tactical_sitrep(trade_data)
    sent_message = await bot.send_message(
        chat_id=CHAT_ID,
        text=f"**Countdown Demo - Watch the timer!**\n\n{message_text}",
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Update countdown every 10 seconds
    for i in range(6):
        await asyncio.sleep(10)
        trade_data['seconds_remaining'] -= 10
        trade_data['active_traders'] += 2  # Simulate more traders joining
        
        updated_text = TradeAlertTemplates.tactical_sitrep(trade_data)
        
        try:
            await bot.edit_message_text(
                chat_id=CHAT_ID,
                message_id=sent_message.message_id,
                text=f"**Countdown Demo - Watch the timer!**\n\n{updated_text}",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            print(f"Update error: {e}")
    
    # Show expired version
    trade_data['total_engaged'] = trade_data['active_traders']
    expired_text = TradeAlertTemplates.expired_alert(message_text, trade_data)
    
    await bot.edit_message_text(
        chat_id=CHAT_ID,
        message_id=sent_message.message_id,
        text=f"**Countdown Demo - EXPIRED**\n\n{expired_text}",
        parse_mode=ParseMode.MARKDOWN
    )

if __name__ == "__main__":
    # Run the test
    print("🚀 BITTEN Trade Alert Mockup Test")
    print("=" * 40)
    
    # Choose what to test
    print("\nWhat would you like to test?")
    print("1. Send all alert mockups")
    print("2. Test countdown timer animation")
    print("3. Both")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        asyncio.run(send_alert_mockups())
    elif choice == "2":
        asyncio.run(test_countdown_animation())
    elif choice == "3":
        asyncio.run(send_alert_mockups())
        print("\n⏱️ Starting countdown demo in 5 seconds...")
        time.sleep(5)
        asyncio.run(test_countdown_animation())
    else:
        print("❌ Invalid choice")