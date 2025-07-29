#!/usr/bin/env python3
"""
🏆 TRUTH DASHBOARD INTEGRATION
Single source of truth for all BITTEN performance data
Reads exclusively from truth_log.jsonl - NO OTHER SOURCES
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

class TruthDashboard:
    """Black Box Truth Dashboard - Single source of truth for all performance data"""
    
    def __init__(self, truth_log_path: str = "/root/HydraX-v2/truth_log.jsonl"):
        self.truth_log_path = Path(truth_log_path)
        logger.info("🔒 Truth Dashboard initialized - SINGLE SOURCE OF TRUTH")
    
    def load_truth_data(self, hours_back: int = 24) -> List[Dict[str, Any]]:
        """Load truth data from specified time window"""
        if not self.truth_log_path.exists():
            logger.warning(f"Truth log not found: {self.truth_log_path}")
            return []
        
        cutoff_time = datetime.now().timestamp() - (hours_back * 3600)
        signals = []
        
        try:
            with open(self.truth_log_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        
                        # Parse timestamp
                        completed_at = data.get('completed_at')
                        if completed_at:
                            if isinstance(completed_at, str):
                                try:
                                    completed_ts = datetime.fromisoformat(completed_at.replace('Z', '+00:00')).timestamp()
                                except:
                                    completed_ts = datetime.now().timestamp()
                            else:
                                completed_ts = float(completed_at)
                            
                            if completed_ts >= cutoff_time:
                                signals.append(data)
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing truth log line {line_num}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error loading truth data: {e}")
            
        return signals
    
    def get_black_box_summary(self, hours_back: int = 24) -> Dict[str, Any]:
        """Get Black Box confirmed performance summary"""
        signals = self.load_truth_data(hours_back)
        
        if not signals:
            return {
                "total_tracked": 0,
                "black_box_confirmed_win_rate": 0.0,
                "signals_tracked_realtime": 0,
                "wins": 0,
                "losses": 0,
                "avg_runtime_wins": 0,
                "avg_runtime_losses": 0,
                "best_pairs": [],
                "worst_pairs": [],
                "last_update": "No data available",
                "confidence_interval": "Insufficient data",
                "sample_size_warning": True
            }
        
        # Calculate basic stats
        total_tracked = len(signals)
        wins = sum(1 for s in signals if s.get('result') == 'WIN')
        losses = sum(1 for s in signals if s.get('result') == 'LOSS')
        
        # Black Box Confirmed Win Rate
        black_box_win_rate = (wins / total_tracked * 100) if total_tracked > 0 else 0.0
        
        # Runtime analysis
        win_runtimes = []
        loss_runtimes = []
        
        for signal in signals:
            runtime = signal.get('runtime_seconds', 0)
            if signal.get('result') == 'WIN':
                win_runtimes.append(runtime)
            elif signal.get('result') == 'LOSS':
                loss_runtimes.append(runtime)
        
        avg_runtime_wins = sum(win_runtimes) / len(win_runtimes) if win_runtimes else 0
        avg_runtime_losses = sum(loss_runtimes) / len(loss_runtimes) if loss_runtimes else 0
        
        # Pair performance analysis
        pair_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0})
        
        for signal in signals:
            symbol = signal.get('symbol', 'UNKNOWN')
            result = signal.get('result')
            
            pair_stats[symbol]['total'] += 1
            if result == 'WIN':
                pair_stats[symbol]['wins'] += 1
            elif result == 'LOSS':
                pair_stats[symbol]['losses'] += 1
        
        # Calculate pair win rates and sort
        pair_performance = []
        for symbol, stats in pair_stats.items():
            if stats['total'] >= 3:  # Only pairs with significant data
                win_rate = (stats['wins'] / stats['total'] * 100) if stats['total'] > 0 else 0
                pair_performance.append({
                    'symbol': symbol,
                    'win_rate': win_rate,
                    'total': stats['total'],
                    'wins': stats['wins'],
                    'losses': stats['losses']
                })
        
        pair_performance.sort(key=lambda x: x['win_rate'], reverse=True)
        
        # Best and worst pairs (minimum 3 trades)
        best_pairs = pair_performance[:3] if pair_performance else []
        worst_pairs = pair_performance[-3:] if len(pair_performance) >= 3 else []
        
        # Confidence interval calculation
        if total_tracked >= 30:
            confidence_interval = f"±{1.96 * (black_box_win_rate * (100 - black_box_win_rate) / total_tracked) ** 0.5:.1f}% (95% CI)"
            sample_size_warning = False
        elif total_tracked >= 10:
            confidence_interval = f"±{2.58 * (black_box_win_rate * (100 - black_box_win_rate) / total_tracked) ** 0.5:.1f}% (Low sample)"
            sample_size_warning = True
        else:
            confidence_interval = "Insufficient data (<10 trades)"
            sample_size_warning = True
        
        # Last update timestamp
        if signals:
            latest_signal = max(signals, key=lambda x: x.get('completed_at', ''))
            last_update = latest_signal.get('completed_at', 'Unknown')
            if isinstance(last_update, str):
                try:
                    last_update = datetime.fromisoformat(last_update.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S UTC')
                except:
                    pass
        else:
            last_update = "No data available"
        
        return {
            "total_tracked": total_tracked,
            "black_box_confirmed_win_rate": round(black_box_win_rate, 1),
            "signals_tracked_realtime": total_tracked,
            "wins": wins,
            "losses": losses,
            "avg_runtime_wins": round(avg_runtime_wins / 60, 1),  # Convert to minutes
            "avg_runtime_losses": round(avg_runtime_losses / 60, 1),  # Convert to minutes
            "best_pairs": best_pairs,
            "worst_pairs": worst_pairs,
            "last_update": last_update,
            "confidence_interval": confidence_interval,
            "sample_size_warning": sample_size_warning
        }
    
    def get_time_series_data(self, hours_back: int = 168) -> List[Dict[str, Any]]:
        """Get time series data for charting"""
        signals = self.load_truth_data(hours_back)
        
        if not signals:
            return []
        
        # Group by hour
        hourly_data = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0})
        
        for signal in signals:
            completed_at = signal.get('completed_at')
            if completed_at:
                try:
                    if isinstance(completed_at, str):
                        dt = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                    else:
                        dt = datetime.fromtimestamp(float(completed_at))
                    
                    hour_key = dt.strftime('%Y-%m-%d %H:00')
                    result = signal.get('result')
                    
                    hourly_data[hour_key]['total'] += 1
                    if result == 'WIN':
                        hourly_data[hour_key]['wins'] += 1
                    elif result == 'LOSS':
                        hourly_data[hour_key]['losses'] += 1
                        
                except Exception as e:
                    logger.error(f"Error parsing timestamp: {e}")
                    continue
        
        # Convert to list and sort by time
        time_series = []
        for hour, stats in hourly_data.items():
            win_rate = (stats['wins'] / stats['total'] * 100) if stats['total'] > 0 else 0
            time_series.append({
                'timestamp': hour,
                'win_rate': round(win_rate, 1),
                'total': stats['total'],
                'wins': stats['wins'],
                'losses': stats['losses']
            })
        
        time_series.sort(key=lambda x: x['timestamp'])
        
        return time_series
    
    def get_detailed_breakdown(self, hours_back: int = 24) -> Dict[str, Any]:
        """Get detailed breakdown for analysis"""
        signals = self.load_truth_data(hours_back)
        
        if not signals:
            return {
                "signal_types": {},
                "exit_types": {},
                "tcs_ranges": {},
                "runtime_distribution": {},
                "hourly_distribution": {}
            }
        
        # Signal type analysis
        signal_types = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0})
        
        # Exit type analysis
        exit_types = defaultdict(lambda: {'count': 0, 'win_rate': 0})
        
        # TCS score ranges
        tcs_ranges = {
            "60-70": {'wins': 0, 'losses': 0, 'total': 0},
            "70-80": {'wins': 0, 'losses': 0, 'total': 0},
            "80-90": {'wins': 0, 'losses': 0, 'total': 0},
            "90-100": {'wins': 0, 'losses': 0, 'total': 0}
        }
        
        # Runtime distribution
        runtime_ranges = {
            "0-30min": {'wins': 0, 'losses': 0, 'total': 0},
            "30-60min": {'wins': 0, 'losses': 0, 'total': 0},
            "1-2hr": {'wins': 0, 'losses': 0, 'total': 0},
            "2hr+": {'wins': 0, 'losses': 0, 'total': 0}
        }
        
        # Hourly distribution
        hourly_dist = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0})
        
        for signal in signals:
            result = signal.get('result')
            signal_type = signal.get('signal_type', 'UNKNOWN')
            exit_type = signal.get('exit_type', 'UNKNOWN')
            tcs_score = float(signal.get('tcs_score', 0))
            runtime_seconds = signal.get('runtime_seconds', 0)
            
            # Signal type stats
            signal_types[signal_type]['total'] += 1
            if result == 'WIN':
                signal_types[signal_type]['wins'] += 1
            elif result == 'LOSS':
                signal_types[signal_type]['losses'] += 1
            
            # Exit type stats
            exit_types[exit_type]['count'] += 1
            
            # TCS range stats
            if 60 <= tcs_score < 70:
                tcs_range = "60-70"
            elif 70 <= tcs_score < 80:
                tcs_range = "70-80"
            elif 80 <= tcs_score < 90:
                tcs_range = "80-90"
            elif 90 <= tcs_score <= 100:
                tcs_range = "90-100"
            else:
                continue  # Skip invalid scores
            
            tcs_ranges[tcs_range]['total'] += 1
            if result == 'WIN':
                tcs_ranges[tcs_range]['wins'] += 1
            elif result == 'LOSS':
                tcs_ranges[tcs_range]['losses'] += 1
            
            # Runtime distribution
            runtime_minutes = runtime_seconds / 60
            if runtime_minutes < 30:
                runtime_range = "0-30min"
            elif runtime_minutes < 60:
                runtime_range = "30-60min"
            elif runtime_minutes < 120:
                runtime_range = "1-2hr"
            else:
                runtime_range = "2hr+"
            
            runtime_ranges[runtime_range]['total'] += 1
            if result == 'WIN':
                runtime_ranges[runtime_range]['wins'] += 1
            elif result == 'LOSS':
                runtime_ranges[runtime_range]['losses'] += 1
            
            # Hourly distribution
            completed_at = signal.get('completed_at')
            if completed_at:
                try:
                    if isinstance(completed_at, str):
                        dt = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                    else:
                        dt = datetime.fromtimestamp(float(completed_at))
                    
                    hour = dt.hour
                    hourly_dist[hour]['total'] += 1
                    if result == 'WIN':
                        hourly_dist[hour]['wins'] += 1
                    elif result == 'LOSS':
                        hourly_dist[hour]['losses'] += 1
                        
                except Exception:
                    continue
        
        # Calculate win rates for all categories
        for category_dict in [signal_types, tcs_ranges, runtime_ranges]:
            for key, stats in category_dict.items():
                if stats['total'] > 0:
                    stats['win_rate'] = round(stats['wins'] / stats['total'] * 100, 1)
                else:
                    stats['win_rate'] = 0.0
        
        # Calculate exit type win rates
        for exit_type, stats in exit_types.items():
            # Count wins for this exit type
            wins = sum(1 for s in signals if s.get('exit_type') == exit_type and s.get('result') == 'WIN')
            total = stats['count']
            stats['win_rate'] = round(wins / total * 100, 1) if total > 0 else 0
        
        return {
            "signal_types": dict(signal_types),
            "exit_types": dict(exit_types),
            "tcs_ranges": tcs_ranges,
            "runtime_distribution": runtime_ranges,
            "hourly_distribution": dict(hourly_dist)
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Check system health and data integrity"""
        return {
            "truth_log_exists": self.truth_log_path.exists(),
            "truth_log_path": str(self.truth_log_path),
            "file_size_bytes": self.truth_log_path.stat().st_size if self.truth_log_path.exists() else 0,
            "total_records": len(self.load_truth_data(8760)),  # All records (1 year)
            "last_24h_records": len(self.load_truth_data(24)),
            "last_1h_records": len(self.load_truth_data(1)),
            "system_status": "OPERATIONAL" if self.truth_log_path.exists() else "NO_DATA"
        }

# Global instance
truth_dashboard = TruthDashboard()