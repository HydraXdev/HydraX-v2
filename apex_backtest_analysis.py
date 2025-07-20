#!/usr/bin/env python3
"""
APEX Engine Backtest Analysis
Analyzes historical signals with TCS > 70 and calculates success rates
"""

import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import statistics

class APEXBacktestAnalyzer:
    """Comprehensive backtest analysis for APEX signals with TCS > 70"""
    
    def __init__(self):
        self.base_path = Path('/root/HydraX-v2')
        self.major_pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']
        self.tcs_threshold = 70
        
        # Analysis results storage
        self.signals_data = []
        self.trades_data = []
        self.backtest_results = {}
        
    def load_historical_data(self) -> Dict:
        """Load all historical trading data"""
        
        # Load fired trades
        fired_trades_file = self.base_path / 'fired_trades.json'
        uuid_tracking_file = self.base_path / 'data' / 'uuid_trade_tracking.json'
        
        fired_trades = []
        signal_tracking = {}
        
        try:
            if fired_trades_file.exists():
                with open(fired_trades_file, 'r') as f:
                    fired_trades = json.load(f)
                    
            if uuid_tracking_file.exists():
                with open(uuid_tracking_file, 'r') as f:
                    tracking_data = json.load(f)
                    signal_tracking = tracking_data.get('signals', {})
                    
        except Exception as e:
            print(f"Error loading historical data: {e}")
            
        return {
            'fired_trades': fired_trades,
            'signal_tracking': signal_tracking
        }
    
    def extract_70plus_tcs_signals(self, data: Dict) -> List[Dict]:
        """Extract signals with TCS score > 70 for major pairs"""
        
        filtered_signals = []
        
        # Process fired trades
        for trade in data['fired_trades']:
            if (trade.get('symbol') in self.major_pairs and 
                trade.get('tcs_score', 0) > self.tcs_threshold):
                
                filtered_signals.append({
                    'source': 'fired_trades',
                    'mission_id': trade.get('mission_id'),
                    'symbol': trade.get('symbol'),
                    'direction': trade.get('direction'),
                    'tcs_score': trade.get('tcs_score'),
                    'signal_type': trade.get('signal_type'),
                    'entry_price': trade.get('entry_price'),
                    'stop_loss': trade.get('stop_loss'),
                    'take_profit': trade.get('take_profit'),
                    'risk_reward_ratio': trade.get('risk_reward_ratio'),
                    'execution_success': trade.get('execution_result', {}).get('success', False),
                    'execution_message': trade.get('execution_result', {}).get('message', ''),
                    'ticket': trade.get('execution_result', {}).get('ticket'),
                    'fired_at': trade.get('fired_at'),
                    'user_tier': trade.get('user_tier', 'UNKNOWN')
                })
        
        # Process signal tracking data
        for signal_id, signal_data in data['signal_tracking'].items():
            signal_info = signal_data.get('signal_data', {})
            
            if (signal_info.get('symbol') in self.major_pairs and 
                signal_info.get('tcs_score', 0) > self.tcs_threshold):
                
                filtered_signals.append({
                    'source': 'signal_tracking',
                    'signal_uuid': signal_id,
                    'symbol': signal_info.get('symbol'),
                    'direction': signal_info.get('direction'),
                    'tcs_score': signal_info.get('tcs_score'),
                    'signal_type': signal_info.get('signal_type'),
                    'entry_price': signal_info.get('entry_price'),
                    'timestamp': signal_info.get('timestamp'),
                    'user_id': signal_info.get('user_id')
                })
        
        return filtered_signals
    
    def calculate_tcs_distribution(self, signals: List[Dict]) -> Dict:
        """Calculate TCS score distribution analysis"""
        
        tcs_scores = [s['tcs_score'] for s in signals if s.get('tcs_score')]
        
        if not tcs_scores:
            return {}
        
        # TCS ranges analysis
        ranges = {
            '70-75': [s for s in tcs_scores if 70 <= s < 75],
            '75-80': [s for s in tcs_scores if 75 <= s < 80],
            '80-85': [s for s in tcs_scores if 80 <= s < 85],
            '85-90': [s for s in tcs_scores if 85 <= s < 90],
            '90-95': [s for s in tcs_scores if 90 <= s < 95],
            '95+': [s for s in tcs_scores if s >= 95]
        }
        
        return {
            'total_signals': len(tcs_scores),
            'avg_tcs': statistics.mean(tcs_scores),
            'median_tcs': statistics.median(tcs_scores),
            'min_tcs': min(tcs_scores),
            'max_tcs': max(tcs_scores),
            'std_dev': statistics.stdev(tcs_scores) if len(tcs_scores) > 1 else 0,
            'range_distribution': {
                range_name: {
                    'count': len(range_scores),
                    'percentage': (len(range_scores) / len(tcs_scores)) * 100,
                    'avg_tcs': statistics.mean(range_scores) if range_scores else 0
                }
                for range_name, range_scores in ranges.items()
            }
        }
    
    def analyze_execution_success_rate(self, signals: List[Dict]) -> Dict:
        """Analyze execution success rates by TCS score ranges"""
        
        # Filter signals that have execution data
        executed_signals = [s for s in signals if 'execution_success' in s]
        
        if not executed_signals:
            return {'error': 'No execution data available'}
        
        # Group by TCS ranges
        ranges = {
            '70-75': [s for s in executed_signals if 70 <= s.get('tcs_score', 0) < 75],
            '75-80': [s for s in executed_signals if 75 <= s.get('tcs_score', 0) < 80],
            '80-85': [s for s in executed_signals if 80 <= s.get('tcs_score', 0) < 85],
            '85-90': [s for s in executed_signals if 85 <= s.get('tcs_score', 0) < 90],
            '90+': [s for s in executed_signals if s.get('tcs_score', 0) >= 90]
        }
        
        success_analysis = {}
        
        for range_name, range_signals in ranges.items():
            if range_signals:
                successful = [s for s in range_signals if s.get('execution_success', False)]
                success_rate = (len(successful) / len(range_signals)) * 100
                
                success_analysis[range_name] = {
                    'total_signals': len(range_signals),
                    'successful_executions': len(successful),
                    'failed_executions': len(range_signals) - len(successful),
                    'success_rate_percent': round(success_rate, 2),
                    'avg_tcs': statistics.mean([s['tcs_score'] for s in range_signals])
                }
        
        # Overall success rate
        total_successful = sum([s.get('execution_success', False) for s in executed_signals])
        overall_success_rate = (total_successful / len(executed_signals)) * 100
        
        success_analysis['overall'] = {
            'total_signals': len(executed_signals),
            'successful_executions': total_successful,
            'failed_executions': len(executed_signals) - total_successful,
            'success_rate_percent': round(overall_success_rate, 2)
        }
        
        return success_analysis
    
    def analyze_by_trading_pairs(self, signals: List[Dict]) -> Dict:
        """Analyze signals by major trading pairs"""
        
        pair_analysis = {}
        
        for pair in self.major_pairs:
            pair_signals = [s for s in signals if s.get('symbol') == pair]
            
            if pair_signals:
                # TCS analysis for this pair
                tcs_scores = [s['tcs_score'] for s in pair_signals if s.get('tcs_score')]
                
                # Execution analysis for this pair  
                executed = [s for s in pair_signals if 'execution_success' in s]
                successful = [s for s in executed if s.get('execution_success', False)]
                
                pair_analysis[pair] = {
                    'total_signals': len(pair_signals),
                    'avg_tcs': statistics.mean(tcs_scores) if tcs_scores else 0,
                    'max_tcs': max(tcs_scores) if tcs_scores else 0,
                    'min_tcs': min(tcs_scores) if tcs_scores else 0,
                    'executed_signals': len(executed),
                    'successful_executions': len(successful),
                    'execution_success_rate': (len(successful) / len(executed) * 100) if executed else 0,
                    'signal_types': {
                        signal_type: len([s for s in pair_signals if s.get('signal_type') == signal_type])
                        for signal_type in set([s.get('signal_type') for s in pair_signals if s.get('signal_type')])
                    }
                }
        
        return pair_analysis
    
    def simulate_trade_outcomes(self, signals: List[Dict]) -> Dict:
        """Simulate trade outcomes based on historical data"""
        
        # This would require actual price data to calculate P&L
        # For now, we'll analyze the structure and provide framework
        
        simulation_results = {
            'methodology': 'Based on Risk/Reward ratios and execution success',
            'assumptions': [
                'Successful executions hit take profit targets',
                'Failed executions result in stop loss hits',
                'No slippage or spread costs included'
            ],
            'signals_analyzed': len(signals),
            'executeable_signals': len([s for s in signals if 'execution_success' in s])
        }
        
        # Calculate theoretical performance based on R:R ratios
        executed_signals = [s for s in signals if 'execution_success' in s and s.get('risk_reward_ratio')]
        
        if executed_signals:
            successful = [s for s in executed_signals if s.get('execution_success', False)]
            
            # Assume winning trades achieve full R:R and losing trades lose 1R
            total_r = 0
            for signal in executed_signals:
                if signal.get('execution_success', False):
                    total_r += signal.get('risk_reward_ratio', 1.5)  # Win = +R:R
                else:
                    total_r -= 1  # Loss = -1R
            
            win_rate = (len(successful) / len(executed_signals)) * 100
            avg_rr = statistics.mean([s.get('risk_reward_ratio', 1.5) for s in executed_signals])
            
            simulation_results.update({
                'theoretical_performance': {
                    'total_r_multiple': round(total_r, 2),
                    'win_rate_percent': round(win_rate, 2),
                    'average_rr_ratio': round(avg_rr, 2),
                    'expectancy_per_trade': round((win_rate/100 * avg_rr) - ((100-win_rate)/100), 3)
                }
            })
        
        return simulation_results
    
    def generate_backtest_report(self) -> Dict:
        """Generate comprehensive backtest report"""
        
        print("🔍 Loading historical data...")
        historical_data = self.load_historical_data()
        
        print("📊 Extracting signals with TCS > 70...")
        filtered_signals = self.extract_70plus_tcs_signals(historical_data)
        
        print(f"✅ Found {len(filtered_signals)} signals with TCS > {self.tcs_threshold}")
        
        # Run all analyses
        tcs_distribution = self.calculate_tcs_distribution(filtered_signals)
        execution_analysis = self.analyze_execution_success_rate(filtered_signals)
        pair_analysis = self.analyze_by_trading_pairs(filtered_signals)
        simulation_results = self.simulate_trade_outcomes(filtered_signals)
        
        # Compile comprehensive report
        report = {
            'backtest_metadata': {
                'analysis_date': datetime.now().isoformat(),
                'tcs_threshold': self.tcs_threshold,
                'major_pairs_analyzed': self.major_pairs,
                'data_sources': ['fired_trades.json', 'uuid_trade_tracking.json'],
                'total_signals_found': len(filtered_signals)
            },
            'tcs_score_analysis': tcs_distribution,
            'execution_success_analysis': execution_analysis,
            'trading_pairs_analysis': pair_analysis,
            'performance_simulation': simulation_results,
            'raw_signals_sample': filtered_signals[:10]  # Sample for verification
        }
        
        return report

