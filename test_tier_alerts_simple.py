#!/usr/bin/env python3
"""Simple test for tiered alerts showing data visibility differences"""

import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

# Bot configuration
BOT_TOKEN = "7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ"
CHAT_ID = -1002581996861

async def send_all_tier_alerts():
    """Send alerts for all tiers to show data visibility differences"""
    bot = Bot(token=BOT_TOKEN)
    
    # NIBBLER Alert (40% data visible)
    nibbler_message = """🟢 **NIBBLER ALERT**
━━━━━━━━━━━━━━━━━━
📍 EURUSD | Direction: BUY
💰 Entry: ~1.08XX area
🎯 Target: [LOCKED - UPGRADE]
⚡ Confidence: [LOCKED]
📊 Risk/Reward: [LOCKED]

_Only basic direction shown_"""
    
    nibbler_keyboard = [
        [InlineKeyboardButton("🔓 UPGRADE TO SEE MORE", url="https://t.me/bitten_bot?start=upgrade")]
    ]
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=nibbler_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(nibbler_keyboard)
    )
    await asyncio.sleep(2)
    
    # FANG Alert (60% data visible)
    fang_message = """🔵 **FANG ALERT** 
━━━━━━━━━━━━━━━━━━
📍 EURUSD | Direction: BUY 📈
💰 Entry: 1.0823
🎯 Target: 1.0853 (+30 pips)
⚡ TCS Score: 85%
📊 Risk/Reward: 1:2

🔒 _Stop Loss: [COMMANDER+]_
🔒 _Network Data: [COMMANDER+]_
🔒 _Pattern: [COMMANDER+]_"""
    
    fang_keyboard = [
        [InlineKeyboardButton("📊 VIEW DETAILS", callback_data="fang_details")],
        [InlineKeyboardButton("🔓 UPGRADE TO COMMANDER", url="https://t.me/bitten_bot?start=upgrade")]
    ]
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=fang_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(fang_keyboard)
    )
    await asyncio.sleep(2)
    
    # COMMANDER Alert (85% data visible)
    commander_message = """🟡 **COMMANDER ALERT**
━━━━━━━━━━━━━━━━━━
📍 EURUSD | BUY 📈 | Pattern: Bull Flag
💰 Entry: 1.0823 | Stop: 1.0803
🎯 TP1: 1.0843 | TP2: 1.0853 | TP3: 1.0863
⚡ TCS: 91% | Confluence: 5/5
📊 Risk/Reward: 1:3

👥 Squad: 87% positioned
📈 30-day edge: 83% win rate
💎 Smart money: Accumulating

🔒 _Quantum metrics: [APEX ONLY]_
🔒 _AI prediction: [APEX ONLY]_"""
    
    commander_keyboard = [
        [InlineKeyboardButton("💎 FULL INTEL", callback_data="commander_intel")],
        [InlineKeyboardButton("👥 SQUAD VIEW", callback_data="squad")]
    ]
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=commander_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(commander_keyboard)
    )
    await asyncio.sleep(2)
    
    # Comparison Summary
    summary_message = """📊 **DATA VISIBILITY SUMMARY**
━━━━━━━━━━━━━━━━━━

**What NIBBLER sees (40%):**
✅ Basic direction
✅ Approximate entry area
❌ No targets, stops, or confidence

**What FANG sees (60%):**
✅ Exact entry & target
✅ TCS confidence score
✅ Basic risk/reward
❌ No stop loss or advanced data

**What COMMANDER sees (85%):**
✅ All price levels & multiple targets
✅ Pattern recognition
✅ Squad performance
✅ Historical edge data
❌ No quantum/AI metrics

**What APEX sees (100%):**
✅ Everything above PLUS
✅ Quantum probability clouds
✅ AI predictive models
✅ Reality distortion metrics
✅ Collective consciousness data

_Each tier reveals more strategic intelligence!_"""
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=summary_message,
        parse_mode=ParseMode.MARKDOWN
    )
    
    print("✅ All tier comparison alerts sent!")

async def main():
    """Run the test"""
    print("🚀 Sending tier comparison alerts...")
    print("=" * 50)
    
    await send_all_tier_alerts()
    
    print("\n✅ Check your Telegram group to see the data visibility differences!")
    print("Notice how each tier reveals progressively more trading intelligence.")

if __name__ == "__main__":
    asyncio.run(main())