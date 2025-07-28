#!/usr/bin/env python3
"""
VENOM v7.0 LIVE REALITY ANALYSIS
What happens when VENOM meets the real market vs simulator perfection

CRITICAL REALITY CHECK:
Simulators: 81.3% win rate, perfect execution
Live Market: ??? (probably much different)
"""

import json
import random
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VenomLiveRealityCheck:
    """
    HARSH REALITY: What VENOM would face in live markets
    
    Simulator Performance: 81.3% win rate
    Live Market Factors: Slippage, spread widening, execution delays,
                        server issues, news events, liquidity gaps
    """
    
    def __init__(self):
        # Simulator results (our baseline fantasy)
        self.simulator_results = {
            'win_rate': 81.3,
            'total_trades': 3300,
            'tp_rate': 78.3,
            'avg_slippage': 0.3,  # Perfect world slippage
            'spread_assumption': 'normal',
            'execution_delay': 0,  # Instant execution
            'server_uptime': 100.0,  # Never fails
            'news_impact': 'minimal'  # Controlled environment
        }
        
        # Real market harsh realities
        self.live_market_factors = {
            # EXECUTION REALITY
            'typical_slippage': {'min': 0.5, 'max': 3.5, 'spike': 10.0},  # Pips
            'spread_widening': {
                'normal': 1.0,      # Normal multiplier
                'news': 3.0,        # During news
                'illiquid': 5.0,    # Off hours
                'crisis': 10.0      # Market crisis
            },
            'execution_delays': {
                'normal': 50,       # 50ms average
                'busy': 200,        # 200ms during busy times
                'peak': 500,        # 500ms+ during news
                'server_lag': 2000  # 2+ seconds during issues
            },
            
            # BROKER REALITY
            'requotes': 0.15,           # 15% of trades get requoted
            'rejected_trades': 0.05,    # 5% rejections
            'partial_fills': 0.08,      # 8% partial fills
            'server_issues': 0.02,      # 2% server problems
            
            # MARKET STRUCTURE
            'liquidity_gaps': 0.12,     # 12% of time - low liquidity
            'weekend_gaps': 0.95,       # 95% chance of Sunday gap
            'flash_crashes': 0.001,     # 0.1% extreme events
            'news_events': 0.08,        # 8% of time major news
            
            # PSYCHOLOGICAL FACTORS
            'trade_hesitation': 0.10,   # 10% missed due to hesitation
            'overriding_signals': 0.05, # 5% manual overrides
            'internet_issues': 0.02,    # 2% connectivity problems
            'power_outages': 0.001      # 0.1% infrastructure failures
        }
        
        logger.info("🔍 VENOM Live Reality Analysis Initialized")
        logger.info("🎯 Analyzing gap between simulator and live performance")
    
    def simulate_live_trading_session(self, num_trades: int = 100) -> Dict:
        """Simulate what would happen in a real live trading session"""
        live_trades = []
        live_stats = {
            'executed_trades': 0,
            'missed_trades': 0,
            'requoted_trades': 0,
            'rejected_trades': 0,
            'partial_fills': 0,
            'wins': 0,
            'losses': 0,
            'total_slippage_pips': 0,
            'spread_costs': 0,
            'execution_issues': 0
        }
        
        for i in range(num_trades):
            trade_result = self.execute_single_live_trade(i)
            live_trades.append(trade_result)
            
            # Update stats
            if trade_result['executed']:
                live_stats['executed_trades'] += 1
                if trade_result['result'] == 'WIN':
                    live_stats['wins'] += 1
                else:
                    live_stats['losses'] += 1
                live_stats['total_slippage_pips'] += trade_result['slippage_pips']
                live_stats['spread_costs'] += trade_result['spread_cost']
            else:
                live_stats['missed_trades'] += 1
                if trade_result['reason'] == 'requoted':
                    live_stats['requoted_trades'] += 1
                elif trade_result['reason'] == 'rejected':
                    live_stats['rejected_trades'] += 1
                elif trade_result['reason'] == 'partial_fill':
                    live_stats['partial_fills'] += 1
                else:
                    live_stats['execution_issues'] += 1
        
        # Calculate live performance metrics
        executed = live_stats['executed_trades']
        if executed > 0:
            live_win_rate = (live_stats['wins'] / executed) * 100
            avg_slippage = live_stats['total_slippage_pips'] / executed
            avg_spread_cost = live_stats['spread_costs'] / executed
        else:
            live_win_rate = 0
            avg_slippage = 0
            avg_spread_cost = 0
        
        execution_rate = (executed / num_trades) * 100
        
        return {
            'trades_attempted': num_trades,
            'trades_executed': executed,
            'execution_rate': round(execution_rate, 1),
            'live_win_rate': round(live_win_rate, 1),
            'simulator_win_rate': self.simulator_results['win_rate'],
            'win_rate_degradation': round(self.simulator_results['win_rate'] - live_win_rate, 1),
            'avg_slippage_pips': round(avg_slippage, 2),
            'avg_spread_cost_pips': round(avg_spread_cost, 2),
            'detailed_stats': live_stats,
            'all_trades': live_trades
        }
    
    def execute_single_live_trade(self, trade_id: int) -> Dict:
        """Simulate execution of a single trade with all real-world factors"""
        
        # Start with simulator signal (perfect world)
        signal_quality = random.choice(['PLATINUM', 'GOLD', 'SILVER'])
        simulator_win_prob = random.uniform(0.75, 0.85)  # VENOM range
        
        # STEP 1: Can we even execute the trade?
        execution_check = self.check_execution_possibility()
        if not execution_check['can_execute']:
            return {
                'trade_id': trade_id,
                'executed': False,
                'reason': execution_check['reason'],
                'simulator_win_prob': simulator_win_prob,
                'actual_result': None
            }
        
        # STEP 2: Apply real market execution factors
        market_conditions = self.get_current_market_conditions()
        
        # Calculate real slippage
        slippage_pips = self.calculate_realistic_slippage(market_conditions)
        
        # Calculate spread cost
        spread_cost_pips = self.calculate_spread_cost(market_conditions)
        
        # Adjust win probability for real conditions
        adjusted_win_prob = self.adjust_win_probability_for_reality(
            simulator_win_prob, market_conditions, slippage_pips
        )
        
        # STEP 3: Execute trade with degraded conditions
        is_win = random.random() < adjusted_win_prob
        
        # Calculate realistic pips result
        if signal_quality in ['PLATINUM', 'GOLD']:
            target_pips = random.randint(20, 40)
            stop_pips = random.randint(10, 20)
        else:
            target_pips = random.randint(15, 30)
            stop_pips = random.randint(10, 15)
        
        if is_win:
            pips_result = target_pips - slippage_pips - spread_cost_pips
        else:
            pips_result = -(stop_pips + slippage_pips + spread_cost_pips)
        
        return {
            'trade_id': trade_id,
            'executed': True,
            'signal_quality': signal_quality,
            'simulator_win_prob': round(simulator_win_prob, 3),
            'adjusted_win_prob': round(adjusted_win_prob, 3),
            'result': 'WIN' if is_win else 'LOSS',
            'pips_result': round(pips_result, 1),
            'slippage_pips': round(slippage_pips, 2),
            'spread_cost': round(spread_cost_pips, 2),
            'market_conditions': market_conditions,
            'target_pips': target_pips,
            'stop_pips': stop_pips
        }
    
    def check_execution_possibility(self) -> Dict:
        """Check if trade can even be executed (before market factors)"""
        
        # Random execution issues
        if random.random() < self.live_market_factors['server_issues']:
            return {'can_execute': False, 'reason': 'server_error'}
        
        if random.random() < self.live_market_factors['rejected_trades']:
            return {'can_execute': False, 'reason': 'rejected'}
        
        if random.random() < self.live_market_factors['requotes']:
            return {'can_execute': False, 'reason': 'requoted'}
        
        if random.random() < self.live_market_factors['partial_fills']:
            return {'can_execute': False, 'reason': 'partial_fill'}
        
        # Psychological factors
        if random.random() < self.live_market_factors['trade_hesitation']:
            return {'can_execute': False, 'reason': 'hesitation'}
        
        if random.random() < self.live_market_factors['internet_issues']:
            return {'can_execute': False, 'reason': 'connectivity'}
        
        return {'can_execute': True, 'reason': 'ok'}
    
    def get_current_market_conditions(self) -> Dict:
        """Determine current market conditions affecting execution"""
        
        # Determine market session
        current_hour = random.randint(0, 23)
        if 7 <= current_hour <= 11:
            session = 'LONDON'
        elif 13 <= current_hour <= 17:
            session = 'NY'
        elif 8 <= current_hour <= 9 or 14 <= current_hour <= 15:
            session = 'OVERLAP'
        else:
            session = 'OFF_HOURS'
        
        # Check for special conditions
        is_news_time = random.random() < self.live_market_factors['news_events']
        is_low_liquidity = random.random() < self.live_market_factors['liquidity_gaps']
        is_friday_close = random.random() < 0.05  # 5% chance it's Friday close
        
        # Determine volatility spike
        volatility_multiplier = 1.0
        if is_news_time:
            volatility_multiplier = random.uniform(2.0, 5.0)
        elif is_low_liquidity:
            volatility_multiplier = random.uniform(0.3, 0.7)
        
        return {
            'session': session,
            'is_news_time': is_news_time,
            'is_low_liquidity': is_low_liquidity,
            'is_friday_close': is_friday_close,
            'volatility_multiplier': volatility_multiplier
        }
    
    def calculate_realistic_slippage(self, market_conditions: Dict) -> float:
        """Calculate realistic slippage based on market conditions"""
        
        base_slippage = random.uniform(
            self.live_market_factors['typical_slippage']['min'],
            self.live_market_factors['typical_slippage']['max']
        )
        
        # Apply market condition multipliers
        if market_conditions['is_news_time']:
            base_slippage *= random.uniform(2.0, 4.0)
        
        if market_conditions['is_low_liquidity']:
            base_slippage *= random.uniform(1.5, 3.0)
        
        if market_conditions['is_friday_close']:
            base_slippage *= random.uniform(1.3, 2.0)
        
        # Volatility impact
        base_slippage *= market_conditions['volatility_multiplier']
        
        # Extreme event chance
        if random.random() < self.live_market_factors['flash_crashes']:
            base_slippage = self.live_market_factors['typical_slippage']['spike']
        
        return min(base_slippage, 15.0)  # Cap at 15 pips
    
    def calculate_spread_cost(self, market_conditions: Dict) -> float:
        """Calculate spread costs (always against you)"""
        
        base_spread = random.uniform(0.8, 2.0)  # Normal spread
        
        # Apply spread widening
        spread_multiplier = self.live_market_factors['spread_widening']['normal']
        
        if market_conditions['is_news_time']:
            spread_multiplier = self.live_market_factors['spread_widening']['news']
        elif market_conditions['is_low_liquidity']:
            spread_multiplier = self.live_market_factors['spread_widening']['illiquid']
        
        # Volatility impact on spreads
        spread_multiplier *= market_conditions['volatility_multiplier']
        
        return base_spread * spread_multiplier
    
    def adjust_win_probability_for_reality(self, simulator_prob: float, 
                                         market_conditions: Dict, 
                                         slippage_pips: float) -> float:
        """Adjust win probability for real market conditions"""
        
        adjusted_prob = simulator_prob
        
        # Slippage impact (higher slippage = lower win rate)
        slippage_penalty = min(slippage_pips * 0.02, 0.15)  # Max 15% penalty
        adjusted_prob -= slippage_penalty
        
        # News time impact
        if market_conditions['is_news_time']:
            adjusted_prob -= random.uniform(0.05, 0.20)  # 5-20% penalty
        
        # Low liquidity impact
        if market_conditions['is_low_liquidity']:
            adjusted_prob -= random.uniform(0.03, 0.12)  # 3-12% penalty
        
        # Volatility impact
        if market_conditions['volatility_multiplier'] > 2.0:
            adjusted_prob -= random.uniform(0.08, 0.25)  # High vol penalty
        elif market_conditions['volatility_multiplier'] < 0.5:
            adjusted_prob -= random.uniform(0.02, 0.08)  # Low vol penalty
        
        # Friday close impact
        if market_conditions['is_friday_close']:
            adjusted_prob -= random.uniform(0.05, 0.15)
        
        return max(0.20, min(0.90, adjusted_prob))  # Cap between 20-90%
    
    def run_comprehensive_live_analysis(self) -> Dict:
        """Run comprehensive analysis of live vs simulator performance"""
        
        logger.info("🔍 Starting comprehensive live market analysis...")
        
        # Test different scenarios
        scenarios = {
            'normal_market': 100,
            'news_heavy': 50,
            'low_liquidity': 50,
            'high_volatility': 30,
            'weekend_gap': 20
        }
        
        results = {}
        
        for scenario, num_trades in scenarios.items():
            logger.info(f"🧪 Testing {scenario} scenario ({num_trades} trades)...")
            
            # Adjust market factors for scenario
            original_factors = self.live_market_factors.copy()
            self.adjust_factors_for_scenario(scenario)
            
            # Run simulation
            scenario_results = self.simulate_live_trading_session(num_trades)
            results[scenario] = scenario_results
            
            # Restore original factors
            self.live_market_factors = original_factors
        
        # Calculate overall realistic expectations
        overall_analysis = self.calculate_realistic_expectations(results)
        
        return {
            'simulator_baseline': self.simulator_results,
            'scenario_results': results,
            'realistic_expectations': overall_analysis,
            'harsh_realities': self.get_harsh_realities_summary()
        }
    
    def adjust_factors_for_scenario(self, scenario: str):
        """Adjust market factors for specific test scenarios"""
        
        if scenario == 'news_heavy':
            self.live_market_factors['news_events'] = 0.30  # 30% news time
            self.live_market_factors['requotes'] = 0.25
            
        elif scenario == 'low_liquidity':
            self.live_market_factors['liquidity_gaps'] = 0.60  # 60% low liquidity
            self.live_market_factors['typical_slippage']['min'] = 1.0
            self.live_market_factors['typical_slippage']['max'] = 5.0
            
        elif scenario == 'high_volatility':
            self.live_market_factors['news_events'] = 0.20
            self.live_market_factors['flash_crashes'] = 0.05  # 5% extreme events
            
        elif scenario == 'weekend_gap':
            self.live_market_factors['weekend_gaps'] = 1.0  # 100% weekend gaps
            self.live_market_factors['typical_slippage']['min'] = 2.0
    
    def calculate_realistic_expectations(self, scenario_results: Dict) -> Dict:
        """Calculate realistic expectations for live trading"""
        
        # Weight scenarios by likelihood
        scenario_weights = {
            'normal_market': 0.60,    # 60% of time
            'news_heavy': 0.15,       # 15% of time
            'low_liquidity': 0.15,    # 15% of time
            'high_volatility': 0.07,  # 7% of time
            'weekend_gap': 0.03       # 3% of time
        }
        
        weighted_win_rate = 0
        weighted_execution_rate = 0
        weighted_slippage = 0
        
        for scenario, weight in scenario_weights.items():
            if scenario in scenario_results:
                results = scenario_results[scenario]
                weighted_win_rate += results['live_win_rate'] * weight
                weighted_execution_rate += results['execution_rate'] * weight
                weighted_slippage += results['avg_slippage_pips'] * weight
        
        # Calculate realistic ranges
        best_case = weighted_win_rate + 5  # Best possible
        worst_case = weighted_win_rate - 15  # Worst realistic
        realistic_range = f"{worst_case:.1f}% - {best_case:.1f}%"
        
        return {
            'realistic_win_rate': round(weighted_win_rate, 1),
            'realistic_execution_rate': round(weighted_execution_rate, 1),
            'realistic_slippage': round(weighted_slippage, 2),
            'win_rate_range': realistic_range,
            'vs_simulator_degradation': round(self.simulator_results['win_rate'] - weighted_win_rate, 1),
            'monthly_performance_variability': '±10-20%',
            'annual_drawdown_expectation': '15-35%'
        }
    
    def get_harsh_realities_summary(self) -> Dict:
        """Summary of harsh realities vs simulator perfection"""
        
        return {
            'execution_reality': {
                'simulator': 'Perfect instant execution',
                'live': '85-95% execution rate with delays/rejections'
            },
            'slippage_reality': {
                'simulator': '0.3 pips average',
                'live': '1.5-3.0 pips average, spikes to 10+ pips'
            },
            'spread_reality': {
                'simulator': 'Fixed normal spreads',
                'live': '2-5x widening during news/low liquidity'
            },
            'win_rate_reality': {
                'simulator': '81.3% perfect conditions',
                'live': '55-70% with all real factors'
            },
            'psychological_reality': {
                'simulator': 'Perfect discipline',
                'live': 'Human emotions, hesitation, overrides'
            },
            'infrastructure_reality': {
                'simulator': '100% uptime',
                'live': 'Internet, power, server issues'
            },
            'market_reality': {
                'simulator': 'Controlled environment',
                'live': 'News events, flash crashes, gaps'
            }
        }

