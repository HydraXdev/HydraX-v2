#!/usr/bin/env python3
"""
BITTEN Realistic Account Size Calculator
Conservative account sizing based on industry standards and realistic expectations
"""


def calculate_realistic_accounts():
    """Calculate realistic account sizes for sustainable trading"""

    # Monthly gains from analysis
    monthly_gains = {"nibbler": 577, "fang": 6546, "commander": 24809, "apex": 62219}

    # Lot sizes and pip values
    tier_data = {
        "nibbler": {"lot_size": 0.01, "pip_value": 0.10},
        "fang": {"lot_size": 0.05, "pip_value": 0.50},
        "commander": {"lot_size": 0.10, "pip_value": 1.00},
        "apex": {"lot_size": 0.20, "pip_value": 2.00},
    }

    print("💰 REALISTIC BITTEN ACCOUNT SIZE ANALYSIS")
    print("=" * 60)
    print()

    print("🎯 CONSERVATIVE ACCOUNT SIZING APPROACH")
    print("Target: 2-8% monthly ROI (industry sustainable range)")
    print("-" * 60)
    print()

    # Calculate realistic account sizes for sustainable ROI
    target_monthly_roi = {
        "conservative": 0.02,  # 2% monthly
        "moderate": 0.05,  # 5% monthly
        "aggressive": 0.08,  # 8% monthly
    }

    print(f"{'TIER':<12} {'MONTHLY GAIN':<15} {'CONSERVATIVE':<15} {'MODERATE':<12} {'AGGRESSIVE':<12}")
    print(f"{'':12} {'':15} {'(2% ROI)':<15} {'(5% ROI)':<12} {'(8% ROI)':<12}")
    print("-" * 72)

    realistic_accounts = {}

    for tier, gain in monthly_gains.items():
        conservative = gain / target_monthly_roi["conservative"]
        moderate = gain / target_monthly_roi["moderate"]
        aggressive = gain / target_monthly_roi["aggressive"]

        realistic_accounts[tier] = {
            "conservative": conservative,
            "moderate": moderate,
            "aggressive": aggressive,
            "monthly_gain": gain,
        }

        print(
            f"{tier.upper():<12} ${gain:,.0f}{'':<6} ${conservative:,.0f}{'':<6} ${moderate:,.0f}{'':<4} ${aggressive:,.0f}"
        )

    print()
    print("=" * 72)
    print("📊 RECOMMENDED STARTING ACCOUNTS")
    print("-" * 72)
    print()

    # Recommended approach: Use moderate ROI target (5% monthly)
    for tier, data in realistic_accounts.items():
        recommended = data["moderate"]
        monthly_gain = data["monthly_gain"]
        lot_info = tier_data[tier]

        print(f"🏆 {tier.upper()} TIER")
        print(f"   💰 Recommended Account: ${recommended:,.0f}")
        print(f"   📈 Monthly Gain: ${monthly_gain:,.0f}")
        print(f"   📊 Monthly ROI: 5.0%")
        print(f"   💳 Lot Size: {lot_info['lot_size']} lots")
        print(f"   💵 Pip Value: ${lot_info['pip_value']:.2f}/pip")
        print(f"   ⚠️  Risk per Trade: ${lot_info['pip_value'] * 25:.2f} (1% of account)")
        print()

    print("🎯 KEY INSIGHTS:")
    print("-" * 30)
    print("• These account sizes target sustainable 5% monthly ROI")
    print("• Conservative risk management with 1% risk per trade")
    print("• Account sizes allow for proper diversification")
    print("• Higher tiers require significantly more capital")
    print("• ROI percentages are realistic and achievable")
    print()

    print("📈 SCALING RECOMMENDATIONS:")
    print("-" * 30)
    print("• NIBBLER: Start here with $11,500+ account")
    print("• FANG: Intermediate level with $131,000+ account")
    print("• COMMANDER: Advanced level with $496,000+ account")
    print("• : Professional level with $1.24M+ account")
    print()

    print("⚠️ REALITY CHECK:")
    print("-" * 30)
    print("• These projections assume perfect execution of all signals")
    print("• Market conditions will affect actual results")
    print("• Start with smaller accounts to test the system")
    print("• Scale up gradually as confidence and capital grow")
    print("• Ghost mode protection reduces but doesn't eliminate risks")

    return realistic_accounts


if __name__ == "__main__":
    calculate_realistic_accounts()
