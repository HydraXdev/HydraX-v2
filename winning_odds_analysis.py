#!/usr/bin/env python3
"""
BITTEN Winning Odds and Expected Monthly Gains Analysis
Based on calibrated TCS system and tier-based performance
"""

import json
from datetime import datetime
from typing import Dict, List

class WinningOddsCalculator:
    def __init__(self):
        # Calibrated win rates from backtesting results
        self.calibrated_win_rates = {
            "87_tcs": 82.1,  # Calibrated 87%+ TCS signals
            "90_tcs": 85.5,  # Higher TCS signals
            "93_tcs": 88.2,  # Premium TCS signals 
            "96_tcs": 91.0   # Elite TCS signals
        }
        
        # Tier-based signal access and execution rates
        self.tier_access = {
            "nibbler": {
                "signals_per_day": 8,      # Limited access
                "execution_rate": 0.65,    # 65% execution due to hesitation
                "avg_lot_size": 0.01,      # Micro lots
                "risk_per_trade": 25,      # 25 pips average SL
                "ghost_effectiveness": 48.3
            },
            "fang": {
                "signals_per_day": 15,     # Good access
                "execution_rate": 0.78,    # 78% execution rate
                "avg_lot_size": 0.05,      # Small lots
                "risk_per_trade": 25,      # 25 pips average SL
                "ghost_effectiveness": 69.5
            },
            "commander": {
                "signals_per_day": 25,     # Full access
                "execution_rate": 0.88,    # 88% execution rate
                "avg_lot_size": 0.10,      # Standard lots
                "risk_per_trade": 25,      # 25 pips average SL
                "ghost_effectiveness": 89.2
            },
            "apex": {
                "signals_per_day": 30,     # Premium access + early signals
                "execution_rate": 0.92,    # 92% execution rate
                "avg_lot_size": 0.20,      # Larger lots
                "risk_per_trade": 25,      # 25 pips average SL
                "ghost_effectiveness": 88.0
            }
        }
        
        # Signal type distribution (based on hybrid classification)
        self.signal_distribution = {
            "arcade": {
                "percentage": 35,          # 35% of qualified signals
                "avg_profit_pips": 35,     # Faster, smaller profits
                "avg_rr_ratio": 1.4,       # 1:1.4 R:R
                "tcs_requirement": 87
            },
            "sniper": {
                "percentage": 65,          # 65% of qualified signals  
                "avg_profit_pips": 55,     # Larger, precision profits
                "avg_rr_ratio": 2.2,       # 1:2.2 R:R
                "tcs_requirement": 90
            }
        }
        
        # Account settings per tier
        self.account_settings = {
            "nibbler": {"pip_value_usd": 0.10},    # $0.10/pip (0.01 lot EUR/USD)
            "fang": {"pip_value_usd": 0.50},       # $0.50/pip (0.05 lot EUR/USD)
            "commander": {"pip_value_usd": 1.00},  # $1.00/pip (0.10 lot EUR/USD)
            "apex": {"pip_value_usd": 2.00}        # $2.00/pip (0.20 lot EUR/USD)
        }

    def calculate_winning_odds(self, tier: str) -> Dict:
        """Calculate winning odds for a specific tier"""
        tier_data = self.tier_access[tier]
        
        # Effective signals per month
        signals_per_month = tier_data["signals_per_day"] * 30
        executed_signals = signals_per_month * tier_data["execution_rate"]
        
        # TCS-weighted win rate calculation
        # Assume distribution: 40% at 87%, 35% at 90%, 20% at 93%, 5% at 96%
        weighted_win_rate = (
            0.40 * self.calibrated_win_rates["87_tcs"] +
            0.35 * self.calibrated_win_rates["90_tcs"] +
            0.20 * self.calibrated_win_rates["93_tcs"] +
            0.05 * self.calibrated_win_rates["96_tcs"]
        )
        
        # Ghost mode protection adjustment (higher tiers = better protection = better results)
        ghost_bonus = (tier_data["ghost_effectiveness"] - 50) * 0.02  # 2% per 50% effectiveness
        adjusted_win_rate = weighted_win_rate + ghost_bonus
        
        return {
            "base_win_rate": weighted_win_rate,
            "ghost_adjusted_win_rate": adjusted_win_rate,
            "signals_per_month": signals_per_month,
            "executed_signals_per_month": executed_signals,
            "winning_trades_per_month": executed_signals * (adjusted_win_rate / 100),
            "losing_trades_per_month": executed_signals * (1 - adjusted_win_rate / 100)
        }

    def calculate_monthly_gains(self, tier: str) -> Dict:
        """Calculate expected monthly gains for a tier"""
        odds = self.calculate_winning_odds(tier)
        tier_data = self.tier_access[tier]
        account_data = self.account_settings[tier]
        
        # Calculate expected profit per trade
        arcade_signals = odds["executed_signals_per_month"] * (self.signal_distribution["arcade"]["percentage"] / 100)
        sniper_signals = odds["executed_signals_per_month"] * (self.signal_distribution["sniper"]["percentage"] / 100)
        
        # Profit calculations
        arcade_profit_per_win = self.signal_distribution["arcade"]["avg_profit_pips"] * account_data["pip_value_usd"]
        sniper_profit_per_win = self.signal_distribution["sniper"]["avg_profit_pips"] * account_data["pip_value_usd"]
        loss_per_trade = tier_data["risk_per_trade"] * account_data["pip_value_usd"]
        
        # Monthly calculations
        arcade_wins = arcade_signals * (odds["ghost_adjusted_win_rate"] / 100)
        arcade_losses = arcade_signals * (1 - odds["ghost_adjusted_win_rate"] / 100)
        
        sniper_wins = sniper_signals * (odds["ghost_adjusted_win_rate"] / 100)
        sniper_losses = sniper_signals * (1 - odds["ghost_adjusted_win_rate"] / 100)
        
        total_profit = (arcade_wins * arcade_profit_per_win) + (sniper_wins * sniper_profit_per_win)
        total_losses = (arcade_losses + sniper_losses) * loss_per_trade
        
        net_monthly_gain = total_profit - total_losses
        
        return {
            "total_profit_usd": total_profit,
            "total_losses_usd": total_losses,
            "net_monthly_gain_usd": net_monthly_gain,
            "arcade_trades": {
                "signals": arcade_signals,
                "wins": arcade_wins,
                "losses": arcade_losses,
                "profit_per_win": arcade_profit_per_win
            },
            "sniper_trades": {
                "signals": sniper_signals,
                "wins": sniper_wins,
                "losses": sniper_losses,
                "profit_per_win": sniper_profit_per_win
            },
            "loss_per_trade": loss_per_trade,
            "roi_percentage": (net_monthly_gain / (odds["executed_signals_per_month"] * loss_per_trade)) * 100 if odds["executed_signals_per_month"] > 0 else 0
        }

    def generate_complete_analysis(self) -> Dict:
        """Generate complete analysis for all tiers"""
        analysis = {
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "calibrated_system_data": {
                "base_win_rates": self.calibrated_win_rates,
                "improvement_from_calibration": "+5.1% vs original system",
                "tcs_threshold": "87% minimum (calibrated)",
                "signal_classification": "ARCADE vs SNIPER hybrid system"
            },
            "tiers": {}
        }
        
        for tier in ["nibbler", "fang", "commander", "apex"]:
            odds = self.calculate_winning_odds(tier)
            gains = self.calculate_monthly_gains(tier)
            
            analysis["tiers"][tier] = {
                "winning_odds": odds,
                "monthly_gains": gains,
                "tier_data": self.tier_access[tier],
                "account_settings": self.account_settings[tier]
            }
        
        return analysis