def main():
    """Main execution function"""
    
    print("🚀 APEX Engine Backtest Analysis")
    print("=" * 50)
    
    analyzer = APEXBacktestAnalyzer()
    
    try:
        # Generate comprehensive backtest report
        report = analyzer.generate_backtest_report()
        
        # Save report to file
        report_file = Path('/root/HydraX-v2/apex_backtest_report.json')
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Report saved to: {report_file}")
        
        # Print key findings
        print("\n🎯 KEY FINDINGS:")
        print("=" * 30)
        
        metadata = report['backtest_metadata']
        print(f"Total Signals (TCS > {metadata['tcs_threshold']}): {metadata['total_signals_found']}")
        
        if 'tcs_score_analysis' in report and report['tcs_score_analysis']:
            tcs_analysis = report['tcs_score_analysis']
            print(f"Average TCS Score: {tcs_analysis.get('avg_tcs', 0):.1f}")
            print(f"TCS Range: {tcs_analysis.get('min_tcs', 0)} - {tcs_analysis.get('max_tcs', 0)}")
        
        if 'execution_success_analysis' in report and 'overall' in report['execution_success_analysis']:
            exec_analysis = report['execution_success_analysis']['overall']
            print(f"Overall Execution Success Rate: {exec_analysis.get('success_rate_percent', 0)}%")
        
        if 'performance_simulation' in report and 'theoretical_performance' in report['performance_simulation']:
            sim_results = report['performance_simulation']['theoretical_performance']
            print(f"Theoretical Win Rate: {sim_results.get('win_rate_percent', 0)}%")
            print(f"Expectancy per Trade: {sim_results.get('expectancy_per_trade', 0):.3f}R")
        
        print("\n✅ Backtest analysis complete!")
        
        return report
        
    except Exception as e:
        print(f"❌ Error during backtest analysis: {e}")
        return None

if __name__ == "__main__":
    main()