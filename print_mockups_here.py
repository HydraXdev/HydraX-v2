#!/usr/bin/env python3
"""
Print all signal mockups to console
Since you can't scroll, I'll show them one at a time
"""

import time

mockups = {
    "1_arcade_minimal": """🌅 *DAWN RAID* - EURUSD
→ BUY @ 1.0823
→ +25 pips | TCS: 72%
[🔫 FIRE]""",

    "2_arcade_detailed": """🏰 *WALL DEFENDER*
━━━━━━━━━━━━━━━━━
📍 GBPUSD - SELL
💰 Entry: 1.2750
🎯 Target: 1.2720 (+30p)
🛡️ Stop: 1.2770
⏱️ Duration: ~20min

TCS: ▓▓▓▓▓▓▓░ 78%

[🔫 FIRE NOW]""",

    "3_arcade_compact": """🚀 *ROCKET RIDE*
USDJPY │ BUY │ TCS: 89%
Entry: 110.50
Target: +35 pips
▓▓▓▓▓▓▓▓░

[🔫 FIRE]""",

    "4_sniper": """🎯 *SNIPER SHOT DETECTED!* 🎯
━━━━━━━━━━━━━━━━━━━━
_[CLASSIFIED SETUP]_

Confidence: 91%
Expected: 45 pips
Duration: <2 hours

⚡ *FANG+ EXCLUSIVE* ⚡

[🔫 EXECUTE]""",

    "5_positions": """📊 *ACTIVE POSITIONS (3)*
━━━━━━━━━━━━━━━━━━━━
🟢 GBPUSD BUY │ +23p
🔴 EURUSD SELL │ -8p
🟢 USDJPY BUY │ +15p
─────────────────────
Total P/L: *+30 pips*""",

    "6_hammer": """🔨🔨🔨 *MIDNIGHT HAMMER EVENT* 🔨🔨🔨
═══════════════════════════════

💥 *LEGENDARY SETUP!* 💥

Community Power: ▓▓▓▓▓▓▓ 87%
TCS Score: 🔥🔥🔥🔥🔥 96%
Risk: 5% = 50-100 pips
Unity Bonus: +15% XP

⚡ 147 WARRIORS READY ⚡
⏰ WINDOW CLOSES IN 4:32 ⏰

[🔨 JOIN THE HAMMER!]""",

    "7_daily": """📈 *DAILY BATTLE REPORT*
═══════════════════════
Shots Fired: 4/6
Direct Hits: 3 (75%)
Total Pips: *+47*
XP Earned: *+120*

Rank Progress: ▓▓▓▓▓▓░░ 82%
Next Badge: 🥈 WARRIOR"""
}

print("BITTEN SIGNAL MOCKUPS")
print("=" * 40)
print(f"Total mockups: {len(mockups)}")
print("\nPress Enter to see each mockup...")

for name, mockup in mockups.items():
    input(f"\n[{name}] Press Enter...")
    print("\n" + "─" * 40)
    print(mockup)
    print("─" * 40)

print("\n✅ All mockups displayed!")
print("\nTo send these to Telegram:")
print("1. Edit telegram_signal_sender.py")
print("2. Add your BOT_TOKEN and CHAT_ID")
print("3. Run: python telegram_signal_sender.py")