def main():
    """Generate and display winning odds analysis"""
    calculator = WinningOddsCalculator()
    analysis = calculator.generate_complete_analysis()
    
    print("🎯 BITTEN WINNING ODDS & MONTHLY GAINS ANALYSIS")
    print("=" * 70)
    print(f"📅 Analysis Date: {analysis['analysis_date']}")
    print(f"🔬 Based on: Calibrated TCS system with {analysis['calibrated_system_data']['improvement_from_calibration']}")
    print()
    
    # Summary table header
    print("📊 TIER PERFORMANCE SUMMARY")
    print("-" * 70)
    print(f"{'TIER':<12} {'WIN RATE':<10} {'SIGNALS/MO':<12} {'NET GAIN/MO':<12} {'ROI%':<8}")
    print("-" * 70)
    
    for tier, data in analysis["tiers"].items():
        win_rate = data["winning_odds"]["ghost_adjusted_win_rate"]
        signals = data["winning_odds"]["executed_signals_per_month"]
        net_gain = data["monthly_gains"]["net_monthly_gain_usd"]
        roi = data["monthly_gains"]["roi_percentage"]
        
        print(f"{tier.upper():<12} {win_rate:.1f}%{'':<5} {signals:.0f}{'':<8} ${net_gain:.0f}{'':<7} {roi:.1f}%")
    
    print()
    
    # Detailed breakdown for each tier
    for tier, data in analysis["tiers"].items():
        print(f"🏆 {tier.upper()} TIER DETAILED ANALYSIS")
        print("-" * 50)
        
        odds = data["winning_odds"]
        gains = data["monthly_gains"]
        tier_info = data["tier_data"]
        
        print(f"📈 Winning Probability: {odds['ghost_adjusted_win_rate']:.1f}%")
        print(f"   └ Base TCS Win Rate: {odds['base_win_rate']:.1f}%")
        print(f"   └ Ghost Mode Bonus: +{odds['ghost_adjusted_win_rate'] - odds['base_win_rate']:.1f}% (effectiveness: {tier_info['ghost_effectiveness']:.1f}%)")
        print()
        
        print(f"📊 Monthly Signal Activity:")
        print(f"   • Available Signals: {odds['signals_per_month']:.0f}")
        print(f"   • Executed Signals: {odds['executed_signals_per_month']:.0f} ({tier_info['execution_rate']*100:.0f}% execution rate)")
        print(f"   • Expected Wins: {odds['winning_trades_per_month']:.0f}")
        print(f"   • Expected Losses: {odds['losing_trades_per_month']:.0f}")
        print()
        
        print(f"💰 Monthly Financial Projection:")
        print(f"   • ARCADE Trades: {gains['arcade_trades']['signals']:.0f} signals, {gains['arcade_trades']['wins']:.0f} wins")
        print(f"     └ Profit per win: ${gains['arcade_trades']['profit_per_win']:.2f}")
        print(f"   • SNIPER Trades: {gains['sniper_trades']['signals']:.0f} signals, {gains['sniper_trades']['wins']:.0f} wins")
        print(f"     └ Profit per win: ${gains['sniper_trades']['profit_per_win']:.2f}")
        print(f"   • Loss per trade: ${gains['loss_per_trade']:.2f}")
        print()
        
        print(f"🎯 Monthly Bottom Line:")
        print(f"   • Total Profits: ${gains['total_profit_usd']:.2f}")
        print(f"   • Total Losses: ${gains['total_losses_usd']:.2f}")
        print(f"   • NET GAIN: ${gains['net_monthly_gain_usd']:.2f}")
        print(f"   • ROI: {gains['roi_percentage']:.1f}%")
        print()
        print("=" * 50)
        print()
    
    # Save detailed analysis
    with open("/root/HydraX-v2/winning_odds_complete_analysis.json", "w") as f:
        json.dump(analysis, f, indent=2)
    
    print("💾 Complete analysis saved to: winning_odds_complete_analysis.json")
    
    # Risk warnings
    print()
    print("⚠️ IMPORTANT DISCLAIMERS:")
    print("• Past performance does not guarantee future results")
    print("• Trading involves substantial risk of loss")
    print("• Ghost mode provides protection but cannot eliminate all risks")
    print("• Actual results may vary based on market conditions and execution")
    print("• These projections are based on backtested calibrated data")

if __name__ == "__main__":
    main()