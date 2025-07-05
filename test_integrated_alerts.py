#!/usr/bin/env python3
# Test integrated alert designs with special events

import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
import sys
sys.path.append('/root/HydraX-v2')
from config.telegram import TelegramConfig
from src.bitten_core.signal_display import SignalDisplay

BOT_TOKEN = TelegramConfig.BOT_TOKEN
CHAT_ID = str(TelegramConfig.MAIN_CHAT_ID)

async def send_integrated_alerts():
    """Send all integrated alert designs including special events"""
    
    bot = Bot(token=BOT_TOKEN)
    display = SignalDisplay()
    
    print("📤 Sending integrated alert designs with special events...")
    
    # Send intro
    intro = """🎯 **INTEGRATED ALERT SYSTEM LIVE**

✅ Approved arcade/sniper formats active
✅ Special event cards added
✅ Ready for production use"""
    
    await bot.send_message(chat_id=CHAT_ID, text=intro, parse_mode=ParseMode.MARKDOWN)
    await asyncio.sleep(1)
    
    # Test arcade signals
    arcade_signals = [
        {
            'callsign': '🌅 DAWN RAID',
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'entry_price': 1.08450,
            'expected_pips': 15,
            'risk_pips': 10,
            'tcs_score': 82,
            'active_traders': 17,
            'time_remaining': 272
        },
        {
            'callsign': '🏰 WALL DEFENDER',
            'symbol': 'GBPUSD',
            'direction': 'SELL',
            'entry_price': 1.27850,
            'expected_pips': 20,
            'risk_pips': 12,
            'tcs_score': 78,
            'active_traders': 23,
            'time_remaining': 347
        }
    ]
    
    print("\n📊 Sending arcade alerts...")
    for signal in arcade_signals:
        message = display.create_arcade_signal_card(signal)
        
        # Arcade buttons
        keyboard = [[
            InlineKeyboardButton("⚡ EXECUTE", callback_data=f"execute_arcade_{signal['symbol']}"),
            InlineKeyboardButton("📊 INTEL", callback_data=f"intel_arcade_{signal['symbol']}")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            reply_markup=reply_markup
        )
        
        print(f"✅ Sent: {signal['callsign']}")
        await asyncio.sleep(1.5)
    
    # Test sniper signals
    sniper_signals = [
        {
            'symbol': 'USDJPY',
            'direction': 'SELL',
            'entry_price': 110.250,
            'expected_pips': 35,
            'risk_pips': 15,
            'tcs_score': 94,
            'active_traders': 8,
            'time_remaining': 495
        },
        {
            'symbol': 'XAUUSD',
            'direction': 'BUY',
            'entry_price': 1945.50,
            'expected_pips': 40,
            'risk_pips': 20,
            'tcs_score': 91,
            'active_traders': 12,
            'time_remaining': 600
        }
    ]
    
    print("\n🎯 Sending sniper alerts...")
    for signal in sniper_signals:
        message = display.create_sniper_signal_card(signal)
        
        # Sniper buttons
        keyboard = [[
            InlineKeyboardButton("🎯 EXECUTE", callback_data=f"execute_sniper_{signal['symbol']}"),
            InlineKeyboardButton("📊 INTEL", callback_data=f"intel_sniper_{signal['symbol']}")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            reply_markup=reply_markup
        )
        
        print(f"✅ Sent: Sniper {signal['symbol']}")
        await asyncio.sleep(1.5)
    
    # Send special event separator
    await bot.send_message(
        chat_id=CHAT_ID,
        text="⚡ **SPECIAL EVENTS DETECTED** ⚡\n━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode=ParseMode.MARKDOWN
    )
    await asyncio.sleep(1)
    
    # Test Midnight Hammer
    print("\n🔨 Sending Midnight Hammer event...")
    hammer_signal = {
        'symbol': 'XAUUSD',
        'direction': 'BUY',
        'entry_price': 1948.75,
        'expected_pips': 100,
        'risk_pips': 50,
        'tcs_score': 96,
        'active_traders': 147,
        'seconds_remaining': 300
    }
    
    message = display.create_midnight_hammer_card(hammer_signal)
    
    keyboard = [[
        InlineKeyboardButton("🔨 JOIN THE HAMMER", callback_data="join_hammer"),
        InlineKeyboardButton("📊 VIEW STATS", callback_data="hammer_stats")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=message,
        reply_markup=reply_markup
    )
    print("✅ Sent: Midnight Hammer")
    await asyncio.sleep(2)
    
    # Test other special events
    special_events = [
        {
            'type': 'PERFECT_STORM',
            'signal': {
                'count': 3,
                'avg_tcs': 92,
                'total_pips': 150,
                'active_traders': 89
            }
        },
        {
            'type': 'BLOOD_MOON',
            'signal': {
                'symbol': 'EURJPY',
                'direction': 'SELL',
                'entry_price': 145.500,
                'expected_pips': 60,
                'risk_pips': 25,
                'tcs_score': 95
            }
        },
        {
            'type': 'GOLDEN_HOUR',
            'signal': {
                'symbol': 'GBPJPY',
                'direction': 'BUY',
                'entry_price': 155.250,
                'expected_pips': 45,
                'volatility': 'EXTREME'
            }
        },
        {
            'type': 'STEALTH_BOMB',
            'signal': {
                'tcs_score': 93,
                'expected_pips': 55
            }
        }
    ]
    
    print("\n🌟 Sending special event alerts...")
    for event in special_events:
        message = display.create_special_event_card(event['type'], event['signal'])
        
        # Special event buttons
        if event['type'] == 'PERFECT_STORM':
            keyboard = [[
                InlineKeyboardButton("⛈️ VIEW ALL", callback_data="storm_view"),
                InlineKeyboardButton("🎯 AUTO-FIRE", callback_data="storm_fire")
            ]]
        elif event['type'] == 'BLOOD_MOON':
            keyboard = [[
                InlineKeyboardButton("🩸 EXECUTE", callback_data="blood_moon_fire"),
                InlineKeyboardButton("📊 ANALYSIS", callback_data="blood_moon_intel")
            ]]
        elif event['type'] == 'GOLDEN_HOUR':
            keyboard = [[
                InlineKeyboardButton("✨ CAPTURE", callback_data="golden_fire"),
                InlineKeyboardButton("📈 VOLATILITY", callback_data="golden_vol")
            ]]
        else:  # STEALTH_BOMB
            keyboard = [[
                InlineKeyboardButton("💣 DETONATE", callback_data="stealth_fire"),
                InlineKeyboardButton("🔍 REVEAL", callback_data="stealth_reveal")
            ]]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            reply_markup=reply_markup
        )
        
        print(f"✅ Sent: {event['type']}")
        await asyncio.sleep(2)
    
    # Final summary
    summary = """✅ **INTEGRATION COMPLETE**

**Live Formats:**
• Arcade: 5-line compact with ⚡ EXECUTE
• Sniper: 6-line classified with 🎯 EXECUTE
• Midnight Hammer: Special border effects
• Rare Events: 4 unique templates

**Next Steps:**
• Monitor performance
• Gather squad feedback
• Track engagement metrics"""
    
    await bot.send_message(chat_id=CHAT_ID, text=summary, parse_mode=ParseMode.MARKDOWN)
    
    print("\n✅ All integrated designs sent successfully!")

if __name__ == "__main__":
    asyncio.run(send_integrated_alerts())