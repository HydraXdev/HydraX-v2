#!/usr/bin/env python3
"""
Monthly Performance Calculator for Constrained User
Calculates expected monthly gains for a user with specific limitations
"""

import json
import math
from datetime import datetime, timedelta
from typing import Dict, List

class UserMonthlyPerformance:
    """Calculate monthly performance for constrained user profile"""
    
    def __init__(self):
        # User constraints
        self.max_risk_percent = 2.0  # 2% risk per trade
        self.max_concurrent_trades = 1  # Only 1 trade open at a time
        self.max_trades_per_day = 6  # Max 6 trades per day
        self.trading_days_per_month = 22  # M-F only (4.4 weeks * 5 days)
        
        # system performance (from our analysis)
        self.system_win_rate = 0.56  # 56% win rate
        self.system_expectancy = 0.853  # Average R per trade
        
        # R:R distribution from (from our analysis)
        self.rr_distribution = {
            '1:1.5-1:2': {'probability': 0.34, 'avg_rr': 1.75, 'expectancy': 0.540},
            '1:2-1:2.5': {'probability': 0.34, 'avg_rr': 2.24, 'expectancy': 0.809},
            '1:2.5-1:3': {'probability': 0.17, 'avg_rr': 2.72, 'expectancy': 1.077},
            '1:3+': {'probability': 0.15, 'avg_rr': 3.25, 'expectancy': 1.387}
        }
        
        # Signal availability (from our analysis)
        self.signals_per_day = 76  # generates 76 signals/day
        self.high_quality_signals_per_day = 45  # Assuming 60% are 75+ TCS
        
    def calculate_trade_outcome(self, risk_percent: float, rr_ratio: float, outcome: str) -> float:
        """Calculate the percentage gain/loss for a single trade"""
        
        if outcome == "WIN":
            return risk_percent * rr_ratio  # Gain = risk * R:R ratio
        else:
            return -risk_percent  # Loss = -risk
    
    def simulate_daily_trading(self) -> Dict:
        """Simulate one day of trading with user constraints"""
        
        import random
        
        # Available signals per day (user limited to 6 max)
        available_signals = min(self.max_trades_per_day, self.high_quality_signals_per_day)
        
        daily_results = {
            'trades_taken': 0,
            'trades_won': 0,
            'trades_lost': 0,
            'daily_gain_percent': 0.0,
            'trade_details': []
        }
        
        # Since user can only have 1 trade open at a time, they'll take trades sequentially
        # Assume average trade duration is 6-12 hours, so realistically 1-2 trades per day max
        realistic_trades_per_day = min(2, self.max_trades_per_day)
        
        for trade_num in range(realistic_trades_per_day):
            # Select R:R ratio based on distribution
            rr_category = random.choices(
                list(self.rr_distribution.keys()),
                weights=[data['probability'] for data in self.rr_distribution.values()]
            )[0]
            
            rr_data = self.rr_distribution[rr_category]
            rr_ratio = rr_data['avg_rr']
            
            # Determine win/loss (56% win rate)
            outcome = "WIN" if random.random() < self.system_win_rate else "LOSS"
            
            # Calculate trade result
            trade_gain = self.calculate_trade_outcome(self.max_risk_percent, rr_ratio, outcome)
            
            daily_results['trades_taken'] += 1
            daily_results['daily_gain_percent'] += trade_gain
            
            if outcome == "WIN":
                daily_results['trades_won'] += 1
            else:
                daily_results['trades_lost'] += 1
            
            daily_results['trade_details'].append({
                'trade_num': trade_num + 1,
                'rr_category': rr_category,
                'rr_ratio': rr_ratio,
                'outcome': outcome,
                'gain_percent': trade_gain
            })
        
        return daily_results
    
    def simulate_monthly_performance(self, num_simulations: int = 1000) -> Dict:
        """Simulate monthly performance over multiple scenarios"""
        
        monthly_results = []
        
        for sim in range(num_simulations):
            monthly_gain = 0.0
            total_trades = 0
            total_wins = 0
            
            # Simulate each trading day in the month
            for day in range(self.trading_days_per_month):
                daily_result = self.simulate_daily_trading()
                
                # Compound the gains (percentage-based)
                daily_gain_decimal = daily_result['daily_gain_percent'] / 100
                monthly_gain = (1 + monthly_gain) * (1 + daily_gain_decimal) - 1
                
                total_trades += daily_result['trades_taken']
                total_wins += daily_result['trades_won']
            
            monthly_results.append({
                'monthly_gain_percent': monthly_gain * 100,
                'total_trades': total_trades,
                'total_wins': total_wins,
                'win_rate': (total_wins / total_trades) * 100 if total_trades > 0 else 0
            })
        
        return monthly_results
    
    def calculate_theoretical_performance(self) -> Dict:
        """Calculate theoretical performance using mathematical expectation"""
        
        # Realistic trades per day (limited by 1 concurrent trade)
        trades_per_day = 2  # Conservative estimate
        total_trades_per_month = trades_per_day * self.trading_days_per_month
        
        # Calculate expected R per trade using distribution
        expected_r_per_trade = sum(
            data['probability'] * data['expectancy'] 
            for data in self.rr_distribution.values()
        )
        
        # Expected gain per trade in percentage terms
        expected_gain_per_trade = self.max_risk_percent * expected_r_per_trade
        
        # Monthly performance (simple addition - conservative)
        simple_monthly_gain = expected_gain_per_trade * total_trades_per_month
        
        # Monthly performance (compounded - realistic)
        compounded_monthly_gain = 1.0
        for _ in range(total_trades_per_month):
            compounded_monthly_gain *= (1 + expected_gain_per_trade / 100)
        compounded_monthly_gain = (compounded_monthly_gain - 1) * 100
        
        return {
            'trades_per_day': trades_per_day,
            'total_trades_per_month': total_trades_per_month,
            'expected_r_per_trade': round(expected_r_per_trade, 3),
            'expected_gain_per_trade_percent': round(expected_gain_per_trade, 3),
            'simple_monthly_gain_percent': round(simple_monthly_gain, 2),
            'compounded_monthly_gain_percent': round(compounded_monthly_gain, 2)
        }
    
    def run_comprehensive_analysis(self) -> Dict:
        """Run comprehensive monthly performance analysis"""
        
        print("💰 Monthly Performance Analysis")
        print("🎯 User Profile: 2% risk, 1 concurrent trade, 6 trades/day max")
        print("=" * 60)
        
        # Theoretical calculation
        theoretical = self.calculate_theoretical_performance()
        
        # Monte Carlo simulation
        print("📊 Running 1,000 month simulations...")
        simulations = self.simulate_monthly_performance(1000)
        
        # Analyze simulation results
        monthly_gains = [sim['monthly_gain_percent'] for sim in simulations]
        avg_monthly_gain = sum(monthly_gains) / len(monthly_gains)
        
        # Percentiles
        monthly_gains.sort()
        p10 = monthly_gains[int(len(monthly_gains) * 0.1)]
        p25 = monthly_gains[int(len(monthly_gains) * 0.25)]
        p50 = monthly_gains[int(len(monthly_gains) * 0.5)]  # Median
        p75 = monthly_gains[int(len(monthly_gains) * 0.75)]
        p90 = monthly_gains[int(len(monthly_gains) * 0.9)]
        
        # Winning months
        positive_months = [g for g in monthly_gains if g > 0]
        winning_month_rate = (len(positive_months) / len(monthly_gains)) * 100
        
        # Annual projection
        avg_annual_gain = ((1 + avg_monthly_gain / 100) ** 12 - 1) * 100
        
        return {
            'user_constraints': {
                'max_risk_per_trade': f"{self.max_risk_percent}%",
                'max_concurrent_trades': self.max_concurrent_trades,
                'max_trades_per_day': self.max_trades_per_day,
                'trading_days_per_month': self.trading_days_per_month
            },
            'theoretical_performance': theoretical,
            'simulation_results': {
                'simulations_run': len(simulations),
                'average_monthly_gain_percent': round(avg_monthly_gain, 2),
                'median_monthly_gain_percent': round(p50, 2),
                'percentile_10': round(p10, 2),
                'percentile_25': round(p25, 2),
                'percentile_75': round(p75, 2),
                'percentile_90': round(p90, 2),
                'winning_months_rate': round(winning_month_rate, 1),
                'projected_annual_gain_percent': round(avg_annual_gain, 1)
            },
            'risk_analysis': {
                'best_month_percent': round(max(monthly_gains), 2),
                'worst_month_percent': round(min(monthly_gains), 2),
                'months_with_loss': len([g for g in monthly_gains if g < 0]),
                'largest_loss_percent': round(min(monthly_gains), 2)
            }
        }

