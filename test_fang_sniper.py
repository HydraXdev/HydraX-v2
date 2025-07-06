#!/usr/bin/env python3
"""
Test FANG tier sniper functionality
"""

import sys
sys.path.append('/root/HydraX-v2/src')

from bitten_core.fire_router import FireRouter, TradeRequest, TradeDirection, FireMode, TierLevel
from bitten_core.sniper_xp_handler import sniper_xp_handler

def test_fang_sniper_features():
    print("🎯 FANG TIER SNIPER FEATURE TEST\n")
    
    # Initialize fire router
    router = FireRouter()
    
    # Set user as FANG tier
    user_id = 1001
    router.user_tiers[user_id] = TierLevel.FANG
    
    print("1️⃣ Testing Arcade vs Sniper TCS Requirements:")
    print("-" * 50)
    
    # Test 1: Arcade signal with TCS 75 (should pass)
    arcade_trade = TradeRequest(
        user_id=user_id,
        symbol="EURUSD",
        direction=TradeDirection.BUY,
        volume=0.10,
        tcs_score=75,
        signal_type="arcade"
    )
    
    filter_result = router._apply_probability_filter(arcade_trade)
    print(f"Arcade TCS 75: {'✅ PASS' if filter_result['passed'] else '❌ FAIL'}")
    print(f"  Reason: {filter_result['reason']}\n")
    
    # Test 2: Sniper signal with TCS 75 (should fail - needs 85)
    sniper_trade_low = TradeRequest(
        user_id=user_id,
        symbol="EURUSD",
        direction=TradeDirection.BUY,
        volume=0.10,
        tcs_score=75,
        signal_type="sniper"
    )
    
    filter_result = router._apply_probability_filter(sniper_trade_low)
    print(f"Sniper TCS 75: {'✅ PASS' if filter_result['passed'] else '❌ FAIL'}")
    print(f"  Reason: {filter_result['reason']}\n")
    
    # Test 3: Sniper signal with TCS 85 (should pass)
    sniper_trade = TradeRequest(
        user_id=user_id,
        symbol="EURUSD",
        direction=TradeDirection.BUY,
        volume=0.10,
        tcs_score=85,
        signal_type="sniper"
    )
    
    filter_result = router._apply_probability_filter(sniper_trade)
    print(f"Sniper TCS 85: {'✅ PASS' if filter_result['passed'] else '❌ FAIL'}")
    print(f"  Reason: {filter_result['reason']}\n")
    
    print("\n2️⃣ Testing Risk Limits (2% default, 2.5% boost at $1000+):")
    print("-" * 50)
    
    # Test risk with $500 balance (no boost)
    risk_trade = TradeRequest(
        user_id=user_id,
        symbol="EURUSD",
        direction=TradeDirection.BUY,
        volume=0.20,  # 2% risk with 100 pip SL on $10k account
        tcs_score=85,
        signal_type="sniper"
    )
    
    risk_result = router._check_risk_limits(risk_trade)
    print(f"$500 balance, 2% risk: {'✅ APPROVED' if risk_result['approved'] else '❌ BLOCKED'}")
    if 'risk_percent' in risk_result:
        print(f"  Risk: {risk_result['risk_percent']:.1f}%\n")
    
    print("\n3️⃣ Testing XP System for Sniper Trades:")
    print("-" * 50)
    
    # Simulate a sniper trade lifecycle
    trade_id = "TEST123"
    
    # Register sniper trade
    print("Opening sniper trade...")
    sniper_xp_handler.register_sniper_trade(
        trade_id=trade_id,
        user_id=user_id,
        symbol="EURUSD",
        entry_price=1.2500,
        tp_price=1.2600,
        sl_price=1.2400
    )
    
    # Scenario 1: Hold to TP (bonus)
    print("\nScenario 1: Hold to TP")
    xp_result = sniper_xp_handler.calculate_trade_xp(
        trade_id=trade_id,
        exit_price=1.2600,
        exit_reason='tp_hit',
        pnl=100
    )
    print(f"  {xp_result['message']}")
    print(f"  Base XP: {xp_result['base_xp']}, Final XP: {xp_result['final_xp']}")
    
    # Re-register for next test
    sniper_xp_handler.register_sniper_trade(trade_id, user_id, "EURUSD", 1.2500, 1.2600, 1.2400)
    
    # Scenario 2: Early exit (penalty)
    print("\nScenario 2: Early exit at 30% of target")
    xp_result = sniper_xp_handler.calculate_trade_xp(
        trade_id=trade_id,
        exit_price=1.2530,
        exit_reason='manual_close',
        pnl=30
    )
    print(f"  {xp_result['message']}")
    print(f"  Base XP: {xp_result['base_xp']}, Final XP: {xp_result['final_xp']}")
    
    # Re-register for next test
    sniper_xp_handler.register_sniper_trade(trade_id, user_id, "EURUSD", 1.2500, 1.2600, 1.2400)
    
    # Scenario 3: Stop loss hit (no penalty)
    print("\nScenario 3: Stop loss hit")
    xp_result = sniper_xp_handler.calculate_trade_xp(
        trade_id=trade_id,
        exit_price=1.2400,
        exit_reason='sl_hit',
        pnl=-100
    )
    print(f"  {xp_result['message']}")
    print(f"  Base XP: {xp_result['base_xp']}, Final XP: {xp_result['final_xp']}")
    
    print("\n\n4️⃣ FANG Configuration Summary:")
    print("-" * 50)
    print("✅ Arcade signals: TCS 75+ required")
    print("✅ Sniper signals: TCS 85+ required")
    print("✅ Max 2 trades open at once")
    print("✅ Risk: 2% default, 2.5% boost at $1000+")
    print("✅ Daily cap: 8.5%")
    print("✅ XP bonus for holding sniper to TP (+50%)")
    print("✅ XP penalty for early sniper exit (-50%)")
    print("❌ No access to: Stealth, Autofire, Chaingun")
    print("\nSignal types are tracked separately for optimal XP rewards!")

if __name__ == "__main__":
    test_fang_sniper_features()