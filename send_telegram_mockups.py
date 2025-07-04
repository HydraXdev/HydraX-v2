#!/usr/bin/env python3
"""
Send tactical signal mockups to Telegram
"""

import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot
from telegram.constants import ParseMode

# Load environment variables
load_dotenv()

# Get bot token and chat ID
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_GROUP_ID')

async def send_mockups():
    """Send all signal mockups to Telegram"""
    
    bot = Bot(token=BOT_TOKEN)
    
    print("🚀 Sending tactical signal mockups to Telegram...")
    
    # 1. Intro message
    intro = """🎖️ **TACTICAL SIGNAL DISPLAY MOCKUPS** 🎖️
═══════════════════════════════════════

Testing new military-themed signal displays with:
• SITREP-style briefings
• Expiry countdown bars
• Squad engagement tracking
• Risk/Reward ratios
• Tactical callsigns"""
    
    await bot.send_message(chat_id=CHAT_ID, text=intro, parse_mode=ParseMode.MARKDOWN)
    await asyncio.sleep(2)
    
    # 2. Arcade Signal
    arcade_signal = """⚡ **TACTICAL SITREP** - ARCADE SCALP ⚡
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎮 **OP: DAWN RAID**
📍 **AO:** EURUSD | **VECTOR:** BUY
🎯 **ENTRY:** 1.08234
💥 **OBJECTIVE:** +12 PIPS
⚔️ **RISK:** 3 PIPS

📊 **INTEL CONFIDENCE:** 78%
█████░░░░ GOOD

⏱️ **OP WINDOW:** 🟩🟩🟩🟩🟩 HOT
👥 **SQUAD ENGAGED:** 23 OPERATORS

[🔫 **ENGAGE TARGET**] [📋 **VIEW INTEL**]"""
    
    await bot.send_message(chat_id=CHAT_ID, text="**1️⃣ ARCADE SIGNAL - SITREP STYLE:**", parse_mode=ParseMode.MARKDOWN)
    await bot.send_message(chat_id=CHAT_ID, text=arcade_signal, parse_mode=ParseMode.MARKDOWN)
    await asyncio.sleep(3)
    
    # 3. Sniper Signal
    sniper_signal = """🎯 **[CLASSIFIED]** SNIPER ENGAGEMENT 🎯
══════════════════════════════════════

**MISSION BRIEF:**
• **TARGET:** GBPUSD - SELL
• **ENTRY VECTOR:** 1.26789
• **OBJECTIVE:** +25 PIPS CONFIRMED
• **COLLATERAL:** 5 PIPS MAX
• **R:R RATIO:** 1:5

**TACTICAL INTEL:**
• **CONFIDENCE:** 92% [ELITE]
• **OP WINDOW:** 🟩🟩🟩🟩⬜ ACTIVE
• **SNIPERS ENGAGED:** 12 🎯
• **SQUAD AVG TCS:** 88%

⚡ **FANG+ CLEARANCE REQUIRED** ⚡

[🎯 **TAKE THE SHOT**] [🔍 **RECON**]"""
    
    await bot.send_message(chat_id=CHAT_ID, text="**2️⃣ SNIPER SIGNAL - ELITE BRIEFING:**", parse_mode=ParseMode.MARKDOWN)
    await bot.send_message(chat_id=CHAT_ID, text=sniper_signal, parse_mode=ParseMode.MARKDOWN)
    await asyncio.sleep(3)
    
    # 4. Expiry Examples
    expiry_demo = """**3️⃣ EXPIRY COUNTDOWN EXAMPLES:**

🟩🟩🟩🟩🟩 HOT (>8 min)
🟩🟩🟩🟩⬜ ACTIVE (6-8 min)
🟨🟨🟨⬜⬜ FADING (4-6 min)
🟧🟧⬜⬜⬜ CLOSING (2-4 min)
🟥⬜⬜⬜⬜ CRITICAL (<2 min)
⬛⬛⬛⬛⬛ EXPIRED (0 min)"""
    
    await bot.send_message(chat_id=CHAT_ID, text=expiry_demo, parse_mode=ParseMode.MARKDOWN)
    await asyncio.sleep(2)
    
    # 5. Expired Signal
    expired_signal = """⚫ **[EXPIRED]** OPERATION COMPLETE ⚫
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
~~**OP: DAWN RAID**~~
~~**TARGET:** EURUSD | BUY~~
~~**ENTRY:** 1.08234~~

**FINAL REPORT:**
• 89 operators engaged
• Operation window closed
• Check battle report for results

⬛⬛⬛⬛⬛ EXPIRED"""
    
    await bot.send_message(chat_id=CHAT_ID, text="**4️⃣ EXPIRED SIGNAL EXAMPLE:**", parse_mode=ParseMode.MARKDOWN)
    await bot.send_message(chat_id=CHAT_ID, text=expired_signal, parse_mode=ParseMode.MARKDOWN)
    await asyncio.sleep(3)
    
    # 6. Active Positions
    active_positions = """⚔️ **BATTLEFIELD STATUS** ⚔️
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 **ACTIVE POSITIONS: 4**

🟢 **EURUSD** ↗️ +15p • 45m
🔴 **GBPUSD** ↘️ -8p • 23m
🟢 **USDJPY** ↗️ +22p • 1h7m
⚪ **AUDUSD** ↘️ +0p • 5m

━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 **TOTAL P/L: +29 PIPS**

[📊 **DETAILS**] [✂️ **MANAGE**]"""
    
    await bot.send_message(chat_id=CHAT_ID, text="**5️⃣ ACTIVE POSITIONS DISPLAY:**", parse_mode=ParseMode.MARKDOWN)
    await bot.send_message(chat_id=CHAT_ID, text=active_positions, parse_mode=ParseMode.MARKDOWN)
    await asyncio.sleep(3)
    
    # 7. Daily Battle Report
    battle_report = """🎖️ **DAILY BATTLE REPORT** 🎖️
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **COMBAT STATISTICS**
• **Shots Fired:** 5/6 (1 remaining)
• **Direct Hits:** 4 (80% accuracy)
• **Total Pips:** +73
• **XP Earned:** +285

🎯 **PERFORMANCE RATING**
🔥 ELITE PERFORMANCE

🏅 **RANK PROGRESSION**
• **Current:** 🥉 RECRUIT
• **Progress:** ████████░░ 82%
• **Next:** 🥈 WARRIOR (need 150 XP)

📈 **DAILY OBJECTIVES**
• ✅ Maintain 70%+ accuracy
• ✅ Execute 4+ trades
• ✅ Capture 50+ pips

[📊 **FULL STATS**] [🏆 **LEADERBOARD**]"""
    
    await bot.send_message(chat_id=CHAT_ID, text="**6️⃣ DAILY BATTLE REPORT:**", parse_mode=ParseMode.MARKDOWN)
    await bot.send_message(chat_id=CHAT_ID, text=battle_report, parse_mode=ParseMode.MARKDOWN)
    await asyncio.sleep(3)
    
    # 8. Summary
    summary = """**🎯 KEY FEATURES DEMONSTRATED:**

✅ **Clear Trade Info**: Symbol, direction, entry
✅ **Risk/Reward**: Shows both risk and target pips
✅ **Expiry Countdown**: Visual bar showing time left
✅ **Squad Status**: Active traders + average TCS
✅ **Tactical Theme**: Military callsigns & terminology
✅ **Signal Types**: Distinct arcade (🎮) vs sniper (🎯)

**📝 NOTES:**
• Signals stay in history for 10 hours
• Expired signals show grayed out
• Countdown bar changes color as time runs out
• Social proof via squad engagement numbers

Which style do you prefer? Any modifications needed?"""
    
    await bot.send_message(chat_id=CHAT_ID, text=summary, parse_mode=ParseMode.MARKDOWN)
    
    print("✅ All mockups sent to Telegram!")

if __name__ == "__main__":
    asyncio.run(send_mockups())