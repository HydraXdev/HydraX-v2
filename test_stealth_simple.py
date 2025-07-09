#!/usr/bin/env python3
# test_stealth_simple.py
# Simple test of stealth protocol without complex imports

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Direct import of stealth protocol
from src.bitten_core.stealth_protocol import (
    StealthProtocol, StealthLevel, StealthConfig
)

def test_basic_stealth():
    """Test basic stealth functionality"""
    print("🥷 TESTING STEALTH PROTOCOL")
    print("=" * 50)
    
    # Create stealth protocol instance
    stealth = StealthProtocol()
    print("✅ Stealth protocol initialized")
    
    # Test trade parameters
    trade_params = {
        'symbol': 'EURUSD',
        'volume': 0.1,
        'tp': 1.1050,
        'sl': 1.0950,
        'entry_price': 1.1000,
        'trade_id': 'TEST_001'
    }
    
    # Test each stealth function
    print("\n1. Testing Entry Delay:")
    delay = stealth.entry_delay(trade_params)
    print(f"   Generated delay: {delay:.2f} seconds")
    
    print("\n2. Testing Lot Size Jitter:")
    original_lot = trade_params['volume']
    jittered_lot = stealth.lot_size_jitter(original_lot, trade_params['symbol'])
    print(f"   Original: {original_lot} -> Jittered: {jittered_lot}")
    
    print("\n3. Testing TP/SL Offset:")
    new_tp, new_sl = stealth.tp_sl_offset(
        trade_params['tp'], 
        trade_params['sl'], 
        trade_params['symbol']
    )
    print(f"   TP: {trade_params['tp']} -> {new_tp}")
    print(f"   SL: {trade_params['sl']} -> {new_sl}")
    
    print("\n4. Testing Ghost Skip:")
    skip = stealth.ghost_skip(trade_params)
    print(f"   Skip trade: {skip}")
    
    print("\n5. Testing Volume Cap:")
    allowed = stealth.vol_cap(trade_params['symbol'], trade_params['trade_id'])
    print(f"   Trade allowed: {allowed}")
    
    print("\n6. Testing Full Stealth Application:")
    stealth_params = stealth.apply_full_stealth(trade_params.copy())
    if stealth_params.get('skip_trade'):
        print(f"   Trade skipped: {stealth_params.get('skip_reason')}")
    else:
        print(f"   Entry delay: {stealth_params.get('entry_delay', 0):.2f}s")
        print(f"   Volume adjusted: {stealth_params.get('volume')}")
    
    # Test different stealth levels
    print("\n\n🎚️ TESTING STEALTH LEVELS")
    print("-" * 50)
    
    for level in [StealthLevel.LOW, StealthLevel.MEDIUM, StealthLevel.HIGH]:
        stealth.set_level(level)
        print(f"\n{level.value.upper()} Level:")
        
        # Get 5 delays and average
        delays = []
        for _ in range(5):
            d = stealth.entry_delay(trade_params)
            delays.append(d)
        avg_delay = sum(delays) / len(delays)
        print(f"  Average delay: {avg_delay:.2f}s")
    
    # Check logs
    print("\n\n📊 STEALTH STATISTICS")
    print("-" * 50)
    stats = stealth.get_stealth_stats()
    print(f"Enabled: {stats['enabled']}")
    print(f"Current Level: {stats['level']}")
    print(f"Actions Logged: {stats['actions_logged']}")
    
    # Check if log file exists
    log_path = "/root/HydraX-v2/logs/stealth_log.txt"
    if os.path.exists(log_path):
        print(f"\n✅ Log file created at: {log_path}")
        with open(log_path, 'r') as f:
            lines = f.readlines()
            print(f"   Total log entries: {len(lines)}")
    else:
        print(f"\n⚠️  Log file not found at: {log_path}")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    test_basic_stealth()