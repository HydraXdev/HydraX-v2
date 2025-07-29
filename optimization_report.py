#!/usr/bin/env python3
"""
Optimization Report - Daily signal performance analysis
Loads truth_log.jsonl and generates 24h performance summaries
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from collections import defaultdict, Counter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OptimizationReporter:
    """Generate daily optimization reports from truth data"""
    
    def __init__(self, 
                 truth_log_path: str = "/root/HydraX-v2/truth_log.jsonl",
                 reports_dir: str = "/root/HydraX-v2/reports"):
        
        self.truth_log_path = Path(truth_log_path)
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
    def load_last_24h_signals(self) -> List[Dict[str, Any]]:
        """Load signals from last 24 hours"""
        if not self.truth_log_path.exists():
            logger.warning(f"Truth log not found: {self.truth_log_path}")
            return []
        
        # Calculate 24h cutoff
        cutoff_time = datetime.now().timestamp() - (24 * 60 * 60)
        signals = []
        
        try:
            with open(self.truth_log_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        
                        # Check if signal is from last 24h
                        completed_at = data.get('completed_at', 0)
                        if completed_at >= cutoff_time:
                            signals.append(data)
                            
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON at line {line_num}")
                        continue
            
            logger.info(f"Loaded {len(signals)} signals from last 24h")
            return signals
            
        except Exception as e:
            logger.error(f"Error loading truth log: {e}")
            return []
    
    def analyze_signals(self, signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze signal performance"""
        if not signals:
            return self._get_empty_analysis()
        
        analysis = {
            'total_signals': len(signals),
            'wins': 0,
            'losses': 0,
            'win_rate': 0.0,
            'by_pair': defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0}),
            'by_hour': defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0}),
            'runtime_stats': {
                'win_runtimes': [],
                'loss_runtimes': []
            },
            'top_pairs': [],
            'bottom_pairs': []
        }
        
        # Analyze each signal
        for signal in signals:
            result = signal.get('result', '')
            symbol = signal.get('symbol', '').upper()
            runtime_minutes = signal.get('runtime_minutes', 0)
            completed_at = signal.get('completed_at', 0)
            
            # Overall stats
            if result == 'WIN':
                analysis['wins'] += 1
                analysis['runtime_stats']['win_runtimes'].append(runtime_minutes)
            elif result == 'LOSS':
                analysis['losses'] += 1
                analysis['runtime_stats']['loss_runtimes'].append(runtime_minutes)
            
            # By pair stats
            pair_stats = analysis['by_pair'][symbol]
            pair_stats['total'] += 1
            if result == 'WIN':
                pair_stats['wins'] += 1
            elif result == 'LOSS':
                pair_stats['losses'] += 1
            
            # By hour stats
            if completed_at > 0:
                hour = datetime.fromtimestamp(completed_at).hour
                hour_stats = analysis['by_hour'][hour]
                hour_stats['total'] += 1
                if result == 'WIN':
                    hour_stats['wins'] += 1
                elif result == 'LOSS':
                    hour_stats['losses'] += 1
        
        # Calculate win rate
        total_completed = analysis['wins'] + analysis['losses']
        if total_completed > 0:
            analysis['win_rate'] = analysis['wins'] / total_completed
        
        # Calculate pair win rates and rank them
        pair_performance = []
        for symbol, stats in analysis['by_pair'].items():
            total = stats['wins'] + stats['losses']
            if total > 0:
                win_rate = stats['wins'] / total
                pair_performance.append({
                    'symbol': symbol,
                    'win_rate': win_rate,
                    'wins': stats['wins'],
                    'losses': stats['losses'],
                    'total': total
                })
        
        # Sort by win rate
        pair_performance.sort(key=lambda x: x['win_rate'], reverse=True)
        
        # Get top 3 and bottom 3 pairs
        analysis['top_pairs'] = pair_performance[:3]
        analysis['bottom_pairs'] = pair_performance[-3:] if len(pair_performance) >= 3 else []
        
        return analysis
    
    def _get_empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis structure"""
        return {
            'total_signals': 0,
            'wins': 0,
            'losses': 0,
            'win_rate': 0.0,
            'by_pair': {},
            'by_hour': {},
            'runtime_stats': {
                'win_runtimes': [],
                'loss_runtimes': []
            },
            'top_pairs': [],
            'bottom_pairs': []
        }
    
    def format_report(self, analysis: Dict[str, Any]) -> str:
        """Format analysis into readable report"""
        report_date = datetime.now().strftime("%Y-%m-%d")
        report_time = datetime.now().strftime("%H:%M:%S")
        
        report = f"""
BITTEN OPTIMIZATION REPORT
Daily Performance Analysis
Generated: {report_date} {report_time}
{'=' * 50}

SUMMARY (Last 24 Hours)
{'=' * 25}
Signals Issued: {analysis['total_signals']}
Wins: {analysis['wins']}
Losses: {analysis['losses']}
Overall Win Rate: {analysis['win_rate']:.1%}
"""
        
        # Win rate by pair
        if analysis['by_pair']:
            report += f"""
WIN RATE BY PAIR
{'=' * 20}
"""
            for symbol, stats in sorted(analysis['by_pair'].items()):
                total = stats['wins'] + stats['losses']
                win_rate = stats['wins'] / total if total > 0 else 0
                report += f"{symbol:<8} {win_rate:>6.1%} ({stats['wins']}W/{stats['losses']}L)\n"
        
        # Win rate by hour block
        if analysis['by_hour']:
            report += f"""
