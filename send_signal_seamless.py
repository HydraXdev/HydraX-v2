#!/usr/bin/env python3
"""Send BITTEN signal with seamless Telegram experience"""

import asyncio
import json
import time
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

# Configuration
BOT_TOKEN = '7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ'
CHAT_ID = -1002581996861

async def send_seamless_signal():
    """Send signal with callback buttons for instant response"""
    bot = Bot(token=BOT_TOKEN)
    
    # Brief signal alert
    signal_message = """⚡ **SIGNAL DETECTED**
EUR/USD | BUY | 87% confidence
⏰ Expires in 10 minutes"""

    # Signal ID for tracking
    signal_id = f'sig_{int(time.time())}'
    
    # Create inline keyboard with callback buttons
    keyboard = [
        [
            InlineKeyboardButton("🎯 VIEW INTEL", callback_data=f"view_{signal_id}"),
            InlineKeyboardButton("🔫 QUICK FIRE", callback_data=f"fire_{signal_id}")
        ],
        [
            InlineKeyboardButton("📊 MORE INFO", callback_data=f"info_{signal_id}")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        message = await bot.send_message(
            chat_id=CHAT_ID,
            text=signal_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        print(f"✅ Seamless signal sent!")
        print(f"Message ID: {message.message_id}")
        print(f"\n📱 User Experience:")
        print(f"- Instant response when buttons clicked")
        print(f"- No external links needed")
        print(f"- All within Telegram")
        
    except Exception as e:
        print(f"❌ Error: {e}")

async def send_full_intel_signal():
    """Send signal that expands to show full intel inline"""
    bot = Bot(token=BOT_TOKEN)
    
    # Initial brief message
    brief_message = """⚡ **SIGNAL DETECTED**
EUR/USD | BUY | 87% confidence
⏰ Expires in 10 minutes"""

    # Full intel (hidden initially)
    full_intel = """⚡ **TACTICAL MISSION BRIEF** ⚡
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 **Asset:** EUR/USD
💹 **Direction:** BUY
🎯 **Entry:** 1.0850
🛡️ **Stop Loss:** 1.0830 (-20 pips)
🎖️ **Take Profit:** 1.0880 (+30 pips)
📊 **R:R Ratio:** 1:1.5

**📈 Technical Analysis:**
• RSI: Oversold bounce
• MA Cross: Bullish signal
• Support: Strong at 1.0840

**⚠️ Risk Factors:**
• News in 2 hours
• Daily limit: 50% used

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ready to execute?"""

    # Keyboard for expanded view
    expanded_keyboard = [
        [
            InlineKeyboardButton("🔫 EXECUTE TRADE", callback_data="execute_trade"),
            InlineKeyboardButton("❌ SKIP", callback_data="skip_trade")
        ],
        [
            InlineKeyboardButton("📊 VIEW CHART", url="https://www.tradingview.com/x/ABC123/")
        ]
    ]
    
    # Send with expanding message approach
    keyboard = [[
        InlineKeyboardButton("🔽 EXPAND INTEL", callback_data="expand_intel")
    ]]
    
    message = await bot.send_message(
        chat_id=CHAT_ID,
        text=brief_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    print("✅ Expandable signal sent!")
    print("When user clicks EXPAND INTEL, the message updates to show full details")

async def send_instant_action_signal():
    """Send signal with instant action buttons"""
    bot = Bot(token=BOT_TOKEN)
    
    signal_data = {
        'symbol': 'EUR/USD',
        'direction': 'BUY',
        'entry': 1.0850,
        'sl': 1.0830,
        'tp': 1.0880,
        'confidence': 87,
        'risk_reward': '1:1.5'
    }
    
    # Format signal with essential info visible
    signal_message = f"""⚡ **SIGNAL: {signal_data['symbol']}**
━━━━━━━━━━━━━━━━━━━━━━━━
Direction: **{signal_data['direction']}** @ {signal_data['entry']}
SL: {signal_data['sl']} | TP: {signal_data['tp']}
Risk/Reward: {signal_data['risk_reward']}
Confidence: {signal_data['confidence']}%
━━━━━━━━━━━━━━━━━━━━━━━━

⏰ Quick decision required!"""

    # Action buttons
    keyboard = [
        [
            InlineKeyboardButton("🟢 TAKE TRADE", callback_data=f"take_{json.dumps(signal_data)}"),
        ],
        [
            InlineKeyboardButton("0.01 lot", callback_data="lot_0.01"),
            InlineKeyboardButton("0.05 lot", callback_data="lot_0.05"),
            InlineKeyboardButton("0.10 lot", callback_data="lot_0.10"),
        ],
        [
            InlineKeyboardButton("🔴 SKIP", callback_data="skip")
        ]
    ]
    
    message = await bot.send_message(
        chat_id=CHAT_ID,
        text=signal_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    print("✅ Instant action signal sent!")
    print("User can execute trade with one click!")

if __name__ == "__main__":
    print("🚀 BITTEN Seamless Signal Test")
    print("=" * 50)
    print("This creates a smooth experience within Telegram")
    print("No external links or webapps needed!")
    print("=" * 50)
    
    # Send the seamless signal
    asyncio.run(send_seamless_signal())