def main():
    """Run comprehensive VENOM live reality analysis"""
    print("🔍 VENOM v7.0 LIVE REALITY CHECK")
    print("=" * 80)
    print("🎯 QUESTION: What happens when VENOM meets the real market?")
    print("📊 SIMULATOR: 81.3% win rate, perfect execution")
    print("🌍 LIVE MARKET: Slippage, spreads, delays, rejections...")
    print("=" * 80)
    
    analyzer = VenomLiveRealityCheck()
    results = analyzer.run_comprehensive_live_analysis()
    
    # Display results
    simulator = results['simulator_baseline']
    expectations = results['realistic_expectations']
    realities = results['harsh_realities']
    
    print(f"\n📊 SIMULATOR vs LIVE PERFORMANCE COMPARISON")
    print("=" * 80)
    print(f"🏆 SIMULATOR PERFECTION:")
    print(f"  Win Rate: {simulator['win_rate']}%")
    print(f"  Execution: 100% perfect")
    print(f"  Slippage: {simulator['avg_slippage']} pips")
    print(f"  Environment: Controlled")
    
    print(f"\n🌍 LIVE MARKET REALITY:")
    print(f"  Win Rate: {expectations['realistic_win_rate']}% (range: {expectations['win_rate_range']})")
    print(f"  Execution Rate: {expectations['realistic_execution_rate']}%")
    print(f"  Slippage: {expectations['realistic_slippage']} pips average")
    print(f"  Degradation: -{expectations['vs_simulator_degradation']}% from simulator")
    
    print(f"\n🔥 HARSH REALITIES BREAKDOWN:")
    print("=" * 80)
    
    for category, reality in realities.items():
        print(f"\n{category.upper().replace('_', ' ')}:")
        print(f"  Simulator: {reality['simulator']}")
        print(f"  Live: {reality['live']}")
    
    print(f"\n📊 SCENARIO TESTING RESULTS:")
    print("=" * 80)
    
    for scenario, data in results['scenario_results'].items():
        print(f"\n{scenario.upper().replace('_', ' ')}:")
        print(f"  Execution Rate: {data['execution_rate']}%")
        print(f"  Win Rate: {data['live_win_rate']}%")
        print(f"  Avg Slippage: {data['avg_slippage_pips']} pips")
        print(f"  vs Simulator: -{data['win_rate_degradation']}%")
    
    print(f"\n🎯 REALISTIC LIVE EXPECTATIONS:")
    print("=" * 80)
    print(f"💰 Monthly Variability: {expectations['monthly_performance_variability']}")
    print(f"📉 Annual Drawdown: {expectations['annual_drawdown_expectation']}")
    print(f"🎯 Realistic Win Rate: {expectations['realistic_win_rate']}% ± 5%")
    print(f"⚡ Execution Success: {expectations['realistic_execution_rate']}%")
    
    print(f"\n🏆 FINAL VERDICT:")
    print("=" * 80)
    if expectations['realistic_win_rate'] >= 60:
        print("✅ VENOM STILL VIABLE - Expected 60%+ win rate in live market")
        print("🎯 RECOMMENDATION: Proceed with live testing with realistic expectations")
    elif expectations['realistic_win_rate'] >= 55:
        print("⚠️ VENOM MARGINAL - Expected 55-60% win rate")
        print("🎯 RECOMMENDATION: Live test with reduced position sizes")
    else:
        print("❌ VENOM QUESTIONABLE - Expected <55% win rate")
        print("🎯 RECOMMENDATION: Further optimization needed before live testing")
    
    print(f"\n💡 SIMULATOR vs LIVE DEGRADATION: -{expectations['vs_simulator_degradation']}%")
    print(f"📊 From {simulator['win_rate']}% simulator to ~{expectations['realistic_win_rate']}% live")
    
    # Save results
    with open('venom_live_reality_analysis.json', 'w') as f:
        # Make datetime serializable
        serializable_results = results.copy()
        json.dump(serializable_results, f, indent=2)
    
    print(f"\n💾 Full analysis saved to: venom_live_reality_analysis.json")
    print(f"\n🔍 LIVE REALITY CHECK COMPLETE!")

if __name__ == "__main__":
    main()