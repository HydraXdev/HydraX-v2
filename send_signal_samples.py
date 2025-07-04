#!/usr/bin/env python3
# Send signal display samples to Telegram

import sys
import time
sys.path.append('/root/HydraX-v2/src')

from bitten_core.signal_display import SignalDisplay

def show_arcade_signal():
    display = SignalDisplay()
    
    arcade_signal = {
        'visual_emoji': '🚀',
        'display_type': 'ROCKET RIDE',
        'symbol': 'GBPUSD',
        'direction': 'buy',
        'entry_price': 1.27650,
        'stop_loss': 1.27450,
        'take_profit': 1.27950,
        'tcs_score': 87,
        'expected_pips': 30,
        'expected_duration': 45
    }
    
    card = display.create_arcade_signal_card(arcade_signal)
    print("=== ARCADE SIGNAL CARD ===")
    print(card)
    print("\n" + "="*40 + "\n")
    
    # Wait for user to see it
    input("Press Enter to see next card...")

def show_sniper_signal():
    display = SignalDisplay()
    
    sniper_signal = {
        'tcs_score': 91,
        'expected_pips': 45,
        'expected_duration': 120
    }
    
    card = display.create_sniper_signal_card(sniper_signal)
    print("=== SNIPER SIGNAL CARD ===")
    print(card)
    print("\n" + "="*40 + "\n")
    
    input("Press Enter to see next card...")

def show_midnight_hammer():
    display = SignalDisplay()
    
    card = display.create_midnight_hammer_card()
    print("=== MIDNIGHT HAMMER EVENT ===")
    print(card)
    print("\n" + "="*40 + "\n")
    
    input("Press Enter to see next card...")

def show_chaingun():
    display = SignalDisplay()
    
    card = display.create_chaingun_sequence_card(2, [True])
    print("=== CHAINGUN SEQUENCE ===")
    print(card)
    print("\n" + "="*40 + "\n")
    
    input("Press Enter to see next card...")

def show_positions():
    display = SignalDisplay()
    
    positions = [
        {'symbol': 'GBPUSD', 'direction': 'buy', 'pnl': 23},
        {'symbol': 'EURUSD', 'direction': 'sell', 'pnl': -8},
        {'symbol': 'USDJPY', 'direction': 'buy', 'pnl': 15}
    ]
    
    card = display.create_position_summary_card(positions)
    print("=== POSITION SUMMARY ===")
    print(card)
    print("\n" + "="*40 + "\n")
    
    input("Press Enter to see next card...")

def show_daily_summary():
    display = SignalDisplay()
    
    stats = {
        'trades': 4,
        'wins': 3,
        'win_rate': 75,
        'pips': 47,
        'xp': 120
    }
    
    card = display.create_daily_summary_card(stats)
    print("=== DAILY SUMMARY ===")
    print(card)
    print("\n" + "="*40 + "\n")

# Menu
print("SIGNAL DISPLAY SAMPLES")
print("=====================")
print("1. Arcade Signal")
print("2. Sniper Signal") 
print("3. Midnight Hammer")
print("4. Chaingun Sequence")
print("5. Position Summary")
print("6. Daily Summary")
print("7. Show All (one by one)")
print("")

choice = input("Enter number (1-7): ")

if choice == "1":
    show_arcade_signal()
elif choice == "2":
    show_sniper_signal()
elif choice == "3":
    show_midnight_hammer()
elif choice == "4":
    show_chaingun()
elif choice == "5":
    show_positions()
elif choice == "6":
    show_daily_summary()
elif choice == "7":
    show_arcade_signal()
    show_sniper_signal()
    show_midnight_hammer()
    show_chaingun()
    show_positions()
    show_daily_summary()
    print("All samples shown!")
else:
    print("Invalid choice")