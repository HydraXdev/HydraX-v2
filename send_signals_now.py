#!/usr/bin/env python3
"""Send BITTEN signal mockups to Telegram NOW!"""

import requests
import time

# Your credentials
BOT_TOKEN = "7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ"
CHAT_ID = "-1002581996861"

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
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

# SIGNAL MOCKUPS
print("🚀 SENDING BITTEN SIGNAL MOCKUPS...")
print("=" * 50)

# 1. ARCADE - Dawn Raid (Minimal)
print("\n[1/7] Sending Dawn Raid signal...")
send_to_telegram("""🌅 *DAWN RAID* - EURUSD
→ BUY @ 1.0823
→ +25 pips | TCS: 72%
[🔫 FIRE]""")
time.sleep(3)

# 2. ARCADE - Wall Defender (Detailed)
print("[2/7] Sending Wall Defender signal...")
send_to_telegram("""🏰 *WALL DEFENDER*
━━━━━━━━━━━━━━━━━
📍 GBPUSD - SELL
💰 Entry: 1.2750
🎯 Target: 1.2720 (+30p)
🛡️ Stop: 1.2770
⏱️ Duration: ~20min

TCS: ▓▓▓▓▓▓▓░ 78%

[🔫 FIRE NOW]""")
time.sleep(3)

# 3. ARCADE - Rocket Ride (Compact)
print("[3/7] Sending Rocket Ride signal...")
send_to_telegram("""🚀 *ROCKET RIDE*
USDJPY │ BUY │ TCS: 89%
Entry: 110.50
Target: +35 pips
▓▓▓▓▓▓▓▓░

[🔫 FIRE]""")
time.sleep(3)

# 4. SNIPER Signal
print("[4/7] Sending Sniper signal...")
send_to_telegram("""🎯 *SNIPER SHOT DETECTED!* 🎯
━━━━━━━━━━━━━━━━━━━━
_[CLASSIFIED SETUP]_

Confidence: 91%
Expected: 45 pips
Duration: <2 hours

⚡ *FANG+ EXCLUSIVE* ⚡

[🔫 EXECUTE]""")
time.sleep(3)

# 5. Position Update
print("[5/7] Sending position summary...")
send_to_telegram("""📊 *ACTIVE POSITIONS (3)*
━━━━━━━━━━━━━━━━━━━━
🟢 GBPUSD BUY │ +23p
🔴 EURUSD SELL │ -8p
🟢 USDJPY BUY │ +15p
─────────────────────
Total P/L: *+30 pips*""")
time.sleep(3)

# 6. Midnight Hammer Event
print("[6/7] Sending Midnight Hammer event...")
send_to_telegram("""🔨🔨🔨 *MIDNIGHT HAMMER EVENT* 🔨🔨🔨
═══════════════════════════════

💥 *LEGENDARY SETUP!* 💥

Community Power: ▓▓▓▓▓▓▓ 87%
TCS Score: 🔥🔥🔥🔥🔥 96%
Risk: 5% = 50-100 pips
Unity Bonus: +15% XP

⚡ 147 WARRIORS READY ⚡
⏰ WINDOW CLOSES IN 4:32 ⏰

[🔨 JOIN THE HAMMER!]""")
time.sleep(3)

# 7. Daily Summary
print("[7/7] Sending daily summary...")
send_to_telegram("""📈 *DAILY BATTLE REPORT*
═══════════════════════
Shots Fired: 4/6
Direct Hits: 3 (75%)
Total Pips: *+47*
XP Earned: *+120*

Rank Progress: ▓▓▓▓▓▓░░ 82%
Next Badge: 🥈 WARRIOR""")

print("\n" + "=" * 50)
print("✅ ALL MOCKUPS SENT!")
print("Check your Telegram group now!")
print("=" * 50)