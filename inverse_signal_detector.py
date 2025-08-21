#!/usr/bin/env python3
"""
Inverse Signal Detector - Test if bad patterns work in reverse
Takes eliminated patterns and tests if inverting the direction improves performance
"""

import json
import logging
import sys
from collections import defaultdict
from typing import Dict, List, Any
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/inverse_detector.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class InverseSignalDetector:
    """Tests if poor performing patterns work better in reverse"""
    
    def __init__(self):
        self.tracking_file = "/root/HydraX-v2/comprehensive_tracking.jsonl"
        self.kill_list_file = "/root/HydraX-v2/pattern_kill_list.json"
        self.inverse_results_file = "/root/HydraX-v2/inverse_analysis_results.json"
        
    def load_kill_list(self) -> Dict:
        """Load patterns marked for elimination"""
        try:
            with open(self.kill_list_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("No kill list found - run rapid_elimination_analyzer.py first")
            return {}
        except Exception as e:
            logger.error(f"Error loading kill list: {e}")
            return {}
            
    def load_signals_for_patterns(self, patterns_to_test: List[str]) -> List[Dict]:
        """Load signals for specific patterns that need inverse testing"""
        signals = []
        try:
            with open(self.tracking_file, 'r') as f:
                for line in f:
                    if line.strip():
                        signal = json.loads(line)
                        pattern = signal.get('pattern_type', '')
                        
                        # Only load signals for patterns we want to test
                        if pattern in patterns_to_test:
                            # Only include signals with outcomes
                            if signal.get('outcome_30min') in ['TP_HIT', 'SL_HIT']:
                                signals.append(signal)
                                
        except Exception as e:
            logger.error(f"Error loading signals: {e}")
            
        logger.info(f"📊 Loaded {len(signals)} signals for inverse testing")
        return signals
        
    def calculate_inverse_outcome(self, signal: Dict) -> Dict:
        \"\"\"Calculate what the outcome would be if we inverted the signal direction\"\"\"
        original_direction = signal.get('direction', '').upper()
        original_outcome_30 = signal.get('outcome_30min')
        original_outcome_60 = signal.get('outcome_60min')
        original_pips_30 = signal.get('pips_moved_30min', 0)
        original_pips_60 = signal.get('pips_moved_60min', 0)
        
        # Invert the direction
        inverse_direction = 'SELL' if original_direction == 'BUY' else 'BUY'
        
        # Invert the outcome logic
        inverse_outcome_30 = None
        inverse_outcome_60 = None
        inverse_pips_30 = -original_pips_30 if original_pips_30 else None
        inverse_pips_60 = -original_pips_60 if original_pips_60 else None
        
        # If original was TP_HIT, inverse would be SL_HIT (and vice versa)
        # If original was SL_HIT, inverse would be TP_HIT
        if original_outcome_30 == 'TP_HIT':
            inverse_outcome_30 = 'SL_HIT'
        elif original_outcome_30 == 'SL_HIT':
            inverse_outcome_30 = 'TP_HIT'
        else:
            inverse_outcome_30 = original_outcome_30  # PENDING stays PENDING
            
        if original_outcome_60 == 'TP_HIT':
            inverse_outcome_60 = 'SL_HIT'
        elif original_outcome_60 == 'SL_HIT':
            inverse_outcome_60 = 'TP_HIT'
        else:
            inverse_outcome_60 = original_outcome_60
            
        return {
            'original_direction': original_direction,
            'inverse_direction': inverse_direction,
            'original_outcome_30': original_outcome_30,
            'inverse_outcome_30': inverse_outcome_30,
            'original_outcome_60': original_outcome_60,
            'inverse_outcome_60': inverse_outcome_60,
            'original_pips_30': original_pips_30,
            'inverse_pips_30': inverse_pips_30,
            'original_pips_60': original_pips_60,
            'inverse_pips_60': inverse_pips_60
        }
        
    def analyze_pattern_inverse_performance(self, signals: List[Dict], pattern: str) -> Dict:
        \"\"\"Analyze how a pattern would perform if inverted\"\"\"
        pattern_signals = [s for s in signals if s.get('pattern_type') == pattern]
        
        if not pattern_signals:
            return {}
            
        original_stats = {
            'total': len(pattern_signals),
            'tp_30min': 0, 'sl_30min': 0,
            'tp_60min': 0, 'sl_60min': 0,
            'total_pips_30': 0, 'total_pips_60': 0
        }
        
        inverse_stats = {
            'total': len(pattern_signals),
            'tp_30min': 0, 'sl_30min': 0,
            'tp_60min': 0, 'sl_60min': 0,
            'total_pips_30': 0, 'total_pips_60': 0
        }
        
        for signal in pattern_signals:
            inverse_data = self.calculate_inverse_outcome(signal)
            
            # Count original outcomes
            if inverse_data['original_outcome_30'] == 'TP_HIT':
                original_stats['tp_30min'] += 1
            elif inverse_data['original_outcome_30'] == 'SL_HIT':
                original_stats['sl_30min'] += 1
                
            if inverse_data['original_outcome_60'] == 'TP_HIT':
                original_stats['tp_60min'] += 1
            elif inverse_data['original_outcome_60'] == 'SL_HIT':
                original_stats['sl_60min'] += 1
                
            # Count inverse outcomes
            if inverse_data['inverse_outcome_30'] == 'TP_HIT':
                inverse_stats['tp_30min'] += 1
            elif inverse_data['inverse_outcome_30'] == 'SL_HIT':
                inverse_stats['sl_30min'] += 1
                
            if inverse_data['inverse_outcome_60'] == 'TP_HIT':
                inverse_stats['tp_60min'] += 1
            elif inverse_data['inverse_outcome_60'] == 'SL_HIT':
                inverse_stats['sl_60min'] += 1
                
            # Accumulate pips
            if inverse_data['original_pips_30'] is not None:
                original_stats['total_pips_30'] += inverse_data['original_pips_30']
            if inverse_data['inverse_pips_30'] is not None:
                inverse_stats['total_pips_30'] += inverse_data['inverse_pips_30']
                
            if inverse_data['original_pips_60'] is not None:
                original_stats['total_pips_60'] += inverse_data['original_pips_60']
            if inverse_data['inverse_pips_60'] is not None:
                inverse_stats['total_pips_60'] += inverse_data['inverse_pips_60']
                
        # Calculate win rates and pip averages
        for stats in [original_stats, inverse_stats]:
            total_closed_30 = stats['tp_30min'] + stats['sl_30min']
            if total_closed_30 > 0:
                stats['win_rate_30min'] = round(stats['tp_30min'] / total_closed_30 * 100, 1)
                stats['avg_pips_30min'] = round(stats['total_pips_30'] / total_closed_30, 1)
            else:
                stats['win_rate_30min'] = 0
                stats['avg_pips_30min'] = 0
                
            total_closed_60 = stats['tp_60min'] + stats['sl_60min']
            if total_closed_60 > 0:
                stats['win_rate_60min'] = round(stats['tp_60min'] / total_closed_60 * 100, 1)
                stats['avg_pips_60min'] = round(stats['total_pips_60'] / total_closed_60, 1)
            else:
                stats['win_rate_60min'] = 0
                stats['avg_pips_60min'] = 0
                
        # Calculate improvement
        improvement_30 = inverse_stats['win_rate_30min'] - original_stats['win_rate_30min']
        improvement_60 = inverse_stats['win_rate_60min'] - original_stats['win_rate_60min']
        
        return {
            'pattern': pattern,
            'total_signals': len(pattern_signals),
            'original_performance': original_stats,
            'inverse_performance': inverse_stats,
            'improvement_30min': round(improvement_30, 1),
            'improvement_60min': round(improvement_60, 1),
            'is_better_inverted': improvement_30 > 10  # Consider it better if >10% improvement
        }
        
    def run_inverse_analysis(self) -> Dict:
        \"\"\"Run complete inverse signal analysis\"\"\"
        logger.info(\"🔄 Starting inverse signal analysis...\")
        
        # Load kill list to get patterns to test
        kill_list = self.load_kill_list()
        if not kill_list:
            logger.warning(\"No kill list found - nothing to analyze\")
            return {}
            
        patterns_to_test = [item['pattern'] for item in kill_list.get('patterns_to_kill', [])]
        
        if not patterns_to_test:
            logger.info(\"No patterns marked for elimination\")
            return {}
            
        logger.info(f\"🎯 Testing {len(patterns_to_test)} eliminated patterns for inverse performance\")
        
        # Load signals for these patterns
        signals = self.load_signals_for_patterns(patterns_to_test)
        if not signals:
            logger.warning(\"No signals found for patterns to test\")
            return {}
            
        # Analyze each pattern
        results = {
            'analysis_timestamp': datetime.now().isoformat(),
            'patterns_tested': len(patterns_to_test),
            'total_signals_analyzed': len(signals),
            'pattern_results': [],
            'inverse_opportunities': [],
            'summary': {}
        }
        
        patterns_improved_by_inversion = []
        total_improvement_30min = 0
        total_improvement_60min = 0
        
        for pattern in patterns_to_test:
            pattern_analysis = self.analyze_pattern_inverse_performance(signals, pattern)
            
            if pattern_analysis:
                results['pattern_results'].append(pattern_analysis)
                
                improvement_30 = pattern_analysis['improvement_30min']
                improvement_60 = pattern_analysis['improvement_60min']
                
                total_improvement_30min += improvement_30
                total_improvement_60min += improvement_60
                
                # Check if this pattern is significantly better when inverted
                if pattern_analysis['is_better_inverted']:
                    patterns_improved_by_inversion.append(pattern)
                    
                    results['inverse_opportunities'].append({
                        'pattern': pattern,
                        'original_win_rate': pattern_analysis['original_performance']['win_rate_30min'],
                        'inverse_win_rate': pattern_analysis['inverse_performance']['win_rate_30min'],
                        'improvement': improvement_30,
                        'signal_count': pattern_analysis['total_signals'],
                        'recommendation': f\"INVERT {pattern} - improves from {pattern_analysis['original_performance']['win_rate_30min']}% to {pattern_analysis['inverse_performance']['win_rate_30min']}%\"
                    })
                    
        # Generate summary
        results['summary'] = {
            'patterns_improved_by_inversion': len(patterns_improved_by_inversion),
            'avg_improvement_30min': round(total_improvement_30min / max(len(patterns_to_test), 1), 1),
            'avg_improvement_60min': round(total_improvement_60min / max(len(patterns_to_test), 1), 1),
            'best_inverse_opportunities': patterns_improved_by_inversion
        }
        
        # Save results
        self.save_results(results)
        
        # Log findings
        self.log_inverse_findings(results)
        
        return results
        
    def save_results(self, results: Dict):
        \"\"\"Save inverse analysis results to file\"\"\"
        try:
            with open(self.inverse_results_file, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f\"💾 Inverse analysis results saved to {self.inverse_results_file}\")
        except Exception as e:
            logger.error(f\"❌ Error saving results: {e}\")
            
    def log_inverse_findings(self, results: Dict):
        \"\"\"Log key inverse analysis findings\"\"\"
        logger.info(\"\
\" + \"=\"*60)
        logger.info(\"🔄 INVERSE SIGNAL ANALYSIS RESULTS\")
        logger.info(\"=\"*60)
        
        summary = results.get('summary', {})
        opportunities = results.get('inverse_opportunities', [])
        
        logger.info(f\"\
📊 ANALYSIS SUMMARY:\")
        logger.info(f\"  Patterns tested: {results.get('patterns_tested', 0)}\")
        logger.info(f\"  Signals analyzed: {results.get('total_signals_analyzed', 0)}\")
        logger.info(f\"  Patterns improved by inversion: {summary.get('patterns_improved_by_inversion', 0)}\")
        logger.info(f\"  Average 30min improvement: {summary.get('avg_improvement_30min', 0)}%\")
        
        if opportunities:
            logger.info(\"\
🔄 INVERSE OPPORTUNITIES FOUND:\")
            for opp in opportunities:
                logger.info(f\"  ⚡ {opp['recommendation']} ({opp['signal_count']} signals)\")
        else:
            logger.info(\"\
❌ No patterns significantly improved by inversion\")
            
        # Show detailed results for each pattern
        logger.info(\"\
📈 DETAILED PATTERN ANALYSIS:\")
        for pattern_result in results.get('pattern_results', []):
            pattern = pattern_result['pattern']
            orig_wr = pattern_result['original_performance']['win_rate_30min']
            inv_wr = pattern_result['inverse_performance']['win_rate_30min']
            improvement = pattern_result['improvement_30min']
            
            status = \"🔄 INVERT\" if improvement > 10 else \"❌ NO BENEFIT\"
            logger.info(f\"  {status} {pattern}: {orig_wr}% → {inv_wr}% ({improvement:+.1f}%)\")
            
        logger.info(\"=\"*60 + \"\
\")

def main():
    \"\"\"Main function for standalone operation\"\"\"
    detector = InverseSignalDetector()
    
    try:
        results = detector.run_inverse_analysis()
        
        if results:
            opportunities = len(results.get('inverse_opportunities', []))
            if opportunities > 0:
                logger.info(f\"🎯 Analysis complete: {opportunities} inverse opportunities found\")
            else:
                logger.info(\"🎯 Analysis complete: No inverse opportunities found\")
        else:
            logger.warning(\"No analysis results generated\")
            
    except Exception as e:
        logger.error(f\"❌ Inverse analysis failed: {e}\")
        raise

if __name__ == \"__main__\":
    main()