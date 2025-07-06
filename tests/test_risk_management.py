#!/usr/bin/env python3
"""Test script for the enhanced risk management system"""

from datetime import datetime, timedelta
from src.bitten_core.risk_management import (
    RiskManager, RiskCalculator, RiskProfile, AccountInfo, 
    NewsEvent, RiskMode, SafetySystemIntegration
)

def test_daily_loss_limit():
    """Test daily loss limit enforcement"""
    print("\n=== Testing Daily Loss Limits ===")
    
    risk_manager = RiskManager()
    calculator = RiskCalculator(risk_manager)
    
    # NIBBLER profile with -7% limit
    profile = RiskProfile(
        user_id=1,
        tier_level="NIBBLER",
        current_xp=100,
        max_risk_percent=2.0
    )
    
    # Account down 8% (exceeds NIBBLER limit)
    account = AccountInfo(
        balance=9200,
        equity=9200,
        margin=0,
        free_margin=9200,
        starting_balance=10000
    )
    
    result = calculator.calculate_position_size(
        account=account,
        profile=profile,
        symbol="EURUSD",
        entry_price=1.1000,
        stop_loss_price=1.0950
    )
    
    print(f"Can trade: {result['can_trade']}")
    print(f"Reason: {result.get('reason', 'N/A')}")
    
    # Test with APEX profile (-10% limit)
    profile.tier_level = "APEX"
    result = calculator.calculate_position_size(
        account=account,
        profile=profile,
        symbol="EURUSD",
        entry_price=1.1000,
        stop_loss_price=1.0950
    )
    
    print(f"\nAPEX tier can trade: {result['can_trade']}")

def test_tilt_detection():
    """Test tilt detection and forced breaks"""
    print("\n=== Testing Tilt Detection ===")
    
    risk_manager = RiskManager()
    profile = RiskProfile(user_id=2, tier_level="FANG", current_xp=1000)
    account = AccountInfo(balance=10000, equity=10000, margin=0, free_margin=10000)
    
    # Simulate 3 consecutive losses
    for i in range(3):
        risk_manager.update_trade_result(profile, won=False, pnl=-100)
    
    # Check status
    status = risk_manager.check_trading_restrictions(profile, account, "EURUSD")
    print(f"After 3 losses - Can trade: {status['can_trade']}")
    print(f"Restrictions: {status['restrictions']}")
    
    # One more loss should trigger tilt lockout
    risk_manager.update_trade_result(profile, won=False, pnl=-100)
    status = risk_manager.check_trading_restrictions(profile, account, "EURUSD")
    print(f"\nAfter 4 losses - Can trade: {status['can_trade']}")
    print(f"Reason: {status.get('reason', 'N/A')}")

def test_medic_mode():
    """Test medic mode activation"""
    print("\n=== Testing Medic Mode ===")
    
    risk_manager = RiskManager()
    calculator = RiskCalculator(risk_manager)
    
    profile = RiskProfile(user_id=3, tier_level="COMMANDER", max_risk_percent=2.0)
    
    # Account down 5.5% (triggers medic mode at -5%)
    account = AccountInfo(
        balance=9450,
        equity=9450,
        margin=0,
        free_margin=9450,
        starting_balance=10000
    )
    
    result = calculator.calculate_position_size(
        account=account,
        profile=profile,
        symbol="GBPUSD",
        entry_price=1.2500,
        stop_loss_price=1.2450
    )
    
    print(f"Can trade: {result['can_trade']}")
    print(f"Normal risk: 2.0%")
    print(f"Adjusted risk: {result['risk_percent']:.2f}%")
    print(f"Restrictions: {result['restrictions']}")

def test_weekend_limits():
    """Test weekend trading restrictions"""
    print("\n=== Testing Weekend Limits ===")
    
    risk_manager = RiskManager()
    calculator = RiskCalculator(risk_manager)
    
    profile = RiskProfile(user_id=4, tier_level="FANG")
    account = AccountInfo(balance=10000, equity=10000, margin=0, free_margin=10000)
    
    # Note: This will only show weekend restrictions if run on a weekend
    result = calculator.calculate_position_size(
        account=account,
        profile=profile,
        symbol="XAUUSD",
        entry_price=2000,
        stop_loss_price=1990
    )
    
    if datetime.now().weekday() >= 5:
        print("Weekend restrictions active!")
        print(f"Restrictions: {result['restrictions']}")
    else:
        print("Not weekend - no weekend restrictions")
        print("(Run on Saturday/Sunday to see weekend limits)")

def test_news_lockout():
    """Test news event lockouts"""
    print("\n=== Testing News Lockouts ===")
    
    risk_manager = RiskManager()
    calculator = RiskCalculator(risk_manager)
    
    # Add high impact news in 15 minutes
    news_event = NewsEvent(
        event_time=datetime.now() + timedelta(minutes=15),
        currency="USD",
        impact="high",
        event_name="FOMC Rate Decision"
    )
    risk_manager.add_news_event(news_event)
    
    profile = RiskProfile(user_id=5, tier_level="APEX")
    account = AccountInfo(balance=10000, equity=10000, margin=0, free_margin=10000)
    
    # Try to trade EURUSD (contains USD)
    result = calculator.calculate_position_size(
        account=account,
        profile=profile,
        symbol="EURUSD",
        entry_price=1.1000,
        stop_loss_price=1.0950
    )
    
    print(f"Can trade EURUSD: {result['can_trade']}")
    print(f"Reason: {result.get('reason', 'Trading allowed')}")
    
    # Try GBPJPY (no USD)
    result = calculator.calculate_position_size(
        account=account,
        profile=profile,
        symbol="GBPJPY",
        entry_price=150.00,
        stop_loss_price=149.50
    )
    
    print(f"\nCan trade GBPJPY: {result['can_trade']}")

def test_session_stats():
    """Test session statistics tracking"""
    print("\n=== Testing Session Stats ===")
    
    risk_manager = RiskManager()
    profile = RiskProfile(user_id=6, tier_level="NIBBLER")
    
    # Simulate a trading session
    risk_manager.update_trade_result(profile, won=True, pnl=150)
    risk_manager.update_trade_result(profile, won=True, pnl=200)
    risk_manager.update_trade_result(profile, won=False, pnl=-100)
    risk_manager.update_trade_result(profile, won=True, pnl=175)
    
    # Get stats
    stats = SafetySystemIntegration.get_session_stats(risk_manager, profile.user_id)
    
    print(f"Trades today: {stats['trades_today']}")
    print(f"Consecutive wins: {stats['consecutive_wins']}")
    print(f"Daily P&L: ${stats['daily_pnl']}")
    print(f"Current state: {stats['current_state']}")
    print(f"Can trade: {stats['can_trade']}")

if __name__ == "__main__":
    print("BITTEN Risk Management System - Safety Features Test")
    print("=" * 50)
    
    test_daily_loss_limit()
    test_tilt_detection()
    test_medic_mode()
    test_weekend_limits()
    test_news_lockout()
    test_session_stats()
    
    print("\n" + "=" * 50)
    print("All tests completed!")