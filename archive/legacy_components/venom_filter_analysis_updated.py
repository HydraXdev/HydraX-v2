#!/usr/bin/env python3
"""
VENOM v7.0 - UPDATED FILTER ANALYSIS 
Updated analysis based on live 6-week test results showing 7% boost with filtering
"""

import json
import random
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

def analyze_filter_effectiveness_updated():
    """
    Updated analysis considering the new live test data:
    - Filter provides 7% win rate boost in live conditions
    - Filter cuts signals by 70%
    - Need to determine if boost justifies signal reduction
    """
    
    print("🔍 VENOM FILTER ANALYSIS - UPDATED WITH LIVE TEST DATA")
    print("=" * 80)
    print("📊 NEW FINDINGS:")
    print("   🎯 Live tests show FILTER BOOSTS win rate by 7%")
    print("   🚫 Filter cuts signal volume by 70%")
    print("   ❓ Does 7% boost justify 70% signal reduction?")
    print("=" * 80)
    
    # Current backtest results (from previous analysis)
    current_results = {
        'unfiltered': {
            'signals_per_day': 25.0,
            'win_rate': 78.3,  # From previous backtest
            'daily_profit_potential': 100.0  # Base reference
        },
        'filtered': {
            'signals_per_day': 7.5,  # 30% of original (70% cut)
            'win_rate': 76.3,  # From previous backtest
            'daily_profit_potential': 30.0  # Proportional to volume
        }
    }
    
    # Updated results based on live 6-week test
    live_test_results = {
        'unfiltered': {
            'signals_per_day': 25.0,
            'win_rate': 78.3,
            'daily_profit_potential': 100.0  # Base reference
        },
        'filtered': {
            'signals_per_day': 7.5,  # 30% of original (70% cut) 
            'win_rate': 85.3,  # 78.3% + 7% boost = 85.3%
            'daily_profit_potential': 32.1  # Adjusted for higher win rate
        }
    }
    
    print("\n📊 CURRENT BACKTEST RESULTS:")
    print("=" * 80)
    print(f"🔄 UNFILTERED: {current_results['unfiltered']['signals_per_day']} signals/day @ {current_results['unfiltered']['win_rate']}% = 100% profit baseline")
    print(f"🛡️ FILTERED: {current_results['filtered']['signals_per_day']} signals/day @ {current_results['filtered']['win_rate']}% = {current_results['filtered']['daily_profit_potential']}% of baseline profit")
    
    print("\n🆕 UPDATED LIVE TEST RESULTS (Last 6 Weeks):")
    print("=" * 80)
    print(f"🔄 UNFILTERED: {live_test_results['unfiltered']['signals_per_day']} signals/day @ {live_test_results['unfiltered']['win_rate']}% = 100% profit baseline")
    print(f"🛡️ FILTERED: {live_test_results['filtered']['signals_per_day']} signals/day @ {live_test_results['filtered']['win_rate']}% = {live_test_results['filtered']['daily_profit_potential']}% of baseline profit")
    
    # Calculate detailed impact analysis
    return analyze_filter_trade_offs(current_results, live_test_results)

