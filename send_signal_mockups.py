#!/usr/bin/env python3
"""
Send tactical signal mockups to Telegram for review
"""

import asyncio
import sys
import os
from datetime import datetime
import random

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.bitten_core.signal_display import SignalDisplay
from src.bitten_core.telegram_signal_sender import TelegramSignalSender
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def send_mockups():
    """Generate and send signal mockups to Telegram"""
    
    # Initialize display and sender
    display = SignalDisplay()
    sender = TelegramSignalSender()
    
    print("🚀 Sending tactical signal mockups to Telegram...")
    
    # Sample arcade signal data
    arcade_signal = {
        'visual_emoji': '🎮',
        'display_type': 'DAWN RAID',
        'symbol': 'EURUSD',
        'direction': 'buy',
        'entry_price': 1.08234,
        'expected_pips': 12,
        'risk_pips': 3,
        'tcs_score': 78,
        'expected_duration': 15,
        'time_remaining': 540,  # 9 minutes
        'active_traders': 23,
        'squad_avg_tcs': 75,
        'type': 'arcade',
        'callsign': 'BRAVO-7'
    }
    
    # Sample sniper signal data
    sniper_signal = {
        'visual_emoji': '🎯',
        'display_type': 'PRECISION STRIKE',
        'symbol': 'GBPUSD',
        'direction': 'sell',
        'entry_price': 1.26789,
        'expected_pips': 25,
        'risk_pips': 5,
        'tcs_score': 92,
        'expected_duration': 30,
        'time_remaining': 480,  # 8 minutes
        'active_traders': 12,
        'squad_avg_tcs': 88,
        'type': 'sniper',
        'callsign': 'GHOST-1'
    }
    
    # Send intro message
    intro = """
🎖️ **TACTICAL SIGNAL DISPLAY MOCKUPS** 🎖️
═══════════════════════════════════════

Testing new military-themed signal displays with:
• SITREP-style briefings
• Expiry countdown bars
• Squad engagement tracking
• Risk/Reward ratios
• Tactical callsigns

Please review the following mockups:
"""
    await sender.send_message_to_telegram(intro)
    await asyncio.sleep(2)
    
    # 1. Arcade Signal - SITREP Style
    arcade_card = display.create_arcade_signal_card(arcade_signal)
    await sender.send_message_to_telegram(arcade_card)
    await asyncio.sleep(3)
    
    # 2. Sniper Signal - Elite Briefing
    sniper_card = display.create_sniper_signal_card(sniper_signal)
    await sender.send_message_to_telegram(sniper_card)
    await asyncio.sleep(3)
    
    # 3. Show all tactical variants for arcade
    variants = display.create_tactical_signal_variants(arcade_signal)
    
    await sender.send_message_to_telegram("**📋 VARIANT 1: COMBAT OPS BRIEF**")
    await sender.send_message_to_telegram(variants['combat_ops'])
    await asyncio.sleep(3)
    
    await sender.send_message_to_telegram("**📋 VARIANT 2: STRIKE TEAM ALERT**")
    await sender.send_message_to_telegram(variants['strike_team'])
    await asyncio.sleep(3)
    
    await sender.send_message_to_telegram("**📋 VARIANT 3: TACTICAL HUD**")
    await sender.send_message_to_telegram(variants['tactical_hud'])
    await asyncio.sleep(3)
    
    # 4. Show different expiry states
    expiry_demo = """
**⏱️ EXPIRY COUNTDOWN EXAMPLES:**

🟩🟩🟩🟩🟩 HOT (>8 min)
🟩🟩🟩🟩⬜ ACTIVE (6-8 min)
🟨🟨🟨⬜⬜ FADING (4-6 min)
🟧🟧⬜⬜⬜ CLOSING (2-4 min)
🟥⬜⬜⬜⬜ CRITICAL (<2 min)
⬛⬛⬛⬛⬛ EXPIRED (0 min)
"""
    await sender.send_message_to_telegram(expiry_demo)
    await asyncio.sleep(2)
    
    # 5. Show expired signal (grayed out)
    expired_signal = arcade_signal.copy()
    expired_signal['time_remaining'] = 0
    expired_signal['active_traders'] = 89
    expired_card = f"""
⚫ **[EXPIRED]** OPERATION COMPLETE ⚫
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
~~**OP: {expired_signal['display_type']}**~~
~~**TARGET:** {expired_signal['symbol']} | {expired_signal['direction'].upper()}~~
~~**ENTRY:** {expired_signal['entry_price']:.5f}~~

**FINAL REPORT:**
• 89 operators engaged
• Operation window closed
• Check battle report for results

⬛⬛⬛⬛⬛ EXPIRED
"""
    await sender.send_message_to_telegram(expired_card)
    await asyncio.sleep(2)
    
    # 6. Summary
    summary = """
**🎯 KEY FEATURES DEMONSTRATED:**

✅ **Clear Trade Info**: Symbol, direction, entry
✅ **Risk/Reward**: Shows both risk and target pips
✅ **Expiry Countdown**: Visual bar showing time left
✅ **Squad Status**: Active traders + average TCS
✅ **Tactical Theme**: Military callsigns & terminology
✅ **Signal Types**: Distinct arcade (🎮) vs sniper (🎯)

**📝 NOTES:**
• Signals stay in history for 10 hours (scrollback proof)
• Expired signals show grayed out
• Countdown bar changes color as time runs out
• Social proof via squad engagement numbers

Which variant do you prefer? Any modifications needed?
"""
    await sender.send_message_to_telegram(summary)
    
    print("✅ All mockups sent successfully!")

if __name__ == "__main__":
    asyncio.run(send_mockups())