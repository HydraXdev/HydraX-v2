#!/usr/bin/env python3
"""
BITTEN System Weakness Testing
Systematic testing to find failure points where users could lose money
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from bitten_core.fire_router import FireRouter, TradeRequest, TradeDirection
from bitten_core.fire_modes import TierLevel
from bitten_core.risk_management import RiskManager, RiskProfile, AccountInfo
from bitten_core.bitten_core import BittenCore
import time
from datetime import datetime

def test_basic_execution_bypass():
    """Test 1: Can users bypass basic safety checks?"""
    print("=" * 60)
    print("TEST 1: BASIC EXECUTION BYPASS ATTEMPTS")
    print("=" * 60)
    
    fire_router = FireRouter()
    
    # Edge case: Tiny account with massive trade request
    account = AccountInfo(
        balance=100,  # $100 account
        equity=95,    # Already at 5% loss
        margin=90,
        free_margin=5
    )
    
    profile = RiskProfile(
        user_id=999,
        tier_level='NIBBLER',
        current_xp=0,
        max_risk_percent=2.0
    )
    
    # Attempt massive volume trade
    trade_request = TradeRequest(
        user_id=999,
        symbol='GBPUSD',
        direction=TradeDirection.BUY,
        volume=10.0,  # 10 lots = $1M notional on small account
        tcs_score=95  # High confidence to try to bypass
    )
    
    print(f"Account: ${account.balance}")
    print(f"Requested: {trade_request.volume} lots (${trade_request.volume * 100000:,} notional)")
    print(f"Account risk: {(trade_request.volume * 100000 / account.balance):.1f}x")
    
    try:
        result = fire_router.execute_trade(trade_request)
        print(f"Trade allowed: {result.success}")
        print(f"Message: {result.message}")
        if result.success:
            print("⚠️  WEAKNESS: Large volume trade allowed on small account!")
        else:
            print("✅ Protection working: Trade blocked")
    except Exception as e:
        print(f"❌ SYSTEM ERROR: {e}")
    
    print()

def test_risk_calculation_errors():
    """Test 2: Risk calculation edge cases"""
    print("=" * 60)
    print("TEST 2: RISK CALCULATION EDGE CASES")
    print("=" * 60)
    
    from bitten_core.risk_management import RiskCalculator
    
    calculator = RiskCalculator()
    
    # Test with zero balance
    account_zero = AccountInfo(
        balance=0,
        equity=0,
        margin=0,
        free_margin=0
    )
    
    profile = RiskProfile(
        user_id=999,
        tier_level='NIBBLER',
        max_risk_percent=2.0
    )
    
    print("Testing zero balance account...")
    try:
        result = calculator.calculate_position_size(
            account=account_zero,
            profile=profile,
            symbol='EURUSD',
            entry_price=1.0500,
            stop_loss_price=1.0450  # 50 pip stop
        )
        print(f"Position size calculated: {result.get('lot_size', 'ERROR')}")
        print(f"Can trade: {result.get('can_trade', 'ERROR')}")
        if result.get('lot_size', 0) > 0:
            print("⚠️  WEAKNESS: Trade allowed with zero balance!")
    except Exception as e:
        print(f"❌ CALCULATION ERROR: {e}")
    
    # Test division by zero in stop loss
    print("\nTesting zero stop loss distance...")
    try:
        result = calculator.calculate_position_size(
            account=AccountInfo(balance=1000, equity=1000, margin=0, free_margin=1000),
            profile=profile,
            symbol='EURUSD',
            entry_price=1.0500,
            stop_loss_price=1.0500  # Same price = zero risk distance
        )
        print(f"Position size: {result.get('lot_size', 'ERROR')}")
        if result.get('lot_size', 0) > 0:
            print("⚠️  WEAKNESS: Trade allowed with zero stop distance!")
    except Exception as e:
        print(f"Division by zero handled: {e}")
    
    print()

def test_emergency_stop_bypass():
    """Test 3: Can emergency stops be bypassed?"""
    print("=" * 60)
    print("TEST 3: EMERGENCY STOP BYPASS ATTEMPTS")
    print("=" * 60)
    
    from bitten_core.emergency_stop_controller import EmergencyStopController
    from bitten_core.telegram_router import TelegramRouter
    
    # Create router with emergency controller
    router = TelegramRouter()
    
    # Simulate user hitting emergency stop
    print("Triggering emergency stop...")
    result = router._cmd_emergency_stop(999, ["test_emergency"])
    print(f"Emergency activated: {result.success}")
    print(f"Message: {result.message}")
    
    # Now try to execute trade during emergency
    print("\nAttempting trade during emergency...")
    fire_router = FireRouter()
    
    trade_request = TradeRequest(
        user_id=999,
        symbol='EURUSD',
        direction=TradeDirection.BUY,
        volume=0.1,
        tcs_score=85
    )
    
    try:
        result = fire_router.execute_trade(trade_request)
        print(f"Trade during emergency: {result.success}")
        if result.success:
            print("⚠️  WEAKNESS: Trade executed during emergency stop!")
        else:
            print("✅ Emergency stop working")
    except Exception as e:
        print(f"Emergency stop error: {e}")
    
    print()

def test_concurrent_trading_limits():
    """Test 4: Concurrent trading limit bypass"""
    print("=" * 60)
    print("TEST 4: CONCURRENT TRADING LIMITS")
    print("=" * 60)
    
    fire_router = FireRouter()
    
    # Set low max concurrent trades
    fire_router.max_concurrent_trades = 2
    
    # Try to open multiple trades rapidly
    print("Attempting to open multiple concurrent trades...")
    
    for i in range(5):
        trade_request = TradeRequest(
            user_id=999,
            symbol=f'EURUSD',
            direction=TradeDirection.BUY,
            volume=0.1,
            tcs_score=85
        )
        
        result = fire_router.execute_trade(trade_request)
        print(f"Trade {i+1}: {result.success}")
        
        if result.success:
            # Simulate adding to active trades
            trade_id = f"T{time.time()}{i}"
            fire_router.active_trades[trade_id] = {
                'user_id': 999,
                'symbol': 'EURUSD',
                'volume': 0.1
            }
    
    print(f"Active trades: {len(fire_router.active_trades)}")
    if len(fire_router.active_trades) > fire_router.max_concurrent_trades:
        print("⚠️  WEAKNESS: Exceeded concurrent trade limits!")
    
    print()

def test_tcs_manipulation():
    """Test 5: TCS score manipulation attempts"""
    print("=" * 60)
    print("TEST 5: TCS SCORE MANIPULATION")
    print("=" * 60)
    
    fire_router = FireRouter()
    
    # Test with invalid TCS scores
    invalid_scores = [-1, 0, 101, 999, None]
    
    for score in invalid_scores:
        print(f"Testing TCS score: {score}")
        
        trade_request = TradeRequest(
            user_id=999,
            symbol='EURUSD',
            direction=TradeDirection.BUY,
            volume=0.1,
            tcs_score=score
        )
        
        try:
            result = fire_router.execute_trade(trade_request)
            print(f"  Trade allowed: {result.success}")
            if result.success:
                print(f"  ⚠️  WEAKNESS: Invalid TCS {score} accepted!")
        except Exception as e:
            print(f"  Error handled: {e}")
    
    print()

def test_mt5_bridge_failures():
    """Test 6: MT5 Bridge failure scenarios"""
    print("=" * 60)
    print("TEST 6: MT5 BRIDGE FAILURE SCENARIOS")
    print("=" * 60)
    
    # Test the fire_trade.py bridge script directly
    import subprocess
    
    print("Testing MT5 bridge with invalid parameters...")
    
    # Test with missing symbol
    try:
        result = subprocess.run([
            'python', 'fire_trade.py', 
            '--symbol', '', 
            '--type', 'buy', 
            '--lot', '0.1'
        ], capture_output=True, text=True, timeout=5)
        print(f"Empty symbol result: {result.returncode}")
        if result.returncode == 0:
            print("⚠️  WEAKNESS: Empty symbol accepted by bridge!")
    except Exception as e:
        print(f"Bridge test error: {e}")
    
    # Test with extreme lot size
    try:
        result = subprocess.run([
            'python', 'fire_trade.py',
            '--symbol', 'EURUSD',
            '--type', 'buy', 
            '--lot', '999999'
        ], capture_output=True, text=True, timeout=5)
        print(f"Extreme lot result: {result.returncode}")
        if result.returncode == 0:
            print("⚠️  WEAKNESS: Extreme lot size accepted!")
    except Exception as e:
        print(f"Extreme lot test error: {e}")
    
    print()

def test_timing_attacks():
    """Test 7: Timing-based attacks on cooldowns"""
    print("=" * 60)
    print("TEST 7: TIMING ATTACKS ON COOLDOWNS")
    print("=" * 60)
    
    from bitten_core.fire_modes import FireModeValidator
    
    validator = FireModeValidator()
    
    # Record a shot
    validator.record_shot(999, validator.fire_modes.FireMode.SINGLE_SHOT)
    print("Shot recorded, testing immediate second shot...")
    
    # Try immediate second shot
    can_fire, reason = validator.can_fire(
        user_id=999,
        tier=TierLevel.NIBBLER,
        mode=validator.fire_modes.FireMode.SINGLE_SHOT,
        tcs_score=85
    )
    
    print(f"Immediate second shot allowed: {can_fire}")
    print(f"Reason: {reason}")
    
    if can_fire:
        print("⚠️  WEAKNESS: Cooldown not enforced!")
    else:
        print("✅ Cooldown working properly")
    
    print()

def test_memory_exhaustion():
    """Test 8: Memory exhaustion attacks"""
    print("=" * 60)
    print("TEST 8: MEMORY EXHAUSTION SCENARIOS")
    print("=" * 60)
    
    fire_router = FireRouter()
    
    print("Testing large active trades dictionary...")
    
    # Try to fill active trades with many entries
    start_count = len(fire_router.active_trades)
    
    for i in range(1000):
        trade_id = f"fake_trade_{i}"
        fire_router.active_trades[trade_id] = {
            'user_id': 999,
            'symbol': 'EURUSD',
            'volume': 0.1,
            'timestamp': time.time()
        }
    
    end_count = len(fire_router.active_trades)
    print(f"Added {end_count - start_count} fake trades")
    
    if end_count > 100:
        print("⚠️  WEAKNESS: No limit on active trades dictionary size!")
    
    print()

def run_all_tests():
    """Run all weakness tests"""
    print("BITTEN SYSTEM WEAKNESS ANALYSIS")
    print("=" * 60)
    print("Testing potential failure points and user loss scenarios...")
    print()
    
    tests = [
        test_basic_execution_bypass,
        test_risk_calculation_errors,
        test_emergency_stop_bypass,
        test_concurrent_trading_limits,
        test_tcs_manipulation,
        test_mt5_bridge_failures,
        test_timing_attacks,
        test_memory_exhaustion
    ]
    
    for test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ TEST FAILED: {test_func.__name__} - {e}")
            print()
    
    print("=" * 60)
    print("WEAKNESS ANALYSIS COMPLETE")
    print("Review output above for potential vulnerabilities marked with ⚠️")
    print("=" * 60)

if __name__ == "__main__":
    run_all_tests()