def analyze_filter_trade_offs(backtest_results, live_results):
    """Analyze the trade-offs between volume reduction and win rate improvement"""
    
    print("\n🔬 DETAILED FILTER TRADE-OFF ANALYSIS:")
    print("=" * 80)
    
    # Backtest scenario
    bt_unfiltered = backtest_results['unfiltered']
    bt_filtered = backtest_results['filtered']
    
    # Live test scenario
    live_unfiltered = live_results['unfiltered']
    live_filtered = live_results['filtered']
    
    # Calculate profit factors (simplified)
    # Profit Factor = (Win Rate * Avg Win) / (Loss Rate * Avg Loss)
    # Assuming 1:2 R:R for RAPID and 1:3 R:R for PRECISION, weighted average ~1:2.4
    avg_rr_ratio = 2.4
    
    def calculate_profit_factor(win_rate, rr_ratio):
        loss_rate = 100 - win_rate
        return (win_rate * rr_ratio) / (loss_rate * 1.0) if loss_rate > 0 else float('inf')
    
    def calculate_daily_profit_score(signals_per_day, win_rate, rr_ratio):
        """Calculate daily profit score combining volume and performance"""
        profit_factor = calculate_profit_factor(win_rate, rr_ratio)
        expectancy = (win_rate/100 * rr_ratio) - ((100-win_rate)/100 * 1.0)
        return signals_per_day * expectancy * 10  # Scale for readability
    
    # Calculate scores
    bt_unfiltered_score = calculate_daily_profit_score(
        bt_unfiltered['signals_per_day'], 
        bt_unfiltered['win_rate'], 
        avg_rr_ratio
    )
    
    bt_filtered_score = calculate_daily_profit_score(
        bt_filtered['signals_per_day'], 
        bt_filtered['win_rate'], 
        avg_rr_ratio
    )
    
    live_unfiltered_score = calculate_daily_profit_score(
        live_unfiltered['signals_per_day'], 
        live_unfiltered['win_rate'], 
        avg_rr_ratio
    )
    
    live_filtered_score = calculate_daily_profit_score(
        live_filtered['signals_per_day'], 
        live_filtered['win_rate'], 
        avg_rr_ratio
    )
    
    print(f"\n📈 PROFIT SCORING ANALYSIS:")
    print("=" * 80)
    print(f"BACKTEST SCENARIO:")
    print(f"  🔄 Unfiltered Score: {bt_unfiltered_score:.1f}")
    print(f"  🛡️ Filtered Score: {bt_filtered_score:.1f}")
    print(f"  📊 Filter Impact: {((bt_filtered_score/bt_unfiltered_score - 1) * 100):+.1f}%")
    
    print(f"\nLIVE TEST SCENARIO:")
    print(f"  🔄 Unfiltered Score: {live_unfiltered_score:.1f}")
    print(f"  🛡️ Filtered Score: {live_filtered_score:.1f}")
    print(f"  📊 Filter Impact: {((live_filtered_score/live_unfiltered_score - 1) * 100):+.1f}%")
    
    # Decision analysis
    print(f"\n🎯 FILTER DECISION ANALYSIS:")
    print("=" * 80)
    
    backtest_filter_worse = bt_filtered_score < bt_unfiltered_score
    live_filter_better = live_filtered_score > live_unfiltered_score
    
    if backtest_filter_worse and live_filter_better:
        print("🔄 CONFLICTING RESULTS:")
        print(f"  📊 Backtest: Filter reduces performance by {((1 - bt_filtered_score/bt_unfiltered_score) * 100):.1f}%")
        print(f"  🔴 Live Test: Filter improves performance by {((live_filtered_score/live_unfiltered_score - 1) * 100):.1f}%")
        print("\n🎯 RECOMMENDATION: TRUST LIVE DATA")
        print("✅ USE FILTER - Live market conditions show clear benefit")
        
        # Calculate the break-even analysis
        win_rate_needed = calculate_breakeven_win_rate(live_unfiltered['signals_per_day'], live_filtered['signals_per_day'], live_unfiltered['win_rate'], avg_rr_ratio)
        print(f"\n📊 BREAK-EVEN ANALYSIS:")
        print(f"  📈 Win rate needed to justify 70% signal cut: {win_rate_needed:.1f}%")
        print(f"  🎯 Actual filtered win rate: {live_filtered['win_rate']}%")
        print(f"  ✅ Margin above break-even: {(live_filtered['win_rate'] - win_rate_needed):+.1f}%")
        
        verdict = "FILTER JUSTIFIED"
        confidence = "HIGH"
        
    elif live_filter_better:
        print("✅ FILTER BENEFICIAL:")
        print(f"  📊 Live Test: Filter improves performance by {((live_filtered_score/live_unfiltered_score - 1) * 100):.1f}%")
        verdict = "USE FILTER"
        confidence = "HIGH"
        
    else:
        print("❌ FILTER DETRIMENTAL:")
        print(f"  📊 Filter reduces performance")
        verdict = "AVOID FILTER"
        confidence = "MEDIUM"
    
    # Volume vs Quality trade-off analysis
    print(f"\n⚖️ VOLUME vs QUALITY TRADE-OFF:")
    print("=" * 80)
    volume_reduction = (1 - live_filtered['signals_per_day'] / live_unfiltered['signals_per_day']) * 100
    quality_improvement = live_filtered['win_rate'] - live_unfiltered['win_rate']
    
    print(f"📉 Volume Reduction: {volume_reduction:.1f}%")
    print(f"📈 Quality Improvement: {quality_improvement:+.1f}%")
    print(f"🎯 Trade-off Ratio: {quality_improvement/volume_reduction*100:.2f}% quality per % volume lost")
    
    # Final recommendation
    print(f"\n🎯 FINAL RECOMMENDATION:")
    print("=" * 80)
    print(f"VERDICT: {verdict}")
    print(f"CONFIDENCE: {confidence}")
    
    if verdict == "FILTER JUSTIFIED" or verdict == "USE FILTER":
        print(f"\n✅ IMPLEMENT FILTER:")
        print(f"  🎯 Expected win rate: {live_filtered['win_rate']}%")
        print(f"  📊 Expected signals: {live_filtered['signals_per_day']}/day")
        print(f"  💰 Expected profit improvement: {((live_filtered_score/live_unfiltered_score - 1) * 100):+.1f}%")
        print(f"  🛡️ Risk reduction: Fewer but higher quality signals")
    else:
        print(f"\n❌ AVOID FILTER:")
        print(f"  🎯 Keep unfiltered approach")
        print(f"  📊 Maintain {live_unfiltered['signals_per_day']} signals/day")
        print(f"  💰 Maximize volume for compound growth")
    
    return {
        'verdict': verdict,
        'confidence': confidence,
        'filter_impact_live': ((live_filtered_score/live_unfiltered_score - 1) * 100),
        'filter_impact_backtest': ((bt_filtered_score/bt_unfiltered_score - 1) * 100),
        'volume_reduction': volume_reduction,
        'quality_improvement': quality_improvement,
        'live_filtered_score': live_filtered_score,
        'live_unfiltered_score': live_unfiltered_score
    }

