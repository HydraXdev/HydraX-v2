#!/usr/bin/env python3
"""Corrected tier alerts - all tiers see essential trading data"""

import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

# Bot configuration
BOT_TOKEN = "7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ"
CHAT_ID = -1002581996861

async def send_corrected_tier_alerts():
    """Send corrected alerts where all tiers see essential data"""
    bot = Bot(token=BOT_TOKEN)
    
    # NIBBLER Alert - Shows ALL essential trading info
    nibbler_message = """🟢 **NIBBLER ALERT**
━━━━━━━━━━━━━━━━━━
📍 EURUSD | BUY 📈
💰 Entry: 1.0823
🛡️ Risk: -20p | 🎯 Target: +30p
⚡ TCS: 72% (Good setup!)
📊 Risk/Reward: 1:1.5

_Learn to wait for 85%+ setups_
_AI Analysis: [FANG+ ONLY]_"""
    
    nibbler_keyboard = [
        [InlineKeyboardButton("📊 VIEW MISSION", callback_data="nibbler_mission")],
        [InlineKeyboardButton("🔓 UNLOCK AI INSIGHTS", url="https://t.me/bitten_bot?start=upgrade")]
    ]
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=nibbler_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(nibbler_keyboard)
    )
    await asyncio.sleep(2)
    
    # FANG Alert - Adds AI predictions
    fang_message = """🔵 **FANG ALERT** 
━━━━━━━━━━━━━━━━━━
📍 EURUSD | BUY 📈 | Pattern: Bull Flag
💰 Entry: 1.0823 | SL: -20p | TP: +35p
⚡ TCS: 85% (High confidence!)
📊 R/R: 1:1.75 | Win Rate: 73%

🤖 **AI Prediction**: 82% success probability
📈 Momentum: Building (score: 7.5/10)
⏱️ Optimal window: Next 45 min

🔒 _Spotter Analysis: [COMMANDER+]_
🔒 _Squad Data: [COMMANDER+]_"""
    
    fang_keyboard = [
        [InlineKeyboardButton("🎯 ENTER BRIEFING", callback_data="fang_brief")],
        [InlineKeyboardButton("🤖 AI DETAILS", callback_data="ai_analysis")]
    ]
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=fang_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(fang_keyboard)
    )
    await asyncio.sleep(2)
    
    # COMMANDER Alert - Adds Spotter confirmation & squad data
    commander_message = """🟡 **COMMANDER ALERT**
━━━━━━━━━━━━━━━━━━
📍 EURUSD | BUY 📈 | Pattern: Bull Flag
💰 Entry: 1.0823 | SL: -20p (-$100)
🎯 TP1: +20p | TP2: +35p | TP3: +50p
⚡ TCS: 91% | Confluence: 5/5
📊 R/R: 1:2.5 | Historical: 83% wins

🎯 **SPOTTER CONFIRMED**: All systems aligned
🤖 **AI**: 89% success | Grok confidence: HIGH
👥 **Squad**: 87% positioned @ 1.0821
📈 **Smart Money**: Accumulating (85% buy flow)

🔒 _Quantum Probability: [APEX ONLY]_
🔒 _Reality Distortion: [APEX ONLY]_"""
    
    commander_keyboard = [
        [InlineKeyboardButton("💎 FULL INTEL", callback_data="commander_intel")],
        [InlineKeyboardButton("👥 SQUAD VIEW", callback_data="squad")],
        [InlineKeyboardButton("🎯 SPOTTER DATA", callback_data="spotter")]
    ]
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=commander_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(commander_keyboard)
    )
    await asyncio.sleep(2)
    
    # APEX Alert - Same as Commander + Quantum/Reality metrics
    apex_message = """🔴 **APEX ALERT**
━━━━━━━━━━━━━━━━━━
📍 EURUSD | BUY 📈 | Pattern: Bull Flag
💰 Entry: 1.0823 | SL: -20p (-$200)
🎯 TP1: +20p | TP2: +35p | TP3: +50p
⚡ TCS: 94% | Confluence: 6/6
📊 R/R: 1:2.5 | Historical: 87% wins

🎯 **SPOTTER**: Triple confirmation ✓✓✓
🤖 **AI**: 92% success | Grok: VERY HIGH
👥 **Squad**: 91% positioned @ 1.0821
📈 **Smart Money**: Heavy accumulation

🌌 **QUANTUM PROBABILITY**: 94.7%
🔮 **REALITY DISTORTION**: Level 3 (Market bending to pattern)
⚛️ **Quantum State**: Collapsing to profit
🧠 **Collective Consciousness**: Aligned"""
    
    apex_keyboard = [
        [InlineKeyboardButton("🔮 QUANTUM VIEW", callback_data="quantum")],
        [InlineKeyboardButton("🌌 REALITY MATRIX", callback_data="reality")],
        [InlineKeyboardButton("💎 EXECUTE", callback_data="apex_fire")]
    ]
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=apex_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(apex_keyboard)
    )
    await asyncio.sleep(2)
    
    # Updated Summary
    summary_message = """📊 **CORRECTED DATA ACCESS**
━━━━━━━━━━━━━━━━━━

**ALL TIERS GET:**
✅ Entry, Stop Loss, Take Profit
✅ TCS confidence scores
✅ Risk/Reward ratios
✅ Basic win rate data

**TIER PROGRESSION:**

**NIBBLER** → Learn patience, wait for high TCS
**FANG** → Unlock AI predictions & momentum
**COMMANDER** → Get Spotter confirmation & squad data  
**APEX** → Access quantum probability & reality metrics

_Everyone trades with full information._
_Higher tiers get better edge confirmation!_"""
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=summary_message,
        parse_mode=ParseMode.MARKDOWN
    )
    
    print("✅ All corrected tier alerts sent!")

async def main():
    """Run the corrected test"""
    print("🚀 Sending CORRECTED tier alerts...")
    print("=" * 50)
    
    await send_corrected_tier_alerts()
    
    print("\n✅ Check Telegram - ALL tiers now see essential trading data!")
    print("Higher tiers get confirmation tools, not basic info gatekeeping.")

if __name__ == "__main__":
    asyncio.run(main())