WIN RATE BY HOUR BLOCK
{'=' * 25}
"""
            for hour in sorted(analysis['by_hour'].keys()):
                stats = analysis['by_hour'][hour]
                total = stats['wins'] + stats['losses']
                win_rate = stats['wins'] / total if total > 0 else 0
                report += f"{hour:02d}:00-{hour:02d}:59  {win_rate:>6.1%} ({stats['wins']}W/{stats['losses']}L)\n"
        
        # Average runtime comparison
        win_runtimes = analysis['runtime_stats']['win_runtimes']
        loss_runtimes = analysis['runtime_stats']['loss_runtimes']
        
        report += f"""
AVERAGE RUNTIME ANALYSIS
{'=' * 27}
"""
        
        if win_runtimes:
            avg_win_runtime = sum(win_runtimes) / len(win_runtimes)
            report += f"Avg Runtime (Wins):   {avg_win_runtime:>6.1f} minutes\n"
        else:
            report += f"Avg Runtime (Wins):   {'N/A':>6}\n"
        
        if loss_runtimes:
            avg_loss_runtime = sum(loss_runtimes) / len(loss_runtimes)
            report += f"Avg Runtime (Losses): {avg_loss_runtime:>6.1f} minutes\n"
        else:
            report += f"Avg Runtime (Losses): {'N/A':>6}\n"
        
        # Runtime difference analysis
        if win_runtimes and loss_runtimes:
            avg_win = sum(win_runtimes) / len(win_runtimes)
            avg_loss = sum(loss_runtimes) / len(loss_runtimes)
            if avg_loss < avg_win:
                report += f"⚠️  Losses fail {avg_win - avg_loss:.1f} minutes faster than wins\n"
            else:
                report += f"✅ Wins complete {avg_loss - avg_win:.1f} minutes faster than losses\n"
        
        # Top 3 pairs
        if analysis['top_pairs']:
            report += f"""
TOP 3 PERFORMING PAIRS
{'=' * 26}
"""
            for i, pair in enumerate(analysis['top_pairs'], 1):
                report += f"{i}. {pair['symbol']:<8} {pair['win_rate']:>6.1%} ({pair['total']} signals)\n"
        
        # Bottom 3 pairs
        if analysis['bottom_pairs']:
            report += f"""
BOTTOM 3 PERFORMING PAIRS
{'=' * 29}
"""
            for i, pair in enumerate(analysis['bottom_pairs'], 1):
                report += f"{i}. {pair['symbol']:<8} {pair['win_rate']:>6.1%} ({pair['total']} signals)\n"
        
        # Recommendations
        report += f"""
RECOMMENDATIONS
{'=' * 15}
"""
        
        if analysis['total_signals'] == 0:
            report += "• No signals in last 24h - check signal generation\n"
        elif analysis['win_rate'] < 0.5:
            report += f"• Win rate below 50% - review signal quality\n"
            if analysis['bottom_pairs']:
                worst_pair = analysis['bottom_pairs'][-1]
                report += f"• Consider cooldown for {worst_pair['symbol']} (worst performer)\n"
        else:
            report += "• Performance within acceptable range\n"
        
        if win_runtimes and loss_runtimes:
            avg_win = sum(win_runtimes) / len(win_runtimes)
            avg_loss = sum(loss_runtimes) / len(loss_runtimes)
            if avg_loss < 10 and avg_loss < avg_win * 0.5:
                report += "• High fast-failure rate detected - review entry timing\n"
        
        report += f"""
{'=' * 50}
Report generated by BITTEN Optimization System
Next report: {(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')}
"""
        
        return report
    
    def save_report(self, report_content: str) -> str:
        """Save report to file"""
        report_date = datetime.now().strftime("%Y%m%d")
        report_filename = f"daily_report_{report_date}.txt"
        report_path = self.reports_dir / report_filename
        
        try:
            with open(report_path, 'w') as f:
                f.write(report_content)
            
            logger.info(f"Report saved to {report_path}")
            return str(report_path)
            
        except Exception as e:
            logger.error(f"Error saving report: {e}")
            return ""
    
    def generate_daily_report(self) -> str:
        """Generate complete daily report"""
        logger.info("Generating daily optimization report...")
        
        # Load last 24h signals
        signals = self.load_last_24h_signals()
        
        # Analyze signals
        analysis = self.analyze_signals(signals)
        
        # Format report
        report_content = self.format_report(analysis)
        
        # Save report
        report_path = self.save_report(report_content)
        
        logger.info(f"Daily report generated: {len(signals)} signals analyzed")
        return report_path

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate daily optimization report')
    parser.add_argument('--truth-log', default='/root/HydraX-v2/truth_log.jsonl',
                       help='Path to truth log file')
    parser.add_argument('--reports-dir', default='/root/HydraX-v2/reports',
                       help='Directory to save reports')
    parser.add_argument('--print', action='store_true',
                       help='Print report to console')
    
    args = parser.parse_args()
    
    try:
        # Initialize reporter
        reporter = OptimizationReporter(
            truth_log_path=args.truth_log,
            reports_dir=args.reports_dir
        )
        
        # Generate report
        report_path = reporter.generate_daily_report()
        
        if report_path and args.print:
            # Print report to console
            with open(report_path, 'r') as f:
                print(f.read())
        
        if report_path:
            print(f"\n📊 Daily report saved: {report_path}")
        else:
            print("❌ Failed to generate report")
            
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise

if __name__ == "__main__":
    main()