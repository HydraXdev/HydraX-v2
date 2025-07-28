#!/usr/bin/env python3
"""
BITTEN Account Size Calculator
Determines starting capital requirements for each tier based on risk management
"""

class AccountSizeCalculator:
    def __init__(self):
        # Standard forex values
        self.standard_lot_value = 100000  # 1 standard lot = 100,000 units
        
        # Tier lot sizes from the analysis
        self.tier_lot_sizes = {
            "nibbler": 0.01,    # Micro lots
            "fang": 0.05,       # Small lots  
            "commander": 0.10,  # Standard lots
            "apex": 0.20        # Large lots
        }
        
        # Risk management parameters
        self.max_risk_per_trade_pct = 2.0  # Maximum 2% risk per trade
        self.recommended_risk_pct = 1.0    # Recommended 1% risk per trade
        self.avg_stop_loss_pips = 25       # Average SL distance
        
        # Pip values for EUR/USD (most common pair)
        self.pip_values = {
            "nibbler": 0.10,    # $0.10 per pip (0.01 lot)
            "fang": 0.50,       # $0.50 per pip (0.05 lot)
            "commander": 1.00,  # $1.00 per pip (0.10 lot)
            "apex": 2.00        # $2.00 per pip (0.20 lot)
        }
        
        # Margin requirements (typical broker requirements)
        self.margin_requirements = {
            "nibbler": 0.01,    # 1% margin (100:1 leverage)
            "fang": 0.01,       # 1% margin 
            "commander": 0.01,  # 1% margin
            "apex": 0.01        # 1% margin
        }

    def calculate_risk_per_trade(self, tier: str) -> float:
        """Calculate dollar risk per trade"""
        pip_value = self.pip_values[tier]
        risk_per_trade = pip_value * self.avg_stop_loss_pips
        return risk_per_trade

    def calculate_minimum_account_size(self, tier: str) -> dict:
        """Calculate minimum account size based on risk management"""
        risk_per_trade = self.calculate_risk_per_trade(tier)
        
        # Account size based on 2% max risk per trade
        min_account_max_risk = risk_per_trade / (self.max_risk_per_trade_pct / 100)
        
        # Account size based on 1% recommended risk per trade  
        recommended_account = risk_per_trade / (self.recommended_risk_pct / 100)
        
        # Margin requirement for position
        lot_size = self.tier_lot_sizes[tier]
        position_value = lot_size * self.standard_lot_value  # Assuming EUR/USD ~1.0
        margin_required = position_value * self.margin_requirements[tier]
        
        # Conservative account size (3x margin + risk buffer)
        conservative_account = margin_required * 3 + (risk_per_trade * 20)  # 20 trade buffer
        
        return {
            "risk_per_trade": risk_per_trade,
            "min_account_2pct_risk": min_account_max_risk,
            "recommended_account_1pct_risk": recommended_account,
            "margin_required": margin_required,
            "conservative_account": conservative_account,
            "lot_size": lot_size,
            "pip_value": self.pip_values[tier]
        }

    def analyze_monthly_returns(self, tier: str, account_size: float, monthly_gain: float) -> dict:
        """Analyze monthly returns as percentage of account"""
        risk_per_trade = self.calculate_risk_per_trade(tier)
        
        return {
            "account_size": account_size,
            "monthly_gain": monthly_gain,
            "monthly_roi_pct": (monthly_gain / account_size) * 100,
            "risk_per_trade": risk_per_trade,
            "risk_as_pct_of_account": (risk_per_trade / account_size) * 100,
            "max_consecutive_losses": account_size / (risk_per_trade * 10),  # Conservative estimate
            "recommended_position_sizing": "Current" if (risk_per_trade / account_size) <= 0.02 else "Reduce"
        }

