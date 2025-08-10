#!/usr/bin/env python3
"""
Performance Analyzer - Analyze rapid (30-60min) vs sniper (120min) trade performance

Reads from existing truth_log.jsonl to categorize and analyze trades by duration.
Identifies optimal holding times per pattern and generates performance reports.
"""

import json
import time
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional
import statistics

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('PerformanceAnalyzer')

class PerformanceAnalyzer:
    def __init__(self):
        self.truth_log_path = '/root/HydraX-v2/truth_log.jsonl'
        self.rapid_window = (30, 60)  # minutes
        self.sniper_window = (60, 120)  # minutes
        
        # Performance categories
        self.ultra_quick = []    # <30 min
        self.rapid_trades = []   # 30-60 min
        self.sniper_trades = []  # 60-120 min
        self.marathon_trades = [] # >120 min
        
        self.pattern_duration_stats = defaultdict(list)
        
    def load_truth_data(self) -> List[Dict]:
        """Load all truth tracker data"""
        trades = []
        
        try:
            with open(self.truth_log_path, 'r') as f:
                for line in f:
                    if line.strip():
                        trade = json.loads(line)
                        
                        # Only process completed trades
                        if trade.get('completed') and trade.get('runtime_seconds', 0) > 0:
                            trades.append(trade)
                            
            logger.info(f"Loaded {len(trades)} completed trades from truth tracker")
            return trades
            
        except FileNotFoundError:
            logger.warning(f"Truth log file not found: {self.truth_log_path}")
            return []
        except Exception as e:
            logger.error(f"Error loading truth data: {e}")
            return []
    
    def categorize_trades_by_duration(self, trades: List[Dict]):
        """Categorize trades by duration"""
        
        for trade in trades:
            duration_seconds = trade.get('runtime_seconds', 0)
            duration_minutes = duration_seconds / 60
            
            if duration_minutes < 30:
                self.ultra_quick.append(trade)
            elif 30 <= duration_minutes <= 60:
                self.rapid_trades.append(trade)
            elif 60 < duration_minutes <= 120:
                self.sniper_trades.append(trade)
            else:
                self.marathon_trades.append(trade)
                
            # Track by pattern
            pattern = trade.get('signal_type', 'UNKNOWN')
            self.pattern_duration_stats[pattern].append({
                'duration_minutes': duration_minutes,
                'outcome': trade.get('outcome'),
                'pips_result': trade.get('pips_result', 0),
                'confidence': trade.get('confidence', 0)
            })
                
        logger.info(f"Categorized trades: Ultra-Quick: {len(self.ultra_quick)}, "
                   f"Rapid: {len(self.rapid_trades)}, Sniper: {len(self.sniper_trades)}, "
                   f"Marathon: {len(self.marathon_trades)}")
    
    def calculate_metrics(self, trades: List[Dict]) -> Optional[Dict]:
        """Calculate performance metrics for trade category"""
        
        if not trades:
            return None
            
        wins = [t for t in trades if t.get('outcome') == 'WIN' or t.get('hit_tp_first', False)]
        total_pips = sum(t.get('pips_result', 0) for t in trades)
        durations = [t.get('runtime_seconds', 0) / 60 for t in trades]
        confidences = [t.get('confidence', 0) for t in trades if t.get('confidence', 0) > 0]
        
        # Session analysis
        sessions = defaultdict(list)
        for trade in trades:
            session = trade.get('session', 'UNKNOWN')
            sessions[session].append(trade.get('outcome') == 'WIN' or trade.get('hit_tp_first', False))
        
        best_session = max(sessions.items(), 
                          key=lambda x: sum(x[1]) / len(x[1]) if x[1] else 0)[0] if sessions else 'UNKNOWN'
        
        # Pattern analysis  
        patterns = defaultdict(list)
        for trade in trades:
            pattern = trade.get('signal_type', 'UNKNOWN')
            patterns[pattern].append(trade.get('outcome') == 'WIN' or trade.get('hit_tp_first', False))
            
        best_pattern = max(patterns.items(),
                          key=lambda x: sum(x[1]) / len(x[1]) if x[1] else 0)[0] if patterns else 'UNKNOWN'
        
        return {
            'total_trades': len(trades),
            'wins': len(wins),
            'win_rate': len(wins) / len(trades) * 100,
            'avg_duration_minutes': statistics.mean(durations) if durations else 0,
            'median_duration_minutes': statistics.median(durations) if durations else 0,
            'total_pips': total_pips,
            'avg_pips_per_trade': total_pips / len(trades) if trades else 0,
            'avg_confidence': statistics.mean(confidences) if confidences else 0,
            'best_session': best_session,
            'best_pattern': best_pattern,
            'session_breakdown': {s: sum(outcomes) / len(outcomes) * 100 if outcomes else 0 
                                for s, outcomes in sessions.items()},
            'pattern_breakdown': {p: sum(outcomes) / len(outcomes) * 100 if outcomes else 0 
                                for p, outcomes in patterns.items()}
        }
    
    def find_optimal_duration_per_pattern(self) -> Dict:
        """Find optimal holding duration for each pattern"""
        
        optimal_durations = {}
        
        for pattern, data in self.pattern_duration_stats.items():
            if len(data) < 5:  # Need minimum data
                continue
                
            # Group by duration buckets
            duration_buckets = defaultdict(list)
            
            for entry in data:
                bucket = int(entry['duration_minutes'] // 15) * 15  # 15-minute buckets
                duration_buckets[bucket].append(entry)
            
            # Find best performing bucket
            best_bucket = None
            best_win_rate = 0
            best_avg_pips = 0
            
            bucket_stats = {}
            
            for bucket_start, entries in duration_buckets.items():
                if len(entries) < 3:  # Need minimum samples
                    continue
                    
                wins = sum(1 for e in entries if e['outcome'] == 'WIN')
                win_rate = wins / len(entries) * 100
                avg_pips = sum(e['pips_result'] for e in entries) / len(entries)
                
                bucket_stats[bucket_start] = {
                    'duration_range': f"{bucket_start}-{bucket_start+15} min",
                    'trades': len(entries),
                    'win_rate': win_rate,
                    'avg_pips': avg_pips,
                    'score': win_rate + (avg_pips * 2)  # Composite score
                }
                
                if bucket_stats[bucket_start]['score'] > (best_win_rate + (best_avg_pips * 2)):
                    best_win_rate = win_rate
                    best_avg_pips = avg_pips
                    best_bucket = bucket_start
            
            if best_bucket is not None:
                optimal_durations[pattern] = {
                    'optimal_duration_range': f"{best_bucket}-{best_bucket+15} minutes",
                    'optimal_win_rate': best_win_rate,
                    'optimal_avg_pips': best_avg_pips,
                    'recommendation': self.get_duration_recommendation(best_bucket),
                    'all_buckets': bucket_stats
                }
                
        return optimal_durations
    
    def get_duration_recommendation(self, optimal_minutes: int) -> str:
        """Get trading recommendation based on optimal duration"""
        
        if optimal_minutes <= 30:
            return "ULTRA_QUICK - Execute immediately with tight stops"
        elif optimal_minutes <= 60:
            return "RAPID_ASSAULT - Target 30-60 minute holds"
        elif optimal_minutes <= 120:
            return "PRECISION_STRIKE - Allow 1-2 hours for development"
        else:
            return "MARATHON - Long-term position, 2+ hours"
    
    def recommend_fire_mode(self, pattern: str, session: str) -> str:
        """Recommend rapid vs sniper based on historical performance"""
        
        # Get pattern-specific data
        pattern_data = self.pattern_duration_stats.get(pattern, [])
        session_data = [d for d in pattern_data if session == 'UNKNOWN' or session in str(d)]
        
        if not session_data:
            return "INSUFFICIENT_DATA"
        
        # Calculate performance in different windows
        rapid_performance = [d for d in session_data if 30 <= d['duration_minutes'] <= 60]
        sniper_performance = [d for d in session_data if 60 < d['duration_minutes'] <= 120]
        
        rapid_win_rate = sum(1 for d in rapid_performance if d['outcome'] == 'WIN') / len(rapid_performance) * 100 if rapid_performance else 0
        sniper_win_rate = sum(1 for d in sniper_performance if d['outcome'] == 'WIN') / len(sniper_performance) * 100 if sniper_performance else 0
        
        rapid_avg_pips = sum(d['pips_result'] for d in rapid_performance) / len(rapid_performance) if rapid_performance else 0
        sniper_avg_pips = sum(d['pips_result'] for d in sniper_performance) / len(sniper_performance) if sniper_performance else 0
        
        # Score = win_rate + (avg_pips * 2)
        rapid_score = rapid_win_rate + (rapid_avg_pips * 2)
        sniper_score = sniper_win_rate + (sniper_avg_pips * 2)
        
        if rapid_score > sniper_score + 10:  # 10 point threshold
            return "RAPID_RECOMMENDED"
        elif sniper_score > rapid_score + 10:
            return "SNIPER_RECOMMENDED"  
        else:
            return "EITHER_VIABLE"
    
    def generate_performance_report(self) -> Dict:
        """Generate comprehensive performance analysis report"""
        
        trades = self.load_truth_data()
        if not trades:
            return {'error': 'No trade data available'}
            
        self.categorize_trades_by_duration(trades)
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_trades_analyzed': len(trades),
            'duration_analysis': {
                'ultra_quick_performance': self.calculate_metrics(self.ultra_quick),
                'rapid_performance': self.calculate_metrics(self.rapid_trades),
                'sniper_performance': self.calculate_metrics(self.sniper_trades),
                'marathon_performance': self.calculate_metrics(self.marathon_trades)
            },
            'optimal_durations_per_pattern': self.find_optimal_duration_per_pattern(),
            'recommendations': self.generate_recommendations(),
            'summary': self.generate_summary()
        }
        
        return report
    
    def generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        # Compare category performance
        rapid_metrics = self.calculate_metrics(self.rapid_trades)
        sniper_metrics = self.calculate_metrics(self.sniper_trades)
        ultra_metrics = self.calculate_metrics(self.ultra_quick)
        
        if rapid_metrics and sniper_metrics:
            if rapid_metrics['win_rate'] > sniper_metrics['win_rate'] + 5:
                recommendations.append("Consider favoring rapid trades (30-60 min) - higher win rate observed")
            elif sniper_metrics['avg_pips_per_trade'] > rapid_metrics['avg_pips_per_trade'] * 1.5:
                recommendations.append("Sniper trades (60-120 min) show better pip efficiency despite lower win rate")
                
        if ultra_metrics and ultra_metrics['win_rate'] > 70:
            recommendations.append("Ultra-quick exits (<30 min) showing strong performance - consider scalping mode")
            
        # Pattern-specific recommendations
        pattern_optimas = self.find_optimal_duration_per_pattern()
        for pattern, data in pattern_optimas.items():
            if data['optimal_win_rate'] > 75:
                recommendations.append(f"{pattern}: Optimal hold time is {data['optimal_duration_range']} "
                                     f"({data['optimal_win_rate']:.1f}% win rate)")
        
        return recommendations
    
    def generate_summary(self) -> str:
        """Generate executive summary"""
        
        rapid_metrics = self.calculate_metrics(self.rapid_trades)
        sniper_metrics = self.calculate_metrics(self.sniper_trades)
        
        if rapid_metrics and sniper_metrics:
            summary = f"Analysis of {len(self.rapid_trades + self.sniper_trades)} trades shows:\n"
            summary += f"Rapid trades (30-60min): {rapid_metrics['win_rate']:.1f}% win rate, {rapid_metrics['avg_pips_per_trade']:.1f} avg pips\n"
            summary += f"Sniper trades (60-120min): {sniper_metrics['win_rate']:.1f}% win rate, {sniper_metrics['avg_pips_per_trade']:.1f} avg pips"
            return summary
        else:
            return "Insufficient completed trade data for meaningful analysis"
    
    def analyze_by_duration(self) -> Dict:
        """Main analysis method - public interface"""
        return self.generate_performance_report()

def main():
    """Run performance analysis"""
    analyzer = PerformanceAnalyzer()
    report = analyzer.analyze_by_duration()
    
    print("=== RAPID vs SNIPER PERFORMANCE ANALYSIS ===")
    print(json.dumps(report, indent=2))
    
    # Save report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(f'/root/HydraX-v2/reports/performance_analysis_{timestamp}.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Performance analysis complete. Report saved to reports/performance_analysis_{timestamp}.json")

if __name__ == "__main__":
    main()