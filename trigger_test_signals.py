#!/usr/bin/env python3
# Trigger test signals to webhook

import requests
import json
import time

# Webhook endpoint
WEBHOOK_URL = "http://localhost:9001/webhook"

def send_signal_to_webhook(signal_data):
    """Send signal to BITTEN webhook"""
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=signal_data,
            headers={'Content-Type': 'application/json'}
        )
        print(f"Sent: {signal_data['type']} - Status: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

def trigger_arcade_signals():
    """Send arcade signals in sequence"""
    
    # Signal 1: Dawn Raid
    signal1 = {
        "type": "arcade_signal",
        "data": {
            "strategy": "dawn_raid",
            "symbol": "EURUSD",
            "direction": "buy", 
            "entry": 1.0823,
            "stop": 1.0803,
            "target": 1.0853,
            "tcs": 72,
            "pips": 30,
            "display": """🌅 **DAWN RAID** - EURUSD
→ BUY @ 1.0823
→ +30 pips | TCS: 72%
[🔫 FIRE]"""
        }
    }
    send_signal_to_webhook(signal1)
    time.sleep(3)
    
    # Signal 2: Wall Defender (detailed style)
    signal2 = {
        "type": "arcade_signal",
        "data": {
            "strategy": "wall_defender",
            "symbol": "GBPUSD",
            "direction": "sell",
            "entry": 1.2750,
            "stop": 1.2770,
            "target": 1.2720,
            "tcs": 78,
            "pips": 30,
            "display": """┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 🏰 WALL DEFENDER
┃ ───────────────────────────
┃ 📍 GBPUSD - SELL
┃ 💰 Entry: 1.2750
┃ 🎯 Target: 1.2720 (+30p)
┃ 🛡️ Stop: 1.2770
┃ ⏱️ Duration: ~20min
┃ 
┃ TCS: ███████░░░
┃      78% Confidence
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
        [🔫 FIRE NOW]"""
        }
    }
    send_signal_to_webhook(signal2)
    time.sleep(3)
    
    # Signal 3: Rocket Ride (compact)
    signal3 = {
        "type": "arcade_signal",
        "data": {
            "strategy": "rocket_ride",
            "symbol": "USDJPY",
            "direction": "buy",
            "entry": 110.50,
            "stop": 110.30,
            "target": 110.85,
            "tcs": 89,
            "pips": 35,
            "display": """╔═══════════════════════════╗
║ 🚀 ROCKET RIDE            ║
║ USDJPY │ BUY │ TCS: 89%  ║
║ Entry: 110.50             ║
║ Target: +35 pips          ║
║ █████████░                ║
╚═══════════════════════════╝
        [🔫 FIRE]"""
        }
    }
    send_signal_to_webhook(signal3)

def trigger_sniper_signal():
    """Send sniper signal"""
    
    signal = {
        "type": "sniper_signal",
        "data": {
            "tcs": 91,
            "pips": 45,
            "display": """╔═══════════════════════════════╗
║  🎯 SNIPER SHOT DETECTED! 🎯  ║
║ ━━━━━━━━━━━━━━━━━━━━━━━━━━━ ║
║     [CLASSIFIED SETUP]        ║
║                               ║
║  Confidence: 91%              ║
║  Expected: 45 pips           ║
║  Duration: <120 min        ║
║                               ║
║  ⚡ FANG+ EXCLUSIVE ⚡        ║
╚═══════════════════════════════╝
         [🔫 EXECUTE]"""
        }
    }
    send_signal_to_webhook(signal)

def trigger_midnight_hammer():
    """Send Midnight Hammer event"""
    
    signal = {
        "type": "special_event",
        "data": {
            "event": "midnight_hammer",
            "display": """╔═══════════════════════════════════╗
║ 🔨🔨🔨 MIDNIGHT HAMMER EVENT 🔨🔨🔨║
║ ═════════════════════════════════ ║
║      💥 LEGENDARY SETUP! 💥       ║
║                                   ║
║   Community Power: ████████ 87%   ║
║   TCS Score: 🔥🔥🔥🔥🔥 96%      ║
║   Risk: 5% = 50-100 pips         ║
║   Unity Bonus: +15% XP            ║
║                                   ║
║   ⚡ 147 WARRIORS READY ⚡        ║
║   ⏰ WINDOW CLOSES IN 4:32 ⏰     ║
╚═══════════════════════════════════╝
      [🔨 JOIN THE HAMMER!]"""
        }
    }
    send_signal_to_webhook(signal)

# Main execution
print("TRIGGERING TEST SIGNALS...")
print("=" * 40)

print("\n1. Sending arcade signals...")
trigger_arcade_signals()

time.sleep(5)

print("\n2. Sending sniper signal...")
trigger_sniper_signal()

time.sleep(3)

print("\n3. Sending Midnight Hammer...")
trigger_midnight_hammer()

print("\nAll test signals sent!")
print("Check your Telegram group for the displays.")