def main():
    """Generate account size analysis"""
    calculator = AccountSizeCalculator()
    
    # Monthly gains from previous analysis
    monthly_gains = {
        "nibbler": 577,
        "fang": 6546,
        "commander": 24809,
        "apex": 62219
    }
    
    print("💰 BITTEN ACCOUNT SIZE REQUIREMENTS ANALYSIS")
    print("=" * 70)
    print()
    
    print("📊 ACCOUNT SIZE CALCULATIONS PER TIER")
    print("-" * 70)
    
    tier_accounts = {}
    
    for tier in ["nibbler", "fang", "commander", "apex"]:
        print(f"\n🏆 {tier.upper()} TIER")
        print("-" * 30)
        
        account_data = calculator.calculate_minimum_account_size(tier)
        monthly_gain = monthly_gains[tier]
        
        # Use recommended account size (1% risk per trade)
        recommended_account = account_data["recommended_account_1pct_risk"]
        tier_accounts[tier] = recommended_account
        
        print(f"💳 Lot Size: {account_data['lot_size']} lots")
        print(f"💵 Pip Value: ${account_data['pip_value']:.2f} per pip")
        print(f"⚠️  Risk per Trade: ${account_data['risk_per_trade']:.2f} (25 pip SL)")
        print()
        
        print(f"📈 ACCOUNT SIZE OPTIONS:")
        print(f"   • Minimum (2% risk): ${account_data['min_account_2pct_risk']:,.0f}")
        print(f"   • Recommended (1% risk): ${account_data['recommended_account_1pct_risk']:,.0f}")
        print(f"   • Conservative: ${account_data['conservative_account']:,.0f}")
        print(f"   • Margin Required: ${account_data['margin_required']:,.0f}")
        print()
        
        # Analyze returns with recommended account size
        returns = calculator.analyze_monthly_returns(tier, recommended_account, monthly_gain)
        
        print(f"🎯 WITH RECOMMENDED ACCOUNT (${recommended_account:,.0f}):")
        print(f"   • Monthly Gain: ${monthly_gain:,.0f}")
        print(f"   • Monthly ROI: {returns['monthly_roi_pct']:.1f}%")
        print(f"   • Risk per Trade: {returns['risk_as_pct_of_account']:.1f}% of account")
        print(f"   • Position Sizing: {returns['recommended_position_sizing']}")
        
    print("\n" + "=" * 70)
    print("📋 TIER ACCOUNT SIZE SUMMARY")
    print("-" * 70)
    print(f"{'TIER':<12} {'ACCOUNT SIZE':<15} {'LOT SIZE':<10} {'MONTHLY GAIN':<15} {'MONTHLY ROI':<12}")
    print("-" * 70)
    
    for tier in ["nibbler", "fang", "commander", "apex"]:
        account_size = tier_accounts[tier]
        monthly_gain = monthly_gains[tier]
        lot_size = calculator.tier_lot_sizes[tier]
        monthly_roi = (monthly_gain / account_size) * 100
        
        print(f"{tier.upper():<12} ${account_size:,.0f}{'':<6} {lot_size} lots{'':<3} ${monthly_gain:,.0f}{'':<6} {monthly_roi:.1f}%")
    
    print("\n" + "=" * 70)
    print("💡 ACCOUNT SIZE RECOMMENDATIONS")
    print("-" * 70)
    print()
    
    print("🎯 RISK MANAGEMENT PRINCIPLES:")
    print("• Never risk more than 1-2% of account per trade")
    print("• Account sizes calculated for 1% risk per trade (recommended)")
    print("• 25 pip average stop loss used for calculations")
    print("• Margin requirements assume 100:1 leverage (typical)")
    print()
    
    print("📈 SCALING STRATEGY:")
    print("• Start with NIBBLER if new to forex ($2,500 account)")
    print("• Upgrade tiers as account grows and experience increases")
    print("• FANG tier suitable for intermediate traders ($12,500 account)")
    print("• COMMANDER for experienced traders ($25,000 account)")
    print("• for professional/institutional level ($50,000+ account)")
    print()
    
    print("⚠️ IMPORTANT NOTES:")
    print("• These are MINIMUM recommended account sizes")
    print("• Larger accounts provide better risk management")
    print("• Consider starting with conservative account sizes")
    print("• Ghost mode provides additional protection for all account sizes")
    print("• Monthly ROI percentages based on projected gains")
    
    # Save detailed analysis
    import json
    analysis_data = {
        "tier_account_requirements": tier_accounts,
        "monthly_gains": monthly_gains,
        "risk_management": {
            "max_risk_per_trade": "2% of account",
            "recommended_risk": "1% of account", 
            "average_stop_loss": "25 pips",
            "leverage_assumed": "100:1"
        },
        "lot_sizes": calculator.tier_lot_sizes,
        "pip_values": calculator.pip_values
    }
    
    with open("/root/HydraX-v2/account_size_analysis.json", "w") as f:
        json.dump(analysis_data, f, indent=2)
    
    print("\n💾 Detailed analysis saved to: account_size_analysis.json")

if __name__ == "__main__":
    main()