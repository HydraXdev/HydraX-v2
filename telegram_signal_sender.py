#!/usr/bin/env python3
"""
Direct Telegram Signal Sender - No webhook needed!
Just add your bot token and chat ID below.
"""

import requests
import time

# CONFIGURATION - FILL THESE IN!
# ================================
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Get from @BotFather
CHAT_ID = "YOUR_CHAT_ID_HERE"      # Your group chat ID

# To get your chat ID:
# 1. Add your bot to the group
# 2. Send any message in the group
# 3. Visit: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
# 4. Look for "chat":{"id":-123456789} - that negative number is your chat ID

def send_to_telegram(text):
    """Send formatted message to Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ Sent successfully!")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Connection error: {e}")

# SIGNAL MOCKUPS
signals = [
    # 1. ARCADE - Dawn Raid (Minimal)
    """🌅 *DAWN RAID* - EURUSD
→ BUY @ 1.0823
→ +25 pips | TCS: 72%
[🔫 FIRE]""",

    # 2. ARCADE - Wall Defender (Detailed)
    """🏰 *WALL DEFENDER*
━━━━━━━━━━━━━━━━━
📍 GBPUSD - SELL
💰 Entry: 1.2750
🎯 Target: 1.2720 (+30p)
🛡️ Stop: 1.2770
⏱️ Duration: ~20min

TCS: ▓▓▓▓▓▓▓░ 78%

[🔫 FIRE NOW]""",

    # 3. ARCADE - Rocket Ride (Compact)
    """🚀 *ROCKET RIDE*
USDJPY │ BUY │ TCS: 89%
Entry: 110.50
Target: +35 pips
▓▓▓▓▓▓▓▓░

[🔫 FIRE]""",

    # 4. SNIPER Signal
    """🎯 *SNIPER SHOT DETECTED!* 🎯
━━━━━━━━━━━━━━━━━━━━
_[CLASSIFIED SETUP]_

Confidence: 91%
Expected: 45 pips
Duration: <2 hours

⚡ *FANG+ EXCLUSIVE* ⚡

[🔫 EXECUTE]""",

    # 5. Position Update
    """📊 *ACTIVE POSITIONS (3)*
━━━━━━━━━━━━━━━━━━━━
🟢 GBPUSD BUY │ +23p
🔴 EURUSD SELL │ -8p
🟢 USDJPY BUY │ +15p
─────────────────────
Total P/L: *+30 pips*""",

    # 6. Midnight Hammer Event
    """🔨🔨🔨 *MIDNIGHT HAMMER EVENT* 🔨🔨🔨
═══════════════════════════════

💥 *LEGENDARY SETUP!* 💥

Community Power: ▓▓▓▓▓▓▓ 87%
TCS Score: 🔥🔥🔥🔥🔥 96%
Risk: 5% = 50-100 pips
Unity Bonus: +15% XP

⚡ 147 WARRIORS READY ⚡
⏰ WINDOW CLOSES IN 4:32 ⏰

[🔨 JOIN THE HAMMER!]""",

    # 7. Daily Summary
    """📈 *DAILY BATTLE REPORT*
═══════════════════════
Shots Fired: 4/6
Direct Hits: 3 (75%)
Total Pips: *+47*
XP Earned: *+120*

Rank Progress: ▓▓▓▓▓▓░░ 82%
Next Badge: 🥈 WARRIOR"""
]

# MAIN EXECUTION
if __name__ == "__main__":
    print("=" * 50)
    print("BITTEN SIGNAL MOCKUP SENDER")
    print("=" * 50)
    
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or CHAT_ID == "YOUR_CHAT_ID_HERE":
        print("\n⚠️  CONFIGURATION REQUIRED!")
        print("\nPlease edit this file and add:")
        print("1. BOT_TOKEN - Get from @BotFather")
        print("2. CHAT_ID - Your group's chat ID")
        print("\nThen run this script again.")
    else:
        print(f"\nSending {len(signals)} mockups to Telegram...")
        print("Bot Token: " + BOT_TOKEN[:10] + "...")
        print(f"Chat ID: {CHAT_ID}")
        print("-" * 50)
        
        for i, signal in enumerate(signals, 1):
            print(f"\n[{i}/{len(signals)}] Sending signal...")
            send_to_telegram(signal)
            
            if i < len(signals):
                time.sleep(3)  # Wait between messages
        
        print("\n✅ All mockups sent!")
        print("\nCheck your Telegram group now!")