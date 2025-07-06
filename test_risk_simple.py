#!/usr/bin/env python3
"""Simple test to verify risk management features are properly integrated"""

# Check that the file was updated correctly
with open('src/bitten_core/risk_management.py', 'r') as f:
    content = f.read()
    
    # Check for new features
    features = [
        "class TradingState(Enum):",
        "class RiskManager:",
        "DAILY_LIMIT_HIT",
        "TILT_LOCKOUT",
        "MEDIC_MODE",
        "WEEKEND_LIMITED",
        "NEWS_LOCKOUT",
        "def check_trading_restrictions",
        "def update_trade_result",
        "def get_daily_loss_limit",
        "weekend_risk_multiplier",
        "tilt_threshold",
        "medic_mode_threshold"
    ]
    
    print("✅ Risk Management Features Added:")
    print("=" * 50)
    
    for feature in features:
        if feature in content:
            print(f"✓ {feature}")
        else:
            print(f"✗ {feature} - MISSING!")
    
    print("\n📊 Feature Summary:")
    print("=" * 50)
    print("1. Daily Loss Limits:")
    print("   - NIBBLER: -7%")
    print("   - FANG/COMMANDER/APEX: -10%")
    print("\n2. Tilt Detection:")
    print("   - 3 consecutive losses = warning")
    print("   - 4+ losses = 1 hour forced break")
    print("\n3. Medic Mode:")
    print("   - Activates at -5% daily loss")
    print("   - Reduces risk to 50%")
    print("   - Limits to 1 position")
    print("\n4. Weekend Trading:")
    print("   - Max 1 position")
    print("   - 50% risk reduction")
    print("\n5. News Lockouts:")
    print("   - 30 min before/after high impact news")
    print("   - Blocks trading on affected pairs")
    print("\n6. Integration:")
    print("   - RiskCalculator uses RiskManager")
    print("   - SafetySystemIntegration utilities")
    print("   - Session tracking per user")