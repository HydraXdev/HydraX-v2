#!/usr/bin/env python3
"""
Pattern Success Tracker - Track Elite Guard pattern performance in production

Monitors all pattern detections from Elite Guard, cross-references with truth_log outcomes,
and calculates success rates per pattern type to optimize the detection algorithms.
"""

import json
import time
import redis
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional
import statistics

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('PatternSuccessTracker')

class PatternSuccessTracker:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.truth_log_path = '/root/HydraX-v2/truth_log.jsonl'
        
        # Pattern types from Elite Guard
        self.pattern_stats = {
            'LIQUIDITY_SWEEP_REVERSAL': {'attempts': 0, 'wins': 0, 'total_pips': 0, 'avg_confidence': 0},
            'ORDER_BLOCK_BOUNCE': {'attempts': 0, 'wins': 0, 'total_pips': 0, 'avg_confidence': 0},
            'FAIR_VALUE_GAP_FILL': {'attempts': 0, 'wins': 0, 'total_pips': 0, 'avg_confidence': 0},
            'PRECISION_STRIKE': {'attempts': 0, 'wins': 0, 'total_pips': 0, 'avg_confidence': 0}
        }
        
        # Session and symbol breakdown
        self.session_performance = defaultdict(lambda: defaultdict(lambda: {'attempts': 0, 'wins': 0, 'pips': 0}))
        self.symbol_performance = defaultdict(lambda: defaultdict(lambda: {'attempts': 0, 'wins': 0, 'pips': 0}))
        
        # Confidence threshold analysis
        self.confidence_buckets = defaultdict(lambda: {'attempts': 0, 'wins': 0, 'pips': 0})
        
    def load_truth_data(self) -> List[Dict]:
        """Load truth tracker data for pattern analysis"""
        
        patterns = []
        
        try:
            with open(self.truth_log_path, 'r') as f:
                for line in f:
                    if line.strip():
                        trade = json.loads(line)
                        
                        # Focus on Elite Guard signals with patterns
                        if (trade.get('venom_version') == 'v7.0' and 
                            'ELITE_GUARD' in trade.get('signal_id', '') and
                            trade.get('signal_type')):
                            patterns.append(trade)
                            
            logger.info(f"Loaded {len(patterns)} Elite Guard pattern signals from truth tracker")
            return patterns
            
        except FileNotFoundError:
            logger.warning(f"Truth log file not found: {self.truth_log_path}")
            return []
        except Exception as e:
            logger.error(f"Error loading truth data: {e}")
            return []
    
    def track_pattern_signal(self, signal: Dict):
        """Track when pattern is detected and signaled"""
        
        pattern = signal.get('signal_type', 'UNKNOWN')
        confidence = signal.get('confidence', 0)
        signal_id = signal.get('signal_id')
        
        if pattern in self.pattern_stats:
            self.pattern_stats[pattern]['attempts'] += 1
            
            # Store signal for later outcome matching
            signal_key = f"pattern_signal:{signal_id}"
            signal_data = {
                'pattern': pattern,
                'confidence': confidence,
                'timestamp': time.time(),
                'symbol': signal.get('symbol', 'UNKNOWN'),
                'session': signal.get('session', 'UNKNOWN'),
                'entry_price': signal.get('entry_price', 0),
                'stop_loss': signal.get('stop_loss', 0),
                'take_profit': signal.get('take_profit', 0)
            }
            
            self.redis_client.hset(signal_key, mapping=signal_data)
            self.redis_client.expire(signal_key, 86400)  # 24 hour expiry
            
            logger.info(f"Tracking {pattern} signal: {signal_id} @ {confidence}% confidence")
    
    def update_pattern_outcome(self, signal_id: str, outcome: str, pips_result: float = 0):
        """Update pattern stats when trade completes"""
        
        signal_key = f"pattern_signal:{signal_id}"
        signal_data = self.redis_client.hgetall(signal_key)
        
        if not signal_data:
            logger.warning(f"Signal data not found for outcome update: {signal_id}")
            return
            
        pattern = signal_data['pattern']
        confidence = float(signal_data.get('confidence', 0))
        symbol = signal_data.get('symbol', 'UNKNOWN') 
        session = signal_data.get('session', 'UNKNOWN')
        
        if pattern in self.pattern_stats:
            if outcome in ['WIN', 'TP_HIT'] or pips_result > 0:
                self.pattern_stats[pattern]['wins'] += 1
                self.session_performance[session][pattern]['wins'] += 1
                self.symbol_performance[symbol][pattern]['wins'] += 1
                
            self.pattern_stats[pattern]['total_pips'] += pips_result
            self.session_performance[session][pattern]['pips'] += pips_result
            self.symbol_performance[symbol][pattern]['pips'] += pips_result
            
            # Confidence bucket tracking
            confidence_bucket = int(confidence // 10) * 10  # 70-79, 80-89, etc.
            if outcome in ['WIN', 'TP_HIT'] or pips_result > 0:
                self.confidence_buckets[confidence_bucket]['wins'] += 1
            self.confidence_buckets[confidence_bucket]['attempts'] += 1
            self.confidence_buckets[confidence_bucket]['pips'] += pips_result
            
            logger.info(f"Updated {pattern} outcome: {outcome} ({pips_result} pips)")
    
    def analyze_truth_data(self):
        """Analyze historical truth data for pattern performance"""
        
        trades = self.load_truth_data()
        
        for trade in trades:
            pattern = trade.get('signal_type', 'UNKNOWN')
            confidence = trade.get('confidence', 0)
            symbol = trade.get('symbol', 'UNKNOWN')
            session = trade.get('session', 'UNKNOWN')
            
            pips_result = trade.get('pips_result', 0)
            is_win = trade.get('outcome') == 'WIN' or trade.get('hit_tp_first', False) or pips_result > 0
            
            if pattern in self.pattern_stats:
                self.pattern_stats[pattern]['attempts'] += 1
                self.pattern_stats[pattern]['total_pips'] += pips_result
                
                if is_win:
                    self.pattern_stats[pattern]['wins'] += 1
                
                # Session breakdown
                self.session_performance[session][pattern]['attempts'] += 1
                self.session_performance[session][pattern]['pips'] += pips_result
                if is_win:
                    self.session_performance[session][pattern]['wins'] += 1
                
                # Symbol breakdown
                self.symbol_performance[symbol][pattern]['attempts'] += 1
                self.symbol_performance[symbol][pattern]['pips'] += pips_result
                if is_win:
                    self.symbol_performance[symbol][pattern]['wins'] += 1
                
                # Confidence analysis
                confidence_bucket = int(confidence // 10) * 10
                self.confidence_buckets[confidence_bucket]['attempts'] += 1
                self.confidence_buckets[confidence_bucket]['pips'] += pips_result
                if is_win:
                    self.confidence_buckets[confidence_bucket]['wins'] += 1
    
    def get_pattern_performance(self) -> Dict:
        """Calculate real performance per pattern"""
        
        # First analyze historical data
        self.analyze_truth_data()
        
        performance = {}
        
        for pattern, stats in self.pattern_stats.items():
            if stats['attempts'] > 0:
                win_rate = stats['wins'] / stats['attempts'] * 100
                avg_pips = stats['total_pips'] / stats['attempts']
                
                performance[pattern] = {
                    'win_rate': round(win_rate, 1),
                    'total_signals': stats['attempts'],
                    'total_wins': stats['wins'],
                    'total_pips': round(stats['total_pips'], 1),
                    'avg_pips_per_trade': round(avg_pips, 2),
                    'recommendation': self.get_recommendation(win_rate, avg_pips, stats['attempts']),
                    'confidence_threshold_suggestion': self.suggest_confidence_threshold(pattern),
                    'best_session': self.find_best_session_for_pattern(pattern),
                    'best_symbol': self.find_best_symbol_for_pattern(pattern)
                }
        
        return performance
    
    def get_recommendation(self, win_rate: float, avg_pips: float, sample_size: int) -> str:
        """Get recommendation based on pattern performance"""
        
        if sample_size < 10:
            return "INSUFFICIENT_DATA - Need more signals"
        elif win_rate < 30:
            return "DISABLE - Very poor performance"
        elif win_rate < 45:
            return "REVIEW_URGENTLY - Poor performance, check detection logic"
        elif win_rate < 55 and avg_pips < 5:
            return "TUNE_PARAMETERS - Mediocre performance"
        elif win_rate > 75 and avg_pips > 10:
            return "BOOST_CONFIDENCE - Excellent performance, raise thresholds"
        elif win_rate > 65:
            return "WORKING_WELL - Maintain current settings"
        else:
            return "MONITOR - Acceptable but room for improvement"
    
    def suggest_confidence_threshold(self, pattern: str) -> Dict:
        """Suggest optimal confidence threshold based on performance"""
        
        suggestions = {}
        
        for confidence_bucket, stats in self.confidence_buckets.items():
            if stats['attempts'] >= 5:  # Minimum sample size
                win_rate = stats['wins'] / stats['attempts'] * 100
                avg_pips = stats['pips'] / stats['attempts']
                
                suggestions[f"{confidence_bucket}-{confidence_bucket+9}%"] = {
                    'win_rate': round(win_rate, 1),
                    'avg_pips': round(avg_pips, 2),
                    'sample_size': stats['attempts'],
                    'score': win_rate + (avg_pips * 2)  # Composite score
                }
        
        if suggestions:
            # Find best performing confidence bucket
            best_bucket = max(suggestions.items(), key=lambda x: x[1]['score'])
            return {
                'current_analysis': suggestions,
                'recommended_minimum': best_bucket[0],
                'reasoning': f"Best performance: {best_bucket[1]['win_rate']}% win rate, {best_bucket[1]['avg_pips']} avg pips"
            }
        
        return {'error': 'Insufficient confidence data'}
    
    def find_best_session_for_pattern(self, pattern: str) -> Dict:
        """Find best performing session for specific pattern"""
        
        session_scores = {}
        
        for session, patterns in self.session_performance.items():
            if pattern in patterns and patterns[pattern]['attempts'] >= 3:
                stats = patterns[pattern]
                win_rate = stats['wins'] / stats['attempts'] * 100
                avg_pips = stats['pips'] / stats['attempts']
                
                session_scores[session] = {
                    'win_rate': round(win_rate, 1),
                    'avg_pips': round(avg_pips, 2),
                    'trades': stats['attempts'],
                    'score': win_rate + (avg_pips * 2)
                }
        
        if session_scores:
            best_session = max(session_scores.items(), key=lambda x: x[1]['score'])
            return {
                'best_session': best_session[0],
                'performance': best_session[1],
                'all_sessions': session_scores
            }
        
        return {'error': 'No session data available'}
    
    def find_best_symbol_for_pattern(self, pattern: str) -> Dict:
        """Find best performing symbol for specific pattern"""
        
        symbol_scores = {}
        
        for symbol, patterns in self.symbol_performance.items():
            if pattern in patterns and patterns[pattern]['attempts'] >= 3:
                stats = patterns[pattern]
                win_rate = stats['wins'] / stats['attempts'] * 100
                avg_pips = stats['pips'] / stats['attempts']
                
                symbol_scores[symbol] = {
                    'win_rate': round(win_rate, 1),
                    'avg_pips': round(avg_pips, 2), 
                    'trades': stats['attempts'],
                    'score': win_rate + (avg_pips * 2)
                }
        
        if symbol_scores:
            best_symbol = max(symbol_scores.items(), key=lambda x: x[1]['score'])
            return {
                'best_symbol': best_symbol[0],
                'performance': best_symbol[1],
                'all_symbols': symbol_scores
            }
        
        return {'error': 'No symbol data available'}
    
    def generate_optimization_report(self) -> Dict:
        """Generate comprehensive pattern optimization report"""
        
        performance = self.get_pattern_performance()
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'pattern_performance': performance,
            'overall_statistics': self.calculate_overall_stats(),
            'optimization_recommendations': self.generate_optimization_recommendations(performance),
            'confidence_analysis': dict(self.confidence_buckets),
            'session_breakdown': dict(self.session_performance),
            'symbol_breakdown': dict(self.symbol_performance)
        }
        
        return report
    
    def calculate_overall_stats(self) -> Dict:
        """Calculate overall pattern detection statistics"""
        
        total_attempts = sum(stats['attempts'] for stats in self.pattern_stats.values())
        total_wins = sum(stats['wins'] for stats in self.pattern_stats.values())
        total_pips = sum(stats['total_pips'] for stats in self.pattern_stats.values())
        
        return {
            'total_pattern_signals': total_attempts,
            'total_wins': total_wins,
            'overall_win_rate': round(total_wins / total_attempts * 100, 1) if total_attempts > 0 else 0,
            'total_pips_generated': round(total_pips, 1),
            'avg_pips_per_pattern': round(total_pips / total_attempts, 2) if total_attempts > 0 else 0
        }
    
    def generate_optimization_recommendations(self, performance: Dict) -> List[str]:
        """Generate actionable optimization recommendations"""
        
        recommendations = []
        
        for pattern, stats in performance.items():
            if stats['total_signals'] >= 10:  # Enough data
                if stats['win_rate'] < 45:
                    recommendations.append(f"🔴 {pattern}: Win rate {stats['win_rate']}% is too low - review detection algorithm")
                elif stats['win_rate'] > 75:
                    recommendations.append(f"🟢 {pattern}: Excellent {stats['win_rate']}% win rate - consider raising confidence threshold")
                
                if stats['avg_pips_per_trade'] < 5:
                    recommendations.append(f"🟡 {pattern}: Low average pips ({stats['avg_pips_per_trade']}) - check R:R ratios")
        
        # Confidence threshold recommendations
        best_confidence_bucket = max(self.confidence_buckets.items(),
                                   key=lambda x: x[1]['wins'] / x[1]['attempts'] if x[1]['attempts'] > 0 else 0)
        
        if best_confidence_bucket[1]['attempts'] >= 10:
            recommendations.append(f"🎯 Optimal confidence threshold appears to be {best_confidence_bucket[0]}% minimum")
        
        return recommendations

def main():
    """Run pattern success analysis"""
    tracker = PatternSuccessTracker()
    
    print("=== ELITE GUARD PATTERN SUCCESS ANALYSIS ===")
    
    # Generate performance report
    performance = tracker.get_pattern_performance()
    print("\nPattern Performance:")
    print(json.dumps(performance, indent=2))
    
    # Generate full optimization report
    report = tracker.generate_optimization_report()
    
    # Save report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(f'/root/HydraX-v2/reports/pattern_analysis_{timestamp}.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Pattern analysis complete. Report saved to reports/pattern_analysis_{timestamp}.json")
    
    # Print key recommendations
    if report['optimization_recommendations']:
        print("\n🎯 KEY RECOMMENDATIONS:")
        for rec in report['optimization_recommendations']:
            print(f"  {rec}")

if __name__ == "__main__":
    main()