#!/usr/bin/env python3
"""Test tiered WebApp alerts with different data visibility"""

import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
import urllib.parse

# Bot configuration
BOT_TOKEN = "7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ"
CHAT_ID = -1002581996861
WEBAPP_BASE_URL = "https://t.me/bitten_bot/webapp"

async def send_nibbler_alert():
    """Send NIBBLER tier alert (40% data visible)"""
    bot = Bot(token=BOT_TOKEN)
    
    # Create WebApp data
    webapp_data = {
        "tier": "nibbler",
        "signal_id": "SIG-12345",
        "symbol": "EURUSD",
        "direction": "BUY",
        "tcs": 72,
        "user_id": "test_user"
    }
    webapp_url = f"{WEBAPP_BASE_URL}?data={urllib.parse.quote(str(webapp_data))}"
    
    # Shortened alert message (40% data)
    message = """🟢 **NIBBLER ARCADE** | EURUSD
Direction: BUY 📈
Confidence: [LOCKED]
Target: [UPGRADE TO VIEW]

⏱️ Window: 15 min"""
    
    # Create inline keyboard with WebApp button
    keyboard = [
        [InlineKeyboardButton("📊 VIEW MISSION BRIEF", web_app={"url": webapp_url})],
        [InlineKeyboardButton("🔓 UPGRADE TO FANG", url="https://t.me/bitten_bot?start=upgrade")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )
    print("✅ Sent NIBBLER alert (40% data visible)")

async def send_fang_alert():
    """Send FANG tier alert (60% data visible)"""
    bot = Bot(token=BOT_TOKEN)
    
    # Create WebApp data
    webapp_data = {
        "tier": "fang",
        "signal_id": "SIG-23456",
        "symbol": "GBPUSD",
        "direction": "SELL",
        "entry": 1.2750,
        "stop": 1.2770,
        "target": 1.2720,
        "tcs": 85,
        "user_id": "test_user"
    }
    webapp_url = f"{WEBAPP_BASE_URL}?data={urllib.parse.quote(str(webapp_data))}"
    
    # More detailed alert (60% data)
    message = """🔵 **FANG TACTICAL** | GBPUSD
Direction: SELL 📉
Entry Zone: 1.2750
TCS Score: 85% 🎯
Target: +30 pips

⏱️ Window: 20 min
🔥 Network: 73% taking position"""
    
    keyboard = [
        [InlineKeyboardButton("🎯 ENTER BRIEFING", web_app={"url": webapp_url})],
        [InlineKeyboardButton("📊 MY STATS", callback_data="stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )
    print("✅ Sent FANG alert (60% data visible)")

async def send_commander_alert():
    """Send COMMANDER tier alert (85% data visible)"""
    bot = Bot(token=BOT_TOKEN)
    
    # Create WebApp data
    webapp_data = {
        "tier": "commander",
        "signal_id": "SIG-34567",
        "symbol": "XAUUSD",
        "direction": "BUY",
        "entry": 1825.50,
        "stop": 1823.00,
        "target1": 1828.00,
        "target2": 1830.50,
        "target3": 1833.00,
        "tcs": 94,
        "pattern": "Bullish Flag",
        "confluence": 5,
        "user_id": "test_user"
    }
    webapp_url = f"{WEBAPP_BASE_URL}?data={urllib.parse.quote(str(webapp_data))}"
    
    # Highly detailed alert (85% data)
    message = """🟡 **COMMANDER ELITE** | XAUUSD
Direction: BUY 📈 | Pattern: Bullish Flag
Entry: $1825.50 | Stop: $1823.00
TP1: $1828.00 | TP2: $1830.50 | TP3: $1833.00
TCS: 94% 🔥 | Confluence: 5/5
Risk/Reward: 1:3.4

⏱️ Window: 30 min | Volatility: HIGH
👥 Squad: 89% positioned | Avg Entry: $1825.20
💎 Edge: This setup hit 87% last 30 days"""
    
    keyboard = [
        [InlineKeyboardButton("💎 ACCESS INTEL", web_app={"url": webapp_url})],
        [InlineKeyboardButton("👥 SQUAD VIEW", callback_data="squad")],
        [InlineKeyboardButton("📈 MY PERFORMANCE", callback_data="performance")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )
    print("✅ Sent COMMANDER alert (85% data visible)")

async def send_comparison_message():
    """Send a comparison message explaining data visibility"""
    bot = Bot(token=BOT_TOKEN)
    
    message = """📊 **DATA VISIBILITY BY TIER:**

**NIBBLER (40% visible):**
• Basic direction only
• No exact prices
• No confidence scores
• No network data

**FANG (60% visible):**
• Entry zones shown
• TCS scores revealed
• Basic network sentiment
• Single target levels

**COMMANDER (85% visible):**
• All price levels
• Multiple targets
• Pattern recognition
• Squad performance
• Historical edge data
• Confluence factors

**APEX (100% visible):**
• Everything above PLUS
• Quantum metrics
• AI predictions
• Insider flow
• Reality distortion index

Click the WebApp buttons above to see the difference! ☝️"""
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=message,
        parse_mode=ParseMode.MARKDOWN
    )
    print("✅ Sent comparison message")

async def main():
    """Send all test alerts"""
    print("🚀 Sending tiered WebApp test alerts...")
    print("=" * 50)
    
    # Send alerts with delays
    await send_nibbler_alert()
    await asyncio.sleep(2)
    
    await send_fang_alert()
    await asyncio.sleep(2)
    
    await send_commander_alert()
    await asyncio.sleep(2)
    
    await send_comparison_message()
    
    print("\n✅ All test alerts sent! Check your Telegram group.")
    print("Click the WebApp buttons to see the different data visibility levels.")

if __name__ == "__main__":
    asyncio.run(main())