def main():
    """Main execution function"""
    
    calculator = UserMonthlyPerformance()
    results = calculator.run_comprehensive_analysis()
    
    # Save results
    output_file = '/root/HydraX-v2/user_monthly_performance_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print results
    print("✅ Analysis Complete!")
    print("\n" + "="*60)
    print("💰 MONTHLY PERFORMANCE EXPECTATIONS")
    print("="*60)
    
    constraints = results['user_constraints']
    theoretical = results['theoretical_performance']
    simulation = results['simulation_results']
    risk = results['risk_analysis']
    
    print(f"\n👤 USER PROFILE:")
    print(f"  Risk per Trade: {constraints['max_risk_per_trade']}")
    print(f"  Concurrent Trades: {constraints['max_concurrent_trades']}")
    print(f"  Max Trades/Day: {constraints['max_trades_per_day']}")
    print(f"  Trading Days/Month: {constraints['trading_days_per_month']} (M-F only)")
    
    print(f"\n📈 THEORETICAL PERFORMANCE:")
    print(f"  Realistic Trades/Day: {theoretical['trades_per_day']}")
    print(f"  Total Trades/Month: {theoretical['total_trades_per_month']}")
    print(f"  Expected R per Trade: {theoretical['expected_r_per_trade']}")
    print(f"  Expected Gain per Trade: {theoretical['expected_gain_per_trade_percent']}%")
    print(f"  Monthly Gain (Simple): {theoretical['simple_monthly_gain_percent']}%")
    print(f"  Monthly Gain (Compounded): {theoretical['compounded_monthly_gain_percent']}%")
    
    print(f"\n🎲 SIMULATION RESULTS (1,000 months):")
    print(f"  Average Monthly Gain: {simulation['average_monthly_gain_percent']}%")
    print(f"  Median Monthly Gain: {simulation['median_monthly_gain_percent']}%")
    print(f"  25th Percentile: {simulation['percentile_25']}%")
    print(f"  75th Percentile: {simulation['percentile_75']}%")
    print(f"  Winning Months: {simulation['winning_months_rate']}%")
    print(f"  Projected Annual Return: {simulation['projected_annual_gain_percent']}%")
    
    print(f"\n⚠️  RISK ANALYSIS:")
    print(f"  Best Month: +{risk['best_month_percent']}%")
    print(f"  Worst Month: {risk['worst_month_percent']}%")
    print(f"  Losing Months: {risk['months_with_loss']}/1000 simulations")
    
    print(f"\n🎯 BOTTOM LINE:")
    if simulation['average_monthly_gain_percent'] > 0:
        print(f"  Expected Monthly Return: {simulation['average_monthly_gain_percent']}%")
        print(f"  Expected Annual Return: {simulation['projected_annual_gain_percent']}%")
        print(f"  Probability of Profitable Month: {simulation['winning_months_rate']}%")
        print("  ✅ PROFITABLE EXPECTATION")
    else:
        print("  ❌ NEGATIVE EXPECTATION")
    
    print(f"\n💾 Detailed results saved to: {output_file}")

if __name__ == "__main__":
    main()