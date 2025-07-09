#!/usr/bin/env python3
# test_stealth_protocol.py
# Test and demonstrate the stealth protocol implementation

import asyncio
import json
from datetime import datetime
from src.bitten_core.stealth_protocol import (
    StealthProtocol, StealthLevel, StealthConfig, get_stealth_protocol
)
from src.bitten_core.stealth_integration import (
    StealthFireModeIntegration, StealthModeCommands
)
from src.bitten_core.fire_modes import FireMode, TierLevel

async def test_stealth_functions():
    """Test individual stealth functions"""
    print("🥷 TESTING STEALTH PROTOCOL FUNCTIONS")
    print("=" * 50)
    
    # Initialize stealth protocol
    stealth = get_stealth_protocol()
    stealth.config.enabled = True
    stealth.config.level = StealthLevel.MEDIUM
    
    # Test trade parameters
    trade_params = {
        'symbol': 'EURUSD',
        'volume': 0.1,
        'tp': 1.1050,
        'sl': 1.0950,
        'entry_price': 1.1000,
        'trade_id': 'TEST_001'
    }
    
    print("\n1. Testing Entry Delay:")
    delay = stealth.entry_delay(trade_params)
    print(f"   Generated delay: {delay:.2f} seconds")
    
    print("\n2. Testing Lot Size Jitter:")
    original_lot = trade_params['volume']
    jittered_lot = stealth.lot_size_jitter(original_lot, trade_params['symbol'])
    print(f"   Original lot: {original_lot}")
    print(f"   Jittered lot: {jittered_lot}")
    print(f"   Variation: {((jittered_lot/original_lot - 1) * 100):.2f}%")
    
    print("\n3. Testing TP/SL Offset:")
    original_tp = trade_params['tp']
    original_sl = trade_params['sl']
    new_tp, new_sl = stealth.tp_sl_offset(original_tp, original_sl, trade_params['symbol'])
    print(f"   Original TP: {original_tp} -> {new_tp}")
    print(f"   Original SL: {original_sl} -> {new_sl}")
    
    print("\n4. Testing Ghost Skip:")
    skip_count = 0
    total_tests = 100
    for _ in range(total_tests):
        if stealth.ghost_skip(trade_params):
            skip_count += 1
    print(f"   Skipped {skip_count}/{total_tests} trades ({skip_count/total_tests*100:.1f}%)")
    
    print("\n5. Testing Volume Cap:")
    # Test adding multiple trades
    for i in range(5):
        trade_id = f"TEST_{i:03d}"
        allowed = stealth.vol_cap('EURUSD', trade_id)
        print(f"   Trade {trade_id}: {'ALLOWED' if allowed else 'DENIED'}")
    
    print("\n6. Testing Execution Shuffle:")
    trade_queue = [
        {'symbol': 'EURUSD', 'order': 1},
        {'symbol': 'GBPUSD', 'order': 2},
        {'symbol': 'USDJPY', 'order': 3},
        {'symbol': 'AUDUSD', 'order': 4}
    ]
    shuffled = stealth.execution_shuffle(trade_queue)
    print("   Original order:", [t['symbol'] for t in trade_queue])
    print("   Shuffled order:", [t['symbol'] for t in shuffled])

async def test_stealth_levels():
    """Test different stealth levels"""
    print("\n\n🎚️ TESTING STEALTH LEVELS")
    print("=" * 50)
    
    stealth = get_stealth_protocol()
    trade_params = {
        'symbol': 'GBPUSD',
        'volume': 0.2,
        'tp': 1.2600,
        'sl': 1.2500,
        'entry_price': 1.2550
    }
    
    for level in [StealthLevel.LOW, StealthLevel.MEDIUM, StealthLevel.HIGH, StealthLevel.GHOST]:
        print(f"\n{level.value.upper()} Level:")
        stealth.set_level(level)
        
        # Test entry delay
        delays = []
        for _ in range(5):
            delay = stealth.entry_delay(trade_params)
            delays.append(delay)
        avg_delay = sum(delays) / len(delays)
        print(f"  Avg entry delay: {avg_delay:.2f}s")
        
        # Test lot jitter
        jitters = []
        for _ in range(5):
            jittered = stealth.lot_size_jitter(trade_params['volume'])
            jitter_pct = abs((jittered / trade_params['volume'] - 1) * 100)
            jitters.append(jitter_pct)
        avg_jitter = sum(jitters) / len(jitters)
        print(f"  Avg lot jitter: {avg_jitter:.2f}%")

