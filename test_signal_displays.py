#!/usr/bin/env python3
# Test signal display cards

import sys
sys.path.append('/root/HydraX-v2/src')

from bitten_core.signal_display import SignalDisplay

def test_all_displays():
    display = SignalDisplay()
    
    # Test arcade signal
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
    
    print("=== ARCADE SIGNAL ===")
    print(display.create_arcade_signal_card(arcade_signal))
    
    # Test sniper signal
    sniper_signal = {
        'tcs_score': 91,
        'expected_pips': 45,
        'expected_duration': 120
    }
    
    print("\n=== SNIPER SIGNAL ===")
    print(display.create_sniper_signal_card(sniper_signal))
    
    # Test midnight hammer
    print("\n=== MIDNIGHT HAMMER ===")
    print(display.create_midnight_hammer_card())
    
    # Test chaingun
    print("\n=== CHAINGUN SEQUENCE ===")
    print(display.create_chaingun_sequence_card(2, [True]))
    
    # Test positions
    positions = [
        {'symbol': 'GBPUSD', 'direction': 'buy', 'pnl': 23},
        {'symbol': 'EURUSD', 'direction': 'sell', 'pnl': -8},
        {'symbol': 'USDJPY', 'direction': 'buy', 'pnl': 15}
    ]
    
    print("\n=== POSITION SUMMARY ===")
    print(display.create_position_summary_card(positions))
    
    # Test daily summary
    stats = {
        'trades': 4,
        'wins': 3,
        'win_rate': 75,
        'pips': 47,
        'xp': 120
    }
    
    print("\n=== DAILY SUMMARY ===")
    print(display.create_daily_summary_card(stats))

if __name__ == "__main__":
    test_all_displays()