def calculate_breakeven_win_rate(unfiltered_signals_per_day, filtered_signals_per_day, unfiltered_win_rate, rr_ratio):
    """Calculate the win rate needed for filtered approach to match unfiltered performance"""
    
    # Unfiltered expectancy per signal
    unfiltered_expectancy = (unfiltered_win_rate/100 * rr_ratio) - ((100-unfiltered_win_rate)/100 * 1.0)
    unfiltered_daily_expectancy = unfiltered_signals_per_day * unfiltered_expectancy
    
    # For filtered to match: filtered_signals_per_day * filtered_expectancy = unfiltered_daily_expectancy
    required_filtered_expectancy = unfiltered_daily_expectancy / filtered_signals_per_day
    
    # Solve for win rate: (wr/100 * rr_ratio) - ((100-wr)/100 * 1.0) = required_expectancy
    # wr * rr_ratio/100 - (100-wr)/100 = required_expectancy
    # wr * rr_ratio/100 - 1 + wr/100 = required_expectancy
    # wr * (rr_ratio + 1)/100 = required_expectancy + 1
    # wr = (required_expectancy + 1) * 100 / (rr_ratio + 1)
    
    required_win_rate = (required_filtered_expectancy + 1) * 100 / (rr_ratio + 1)
    return required_win_rate

def main():
    """Run the updated filter analysis"""
    results = analyze_filter_effectiveness_updated()
    
    # Save updated results
    with open('/root/HydraX-v2/venom_filter_analysis_updated_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Updated analysis saved to: venom_filter_analysis_updated_results.json")
    print(f"🎯 ANALYSIS COMPLETE!")

if __name__ == "__main__":
    main()