async def test_fire_mode_integration():
    """Test integration with fire modes"""
    print("\n\n🔥 TESTING FIRE MODE INTEGRATION")
    print("=" * 50)
    
    integration = StealthFireModeIntegration()
    
    # Test different tier configurations
    tiers_to_test = [
        (TierLevel.NIBBLER, FireMode.SINGLE_SHOT),
        (TierLevel.FANG, FireMode.CHAINGUN),
        (TierLevel.COMMANDER, FireMode.AUTO_FIRE),
        (TierLevel.APEX, FireMode.STEALTH)
    ]
    
    for tier, fire_mode in tiers_to_test:
        print(f"\n{tier.value.upper()} - {fire_mode.value}:")
        
        trade_params = {
            'symbol': 'USDJPY',
            'volume': 0.1,
            'tp': 150.50,
            'sl': 149.50,
            'entry_price': 150.00
        }
        
        result = await integration.execute_stealth_trade(
            user_id=12345,
            tier=tier,
            fire_mode=fire_mode,
            trade_params=trade_params
        )
        
        if result.get('error'):
            print(f"  Error: {result['error']}")
        elif result.get('skipped'):
            print(f"  Trade skipped: {result['reason']}")
        else:
            print(f"  Trade executed: {result.get('trade_id', 'N/A')}")
            print(f"  Stealth applied: {result.get('stealth_applied', False)}")

async def test_stealth_commands():
    """Test Telegram command handlers"""
    print("\n\n💬 TESTING STEALTH COMMANDS")
    print("=" * 50)
    
    commands = StealthModeCommands()
    
    # Test status command for different tiers
    print("\n1. Status Command:")
    for tier in [TierLevel.NIBBLER, TierLevel.COMMANDER, TierLevel.APEX]:
        print(f"\n{tier.value.upper()}:")
        response = await commands.handle_stealth_status(12345, tier)
        print(response)
    
    # Test level command
    print("\n2. Level Command (APEX):")
    response = await commands.handle_stealth_level(12345, TierLevel.APEX, "ghost")
    print(response)
    
    # Test logs command
    print("\n3. Logs Command (APEX):")
    response = await commands.handle_stealth_logs(12345, TierLevel.APEX)
    print(response)

async def test_stealth_statistics():
    """Test stealth statistics and reporting"""
    print("\n\n📊 TESTING STEALTH STATISTICS")
    print("=" * 50)
    
    stealth = get_stealth_protocol()
    
    # Generate some activity
    for i in range(10):
        trade_params = {
            'symbol': f'PAIR{i}',
            'volume': 0.1 * (i + 1),
            'tp': 1.1000 + (i * 0.001),
            'sl': 1.0900,
            'trade_id': f'STAT_{i:03d}'
        }
        stealth.apply_full_stealth(trade_params)
    
    # Get statistics
    stats = stealth.get_stealth_stats()
    print("\nStealth Protocol Statistics:")
    print(f"  Enabled: {stats['enabled']}")
    print(f"  Current Level: {stats['level']}")
    print(f"  Total Active Trades: {stats['total_active']}")
    print(f"  Actions Logged: {stats['actions_logged']}")
    print(f"\nRecent Actions:")
    for action in stats['recent_actions'][-5:]:
        print(f"  - {action['type']} at {action['timestamp']} (Level: {action['level']})")

async def main():
    """Run all tests"""
    print("🚀 BITTEN STEALTH PROTOCOL TEST SUITE")
    print("=" * 50)
    print(f"Started at: {datetime.now()}")
    
    try:
        await test_stealth_functions()
        await test_stealth_levels()
        await test_fire_mode_integration()
        await test_stealth_commands()
        await test_stealth_statistics()
        
        print("\n\n✅ ALL TESTS COMPLETED SUCCESSFULLY")
        
        # Check if log file was created
        log_path = "/root/HydraX-v2/logs/stealth_log.txt"
        if os.path.exists(log_path):
            print(f"\n📄 Stealth log file created at: {log_path}")
            # Show last few lines
            with open(log_path, 'r') as f:
                lines = f.readlines()
                if lines:
                    print("\nLast 3 log entries:")
                    for line in lines[-3:]:
                        print(f"  {line.strip()}")
        
    except Exception as e:
        print(f"\n\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import os
    import sys
    
    # Add project root to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Run tests
    asyncio.run(main())