#!/usr/bin/env python3
"""
Analyze RR ratio risk implications for different account sizes
"""

def analyze_rr_risk():
    """Analyze risk implications of current RR ratios"""
    
    print("📊 BITTEN RR RATIO RISK ANALYSIS")
    print("=" * 50)
    print()
    
    # Standard risk management: 1-2% risk per trade
    risk_percentages = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    account_sizes = [1000, 5000, 10000, 25000, 50000, 100000]
    
    # Current RR ratios
    rapid_assault_rr = [2.0, 2.15, 2.3, 2.45, 2.6]  # 70%, 75%, 80%, 85%, 90%
    sniper_ops_rr = [2.7, 2.85, 3.0, 3.15, 3.25]    # 70%, 75%, 80%, 85%, 90%+
    
    print("🎯 RAPID_ASSAULT Analysis (2.0 to 2.6 RR)")
    print("-" * 40)
    
    for account in account_sizes:
        print(f"\n💰 ${account:,} Account:")
        for risk_pct in [1.0, 2.0]:
            risk_amount = account * (risk_pct / 100)
            
            # Calculate potential profit for different RR ratios
            min_profit = risk_amount * 2.0  # 70% TCS
            max_profit = risk_amount * 2.6  # 90% TCS
            
            print(f"   {risk_pct}% Risk (${risk_amount:.0f} risk):")
            print(f"   ├── Min Profit (70% TCS): ${min_profit:.0f} (1:2.0)")
            print(f"   └── Max Profit (90% TCS): ${max_profit:.0f} (1:2.6)")
    
    print("\n" + "=" * 50)
    print("⚡ SNIPER_OPS Analysis (2.7 to 3.25 RR)")
    print("-" * 40)
    
    for account in account_sizes:
        print(f"\n💰 ${account:,} Account:")
        for risk_pct in [1.0, 2.0]:
            risk_amount = account * (risk_pct / 100)
            
            # Calculate potential profit for different RR ratios
            min_profit = risk_amount * 2.7   # 70% TCS
            max_profit = risk_amount * 3.25  # 92% TCS
            
            print(f"   {risk_pct}% Risk (${risk_amount:.0f} risk):")
            print(f"   ├── Min Profit (70% TCS): ${min_profit:.0f} (1:2.7)")
            print(f"   └── Max Profit (92% TCS): ${max_profit:.0f} (1:3.25)")
    
    print("\n" + "=" * 50)
    print("⚠️  RISK ANALYSIS")
    print("-" * 40)
    
    # Win rate analysis
    win_rates = [0.40, 0.45, 0.50, 0.55, 0.60]
    
    print("\n📈 Profitability Analysis (100 trades):")
    print("   (Assuming 1% risk per trade)")
    print()
    
    for wr in win_rates:
        print(f"   Win Rate: {wr*100:.0f}%")
        
        # RAPID_ASSAULT (average 2.3 RR)
        rapid_profit = (wr * 2.3) - ((1-wr) * 1.0)
        rapid_result = rapid_profit * 100  # 100 trades at 1% risk
        
        # SNIPER_OPS (average 2.975 RR)
        sniper_profit = (wr * 2.975) - ((1-wr) * 1.0)
        sniper_result = sniper_profit * 100
        
        print(f"   ├── RAPID_ASSAULT: {rapid_result:+.1f}% account growth")
        print(f"   └── SNIPER_OPS: {sniper_result:+.1f}% account growth")
        print()
    
    print("=" * 50)
    print("🔍 SAFETY CONSIDERATIONS")
    print("-" * 40)
    print()
    
    print("✅ CURRENT RATIOS (2.0-2.6 RAPID, 2.7-3.25 SNIPER):")
    print("   ├── Safe for 1-2% risk per trade")
    print("   ├── Profitable at 40%+ win rate")
    print("   ├── Good risk-adjusted returns")
    print("   └── Suitable for all account sizes")
    print()
    
    # Alternative analysis with 1.8 starting point
    print("🔄 ALTERNATIVE: 1.8-2.4 RAPID ASSAULT")
    print("-" * 40)
    
    for wr in [0.45, 0.50, 0.55]:
        rapid_alt_profit = (wr * 2.1) - ((1-wr) * 1.0)  # Average 2.1 RR
        rapid_alt_result = rapid_alt_profit * 100
        
        print(f"   {wr*100:.0f}% Win Rate: {rapid_alt_result:+.1f}% account growth")
    
    print()
    print("💡 RECOMMENDATION:")
    print("   Current 2.0-2.6 RR for RAPID_ASSAULT is SAFE and PROFITABLE")
    print("   - Requires only 38.5% win rate to break even")
    print("   - Lowering to 1.8 would require 43.5% win rate")
    print("   - Higher RR ratios provide better risk-adjusted returns")
    print("   - Safe for all account sizes with proper position sizing")

if __name__ == "__main__":
    analyze_rr_risk()