#!/usr/bin/env python3
"""
Test script to verify the HARD LOCK trade size validation
"""

import sys
sys.path.append('/root/HydraX-v2/src')

from bitten_core.fire_router import FireRouter, TradeRequest, TradeDirection, FireMode, TierLevel
from bitten_core.risk_management import RiskManager, RiskCalculator, RiskProfile, AccountInfo

def test_hard_lock_validation():
    """Test various scenarios for the hard lock validation"""
    
    print("🔒 TESTING HARD LOCK TRADE SIZE VALIDATION 🔒\n")
    
    # Initialize components
    fire_router = FireRouter()
    risk_manager = RiskManager()
    risk_calculator = RiskCalculator(risk_manager)
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Normal trade within limits",
            "tier": "NIBBLER",
            "account_balance": 10000,
            "lot_size": 0.20,  # 2% risk with 100 pip SL
            "stop_loss_pips": 100,
            "expected": "PASS"
        },
        {
            "name": "Trade exceeding tier limit",
            "tier": "NIBBLER", 
            "account_balance": 10000,
            "lot_size": 0.50,  # 5% risk with 100 pip SL (exceeds 2% limit)
            "stop_loss_pips": 100,
            "expected": "FAIL"
        },
        {
            "name": "Small account protection",
            "tier": "NIBBLER",
            "account_balance": 500,
            "lot_size": 0.10,  # 20% risk with 100 pip SL
            "stop_loss_pips": 100,
            "expected": "FAIL"
        },
        {
            "name": "APEX tier higher limit",
            "tier": "APEX",
            "account_balance": 10000,
            "lot_size": 0.30,  # 3% risk with 100 pip SL
            "stop_loss_pips": 100,
            "expected": "PASS"
        },
        {
            "name": "Daily cap scenario",
            "tier": "FANG",
            "account_balance": 10000,
            "lot_size": 0.20,
            "stop_loss_pips": 100,
            "daily_loss": -500,  # Already down 5%
            "expected": "FAIL"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"Test {i}: {scenario['name']}")
        print(f"  Tier: {scenario['tier']}")
        print(f"  Account: ${scenario['account_balance']}")
        print(f"  Lot Size: {scenario['lot_size']}")
        print(f"  Stop Loss: {scenario['stop_loss_pips']} pips")
        
        # Create test profile and account
        profile = RiskProfile(
            user_id=1000 + i,
            tier_level=scenario['tier'],
            current_xp=5000,
            max_risk_percent=2.0,
            daily_loss_limit=6.0
        )
        
        account = AccountInfo(
            balance=scenario['account_balance'],
            equity=scenario['account_balance'],
            margin=0,
            free_margin=scenario['account_balance'],
            starting_balance=scenario['account_balance']
        )
        
        # Simulate daily loss if specified
        if 'daily_loss' in scenario:
            session = risk_manager.get_or_create_session(profile.user_id)
            session.daily_pnl = scenario['daily_loss']
        
        # Test validation
        is_valid, reason, safe_lot_size = risk_calculator.validate_trade_size_hard_lock(
            account=account,
            profile=profile,
            lot_size=scenario['lot_size'],
            stop_loss_pips=scenario['stop_loss_pips'],
            symbol="EURUSD"
        )
        
        # Check result
        if scenario['expected'] == "PASS" and is_valid:
            print(f"  ✅ PASSED: Trade allowed")
        elif scenario['expected'] == "FAIL" and not is_valid:
            print(f"  ✅ PASSED: Trade blocked - {reason}")
            if safe_lot_size > 0:
                print(f"  💡 Suggested safe lot size: {safe_lot_size}")
        else:
            print(f"  ❌ FAILED: Expected {scenario['expected']} but got {'PASS' if is_valid else 'FAIL'}")
            print(f"  Reason: {reason}")
        
        print()
    
    # Test through fire router
    print("\n🔥 TESTING THROUGH FIRE ROUTER 🔥\n")
    
    # Set up user tier
    fire_router.user_tiers[1001] = TierLevel.NIBBLER
    
    # Create a risky trade request
    risky_trade = TradeRequest(
        user_id=1001,
        symbol="EURUSD",
        direction=TradeDirection.BUY,
        volume=0.50,  # Too large for Nibbler
        tcs_score=80,
        fire_mode=FireMode.SINGLE_SHOT
    )
    
    print("Attempting risky trade with 0.50 lots...")
    result = fire_router.execute_trade(risky_trade)
    
    if not result.success and "RISK_LIMIT" in result.error_code:
        print(f"✅ Trade correctly blocked by fire router")
        print(f"Message: {result.message}")
    else:
        print(f"❌ Trade was not blocked properly")
        print(f"Result: {result}")

if __name__ == "__main__":
    test_hard_lock_validation()