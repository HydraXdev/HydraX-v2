#!/usr/bin/env python3
# Simulate signals appearing in sequence

import sys
import time
import random
sys.path.append('/root/HydraX-v2/src')

from bitten_core.signal_display import SignalDisplay

def simulate_trading_session():
    display = SignalDisplay()
    
    print("🟢 BITTEN SYSTEM ONLINE")
    print("━" * 40)
    time.sleep(2)
    
    # 1. First arcade signal appears
    print("\n💫 SIGNAL DETECTED...")
    time.sleep(1)
    
    arcade_signal = {
        'visual_emoji': '🌅',
        'display_type': 'DAWN RAID',
        'symbol': 'EURUSD',
        'direction': 'buy',
        'entry_price': 1.0823,
        'stop_loss': 1.0803,
        'take_profit': 1.0853,
        'tcs_score': 72,
        'expected_pips': 30,
        'expected_duration': 25
    }
    
    print(display.create_arcade_signal_card(arcade_signal))
    time.sleep(4)
    
    # 2. Another arcade signal
    print("\n💫 SIGNAL DETECTED...")
    time.sleep(1)
    
    arcade_signal2 = {
        'visual_emoji': '🏰',
        'display_type': 'WALL DEFENDER',
        'symbol': 'GBPUSD',
        'direction': 'sell',
        'entry_price': 1.2750,
        'stop_loss': 1.2770,
        'take_profit': 1.2720,
        'tcs_score': 78,
        'expected_pips': 30,
        'expected_duration': 20
    }
    
    # Show minimal style this time
    print(f"""
🏰 **WALL DEFENDER** - GBPUSD
→ SELL @ 1.2750
→ +30 pips | TCS: 78%
[🔫 FIRE]""")
    time.sleep(4)
    
    # 3. High confidence arcade
    print("\n⚡ HIGH CONFIDENCE SIGNAL...")
    time.sleep(1)
    
    arcade_signal3 = {
        'visual_emoji': '🚀',
        'display_type': 'ROCKET RIDE',
        'symbol': 'USDJPY',
        'direction': 'buy',
        'entry_price': 110.50,
        'stop_loss': 110.30,
        'take_profit': 110.85,
        'tcs_score': 89,
        'expected_pips': 35,
        'expected_duration': 30
    }
    
    # Compact style
    print(f"""
╔═══════════════════════════╗
║ 🚀 ROCKET RIDE            ║
║ USDJPY │ BUY │ TCS: 89%  ║
║ Entry: 110.50             ║
║ Target: +35 pips          ║
║ █████████░                ║
╚═══════════════════════════╝
        [🔫 FIRE]""")
    time.sleep(5)
    
    # 4. SNIPER SIGNAL!
    print("\n🎯 ELITE SIGNAL INCOMING...")
    time.sleep(2)
    
    sniper_signal = {
        'tcs_score': 91,
        'expected_pips': 45,
        'expected_duration': 120
    }
    
    print(display.create_sniper_signal_card(sniper_signal))
    time.sleep(5)
    
    # 5. Show current positions
    print("\n📊 POSITION UPDATE...")
    time.sleep(1)
    
    positions = [
        {'symbol': 'EURUSD', 'direction': 'buy', 'pnl': 15},
        {'symbol': 'USDJPY', 'direction': 'buy', 'pnl': 22}
    ]
    
    print(display.create_position_summary_card(positions))
    time.sleep(4)
    
    # 6. Another arcade
    print("\n💫 SIGNAL DETECTED...")
    time.sleep(1)
    
    print(f"""
🎯 **RUBBER BAND** - GBPJPY
→ SELL @ 155.20
→ +25 pips | TCS: 73%
[🔫 FIRE]""")
    time.sleep(3)
    
    # 7. MIDNIGHT HAMMER EVENT!
    print("\n🚨🚨🚨 SPECIAL EVENT ALERT 🚨🚨🚨")
    time.sleep(2)
    
    print(display.create_midnight_hammer_card())
    time.sleep(6)
    
    # 8. Daily summary
    print("\n📈 END OF SESSION REPORT...")
    time.sleep(1)
    
    stats = {
        'trades': 5,
        'wins': 4,
        'win_rate': 80,
        'pips': 67,
        'xp': 180
    }
    
    print(display.create_daily_summary_card(stats))

def quick_sequence():
    """Show all styles quickly"""
    display = SignalDisplay()
    
    styles = [
        ("DETAILED STYLE", """
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 🚀 ROCKET RIDE
┃ ───────────────────────────
┃ 📍 GBPUSD - BUY
┃ 💰 Entry: 1.27650
┃ 🎯 Target: 1.27950 (+30p)
┃ 🛡️ Stop: 1.27450
┃ ⏱️ Duration: ~45min
┃ 
┃ TCS: ████████░░
┃      87% Confidence
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
        [🔫 FIRE NOW]"""),
        
        ("COMPACT STYLE", """
╔═══════════════════════════╗
║ 🚀 ROCKET RIDE            ║
║ GBPUSD │ BUY │ TCS: 87%  ║
║ Entry: 1.27650            ║
║ Target: +30 pips          ║
║ ████████░░                ║
╚═══════════════════════════╝
        [🔫 FIRE]"""),
        
        ("MINIMAL STYLE", """
🚀 **ROCKET RIDE** - GBPUSD
→ BUY @ 1.27650
→ +30 pips | TCS: 87%
[🔫 FIRE]"""),
        
        ("GAMING STYLE", """
╭─────────────────────────────╮
│ 🎮 NEW SIGNAL DETECTED!     │
│                             │
│ 🚀 ROCKET RIDE              │
│ ═══════════════════════════ │
│ Pair: GBPUSD     Dir: BUY   │
│ Power: ⚡⚡⚡⚡·              │
│ Reward: +30 pips            │
│                             │
│     Press [🔫] to FIRE      │
╰─────────────────────────────╯""")
    ]
    
    for name, style in styles:
        print(f"\n{'='*40}")
        print(f"{name}:")
        print(style)
        input("\nPress Enter for next style...")

# Menu
print("SIGNAL SIMULATION")
print("================")
print("1. Simulate trading session (signals appear over time)")
print("2. Show all styles quickly")
print("3. Exit")

choice = input("\nChoice: ")

if choice == "1":
    simulate_trading_session()
elif choice == "2":
    quick_sequence()
else:
    print("Exiting...")