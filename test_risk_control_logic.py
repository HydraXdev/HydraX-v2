#!/usr/bin/env python3
"""
Test script to verify risk control implementation logic
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from bitten_core.risk_controller import RiskController, TierLevel, RiskMode
from datetime import datetime, timezone
import json

def test_risk_controller():
    """Test all risk controller functionality"""
    
    print("🔍 TESTING RISK CONTROLLER LOGIC\n")
    
    # Initialize controller with test directory
    test_dir = "/tmp/test_risk_control"
    os.makedirs(test_dir, exist_ok=True)
    controller = RiskController(data_dir=test_dir)
    
    # Test user IDs
    test_user_id = 12345
    
    print("1️⃣ Testing State Persistence and Loading")
    print("-" * 50)
    
    # Test initial state
    risk_percent, reason = controller.get_user_risk_percent(test_user_id, TierLevel.NIBBLER)
    print(f"Initial risk for NIBBLER: {risk_percent}% - {reason}")
    assert risk_percent == 1.0, "Default NIBBLER risk should be 1.0%"
    
    # Toggle to boost mode
    success, msg = controller.toggle_risk_mode(test_user_id, TierLevel.NIBBLER, RiskMode.BOOST)
    print(f"Toggle to BOOST: {success} - {msg}")
    assert success, "Should be able to toggle to boost mode"
    
    # Verify persistence
    risk_percent, reason = controller.get_user_risk_percent(test_user_id, TierLevel.NIBBLER)
    print(f"After toggle: {risk_percent}% - {reason}")
    assert risk_percent == 1.5, "NIBBLER boost mode should be 1.5%"
    
    print("\n2️⃣ Testing Risk Percentage Calculations")
    print("-" * 50)
    
    # Test different tiers
    tiers_and_modes = [
        (TierLevel.NIBBLER, RiskMode.DEFAULT, 1.0),
        (TierLevel.NIBBLER, RiskMode.BOOST, 1.5),
        (TierLevel.FANG, RiskMode.DEFAULT, 1.25),
        (TierLevel.FANG, RiskMode.HIGH_RISK, 2.0),
        (TierLevel.COMMANDER, RiskMode.DEFAULT, 1.25),
        (TierLevel.COMMANDER, RiskMode.HIGH_RISK, 2.0),
        (TierLevel.APEX, RiskMode.DEFAULT, 1.25),
        (TierLevel.APEX, RiskMode.HIGH_RISK, 2.0),
    ]
    
    for tier, mode, expected in tiers_and_modes:
        # Reset mode
        controller.toggle_risk_mode(test_user_id, tier, mode)
        risk_percent, reason = controller.get_user_risk_percent(test_user_id, tier)
        print(f"{tier.value} + {mode.value}: {risk_percent}% (expected: {expected}%)")
        assert risk_percent == expected, f"Incorrect risk for {tier.value} {mode.value}"
    
    print("\n3️⃣ Testing Trade Blocking Logic")
    print("-" * 50)
    
    # Test daily trade limits
    controller.profiles[test_user_id].daily_trades = 5
    controller.profiles[test_user_id].tier = TierLevel.NIBBLER
    
    allowed, reason = controller.check_trade_allowed(test_user_id, TierLevel.NIBBLER, 100, 10000)
    print(f"With 5 trades (NIBBLER limit 6): {allowed} - {reason}")
    assert allowed, "Should allow 6th trade for NIBBLER"
    
    controller.profiles[test_user_id].daily_trades = 6
    allowed, reason = controller.check_trade_allowed(test_user_id, TierLevel.NIBBLER, 100, 10000)
    print(f"With 6 trades (NIBBLER limit 6): {allowed} - {reason}")
    assert not allowed, "Should block 7th trade for NIBBLER"
    assert "Daily trade limit" in reason
    
    # Test drawdown limit
    controller.profiles[test_user_id].daily_trades = 0
    controller.profiles[test_user_id].daily_loss = 500  # 5% of 10k
    
    allowed, reason = controller.check_trade_allowed(test_user_id, TierLevel.NIBBLER, 200, 10000)
    print(f"With 5% loss + 2% potential (NIBBLER limit 6%): {allowed} - {reason}")
    assert not allowed, "Should block trade that would exceed drawdown"
    assert "drawdown" in reason.lower()
    
    print("\n4️⃣ Testing Cooldown Trigger Logic")
    print("-" * 50)
    
    # Reset state
    controller.profiles[test_user_id].daily_trades = 0
    controller.profiles[test_user_id].daily_loss = 0
    controller.profiles[test_user_id].consecutive_high_risk_losses = 0
    controller.toggle_risk_mode(test_user_id, TierLevel.FANG, RiskMode.HIGH_RISK)
    
    # First high-risk loss
    controller.record_trade_result(test_user_id, TierLevel.FANG, won=False, pnl=-200, risk_percent=2.0)
    print(f"After 1st high-risk loss: {controller.profiles[test_user_id].consecutive_high_risk_losses} losses")
    assert not controller._is_in_cooldown(test_user_id), "Should not trigger cooldown after 1 loss"
    
    # Second high-risk loss - should trigger cooldown
    controller.record_trade_result(test_user_id, TierLevel.FANG, won=False, pnl=-200, risk_percent=2.0)
    print(f"After 2nd high-risk loss: {controller.profiles[test_user_id].consecutive_high_risk_losses} losses")
    assert controller._is_in_cooldown(test_user_id), "Should trigger cooldown after 2 consecutive high-risk losses"
    
    # Check cooldown state
    cooldown = controller.cooldowns.get(test_user_id)
    print(f"Cooldown active until: {cooldown.expires_at if cooldown else 'N/A'}")
    print(f"Cooldown reason: {cooldown.trigger_reason if cooldown else 'N/A'}")
    
    # Verify risk is forced to 1.0% during cooldown
    risk_percent, reason = controller.get_user_risk_percent(test_user_id, TierLevel.FANG)
    print(f"Risk during cooldown: {risk_percent}% - {reason}")
    assert risk_percent == 1.0, "Risk should be forced to 1.0% during cooldown"
    assert "Cooldown active" in reason
    
    # Verify can't change risk mode during cooldown
    success, msg = controller.toggle_risk_mode(test_user_id, TierLevel.FANG, RiskMode.HIGH_RISK)
    print(f"Try to toggle during cooldown: {success} - {msg}")
    assert not success, "Should not be able to change risk mode during cooldown"
    assert "cooldown" in msg.lower()
    
    print("\n5️⃣ Testing Daily Reset Functionality")
    print("-" * 50)
    
    # Set some daily stats
    controller.profiles[test_user_id].daily_trades = 5
    controller.profiles[test_user_id].daily_loss = 300
    controller.profiles[test_user_id].last_trade_date = "2024-01-01"
    
    # Trigger reset by checking trade with new date
    controller._check_daily_reset(controller.profiles[test_user_id])
    
    print(f"After daily reset:")
    print(f"  Daily trades: {controller.profiles[test_user_id].daily_trades}")
    print(f"  Daily loss: {controller.profiles[test_user_id].daily_loss}")
    print(f"  Consecutive losses: {controller.profiles[test_user_id].consecutive_high_risk_losses}")
    
    assert controller.profiles[test_user_id].daily_trades == 0, "Daily trades should reset"
    assert controller.profiles[test_user_id].daily_loss == 0, "Daily loss should reset"
    # Note: consecutive losses should NOT reset on new day
    
    print("\n6️⃣ Testing Integration Points")
    print("-" * 50)
    
    # Test get_user_status
    status = controller.get_user_status(test_user_id, TierLevel.FANG, 10000)
    print(f"User status:")
    print(f"  Tier: {status['tier']}")
    print(f"  Risk mode: {status['risk_mode']}")
    print(f"  Current risk: {status['current_risk_percent']}%")
    print(f"  Daily trades: {status['daily_trades']}/{status['max_daily_trades']}")
    print(f"  Daily drawdown: {status['daily_drawdown_percent']:.2f}%")
    print(f"  Cooldown active: {status['cooldown'] is not None}")
    
    print("\n7️⃣ Testing File Persistence")
    print("-" * 50)
    
    # Check files were created
    profile_file = os.path.join(test_dir, "risk_profiles.json")
    cooldown_file = os.path.join(test_dir, "cooldown_state.json")
    
    print(f"Profile file exists: {os.path.exists(profile_file)}")
    print(f"Cooldown file exists: {os.path.exists(cooldown_file)}")
    
    # Read and verify content
    if os.path.exists(profile_file):
        with open(profile_file, 'r') as f:
            profiles = json.load(f)
            print(f"Profiles saved: {len(profiles)}")
            print(f"Test user profile: {json.dumps(profiles.get(str(test_user_id)), indent=2)}")
    
    if os.path.exists(cooldown_file):
        with open(cooldown_file, 'r') as f:
            cooldowns = json.load(f)
            print(f"Cooldowns saved: {len(cooldowns)}")
    
    print("\n✅ ALL TESTS PASSED!")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)

if __name__ == "__main__":
    test_risk_controller()