#!/usr/bin/env python3
"""
Engineer Agent - Adaptive signal optimization based on truth data
Analyzes signal outcomes and generates dynamic overrides for CITADEL
"""

import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from collections import defaultdict, Counter
from dataclasses import dataclass
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class SignalOutcome:
    """Individual signal outcome from truth log"""
    signal_id: str
    symbol: str
    direction: str
    result: str  # WIN or LOSS
    entry_price: float
    exit_price: float
    runtime_seconds: int
    runtime_minutes: float
    pips_result: float
    tcs_score: float
    created_at: float
    completed_at: float

class PatternAnalyzer:
    """Analyzes trading patterns from truth data"""
    
    def __init__(self):
        self.outcomes: List[SignalOutcome] = []
        self.analysis_time = datetime.now(timezone.utc)
    
    def load_truth_log(self, truth_log_path: str) -> int:
        """Load all outcomes from truth log"""
        self.outcomes = []
        
        if not os.path.exists(truth_log_path):
            logger.warning(f"Truth log not found: {truth_log_path}")
            return 0
        
        try:
            with open(truth_log_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        outcome = SignalOutcome(
                            signal_id=data.get('signal_id', ''),
                            symbol=data.get('symbol', '').upper(),
                            direction=data.get('direction', '').upper(),
                            result=data.get('result', ''),
                            entry_price=float(data.get('entry_price', 0)),
                            exit_price=float(data.get('exit_price', 0)),
                            runtime_seconds=int(data.get('runtime_seconds', 0)),
                            runtime_minutes=float(data.get('runtime_minutes', 0)),
                            pips_result=float(data.get('pips_result', 0)),
                            tcs_score=float(data.get('tcs_score', 0)),
                            created_at=float(data.get('created_at', 0)),
                            completed_at=float(data.get('completed_at', 0))
                        )
                        self.outcomes.append(outcome)
                        
                    except (json.JSONDecodeError, ValueError, KeyError) as e:
                        logger.warning(f"Invalid truth log entry at line {line_num}: {e}")
                        continue
            
            logger.info(f"Loaded {len(self.outcomes)} signal outcomes from truth log")
            return len(self.outcomes)
            
        except Exception as e:
            logger.error(f"Error loading truth log: {e}")
            return 0
    
    def analyze_by_pair(self) -> Dict[str, Dict]:
        """Analyze outcomes by trading pair"""
        pair_stats = defaultdict(lambda: {
            'total': 0, 'wins': 0, 'losses': 0, 'win_rate': 0.0,
            'avg_runtime': 0.0, 'avg_pips': 0.0, 'recent_outcomes': [],
            'consecutive_losses': 0, 'last_outcome_time': 0
        })
        
        # Group by pair
        for outcome in self.outcomes:
            stats = pair_stats[outcome.symbol]
            stats['total'] += 1
            stats['last_outcome_time'] = max(stats['last_outcome_time'], outcome.completed_at)
            
            if outcome.result == 'WIN':
                stats['wins'] += 1
                stats['consecutive_losses'] = 0  # Reset streak
            else:
                stats['losses'] += 1
                stats['consecutive_losses'] += 1
            
            # Track recent outcomes (last 10)
            stats['recent_outcomes'].append(outcome.result)
            if len(stats['recent_outcomes']) > 10:
                stats['recent_outcomes'].pop(0)
        
        # Calculate derived metrics
        for symbol, stats in pair_stats.items():
            if stats['total'] > 0:
                stats['win_rate'] = stats['wins'] / stats['total']
                
                # Get outcomes for this pair
                pair_outcomes = [o for o in self.outcomes if o.symbol == symbol]
                if pair_outcomes:
                    stats['avg_runtime'] = statistics.mean([o.runtime_minutes for o in pair_outcomes])
                    stats['avg_pips'] = statistics.mean([o.pips_result for o in pair_outcomes])
        
        return dict(pair_stats)
    
    def analyze_by_time(self) -> Dict[str, Dict]:
        """Analyze outcomes by time of day (hourly)"""
        hourly_stats = defaultdict(lambda: {
            'total': 0, 'wins': 0, 'losses': 0, 'win_rate': 0.0,
            'outcomes': []
        })
        
        for outcome in self.outcomes:
            # Get hour from created_at timestamp
            hour = datetime.fromtimestamp(outcome.created_at).hour
            hour_key = f"{hour:02d}:00"
            
            stats = hourly_stats[hour_key]
            stats['total'] += 1
            stats['outcomes'].append(outcome.result)
            
            if outcome.result == 'WIN':
                stats['wins'] += 1
            else:
                stats['losses'] += 1
        
        # Calculate win rates
        for hour, stats in hourly_stats.items():
            if stats['total'] > 0:
                stats['win_rate'] = stats['wins'] / stats['total']
        
        return dict(hourly_stats)
    
    def analyze_by_runtime(self) -> Dict[str, Any]:
        """Analyze outcomes by signal runtime"""
        if not self.outcomes:
            return {}
        
        runtimes = [o.runtime_minutes for o in self.outcomes]
        fast_failures = [o for o in self.outcomes if o.result == 'LOSS' and o.runtime_minutes < 10]
        
        return {
            'avg_runtime': statistics.mean(runtimes),
            'median_runtime': statistics.median(runtimes),
            'fast_failures_count': len(fast_failures),
            'fast_failure_rate': len(fast_failures) / len(self.outcomes),
            'fast_failure_pairs': Counter([o.symbol for o in fast_failures]).most_common(5)
        }
    
    def analyze_by_tcs_score(self) -> Dict[str, Any]:
        """Analyze outcomes by TCS confidence score"""
        if not self.outcomes:
            return {}
        
        # Group by TCS score ranges
        score_ranges = {
            'high': [o for o in self.outcomes if o.tcs_score >= 80],
            'medium': [o for o in self.outcomes if 70 <= o.tcs_score < 80],
            'low': [o for o in self.outcomes if o.tcs_score < 70]
        }
        
        analysis = {}
        for range_name, outcomes in score_ranges.items():
            if outcomes:
                wins = sum(1 for o in outcomes if o.result == 'WIN')
                analysis[range_name] = {
                    'total': len(outcomes),
                    'wins': wins,
                    'losses': len(outcomes) - wins,
                    'win_rate': wins / len(outcomes),
                    'avg_score': statistics.mean([o.tcs_score for o in outcomes])
                }
        
        return analysis

class EngineerAgent:
    """Main engineer agent that generates adaptive overrides"""
    
    def __init__(self, 
                 truth_log_path: str = "/root/HydraX-v2/truth_log.jsonl",
                 state_path: str = "/root/HydraX-v2/citadel_state.json"):
        
        self.truth_log_path = Path(truth_log_path)
        self.state_path = Path(state_path)
        self.analyzer = PatternAnalyzer()
        
        # Override thresholds (configurable)
        self.thresholds = {
            'consecutive_loss_limit': 3,          # 3 losses in a row = cooldown
            'min_win_rate_hourly': 0.4,           # Below 40% hourly = restrict
            'fast_failure_rate_limit': 0.6,       # 60%+ fast failures = penalty
            'min_sample_size': 5,                 # Minimum trades for analysis
            'cooldown_duration_minutes': 30,      # Default cooldown period
            'tcs_penalty_increase': 10.0,         # TCS penalty amount
            'auto_close_hours': 2.0,              # Auto-close after 2 hours
            'min_signal_threshold_24h': 18,       # Minimum signals per 24h
            'min_signal_threshold_12h': 9,        # Minimum signals per 12h
            'tcs_flex_amount': 4.0,               # TCS penalty reduction for pressure release
            'pressure_release_duration_hours': 4  # How long to maintain pressure release
        }
        
        logger.info("Engineer Agent initialized")
    
    def generate_overrides(self) -> Dict[str, Any]:
        """Generate CITADEL overrides based on pattern analysis"""
        
        # Load and analyze truth data
        outcomes_count = self.analyzer.load_truth_log(str(self.truth_log_path))
        if outcomes_count == 0:
            logger.info("No truth data available - generating minimal overrides")
            return self._get_default_overrides()
        
        # Perform analysis
        pair_analysis = self.analyzer.analyze_by_pair()
        time_analysis = self.analyzer.analyze_by_time() 
        runtime_analysis = self.analyzer.analyze_by_runtime()
        tcs_analysis = self.analyzer.analyze_by_tcs_score()
        
        # Generate overrides
        overrides = {'global': {}}
        current_time = datetime.now(timezone.utc)
        
        # Analyze each pair for issues
        for symbol, stats in pair_analysis.items():
            if stats['total'] < self.thresholds['min_sample_size']:
                continue  # Skip pairs with insufficient data
            
            pair_overrides = {}
            
            # Check for consecutive losses
            if stats['consecutive_losses'] >= self.thresholds['consecutive_loss_limit']:
                cooldown_until = current_time + timedelta(minutes=self.thresholds['cooldown_duration_minutes'])
                pair_overrides.update({
                    'status': 'cooldown',
                    'cooldown_until': cooldown_until.isoformat(),
                    'reason': f"{stats['consecutive_losses']} consecutive losses"
                })
                logger.warning(f"COOLDOWN: {symbol} - {stats['consecutive_losses']} consecutive losses")
            
            # Check for low win rate
            elif stats['win_rate'] < self.thresholds['min_win_rate_hourly']:
                pair_overrides.update({
                    'tcs_penalty': stats['win_rate'] * 20,  # Lower win rate = higher penalty
                    'entry_delay_ms': 5000,  # 5 second delay
                    'reason': f"Low win rate: {stats['win_rate']:.1%}"
                })
                logger.info(f"PENALTY: {symbol} - Win rate {stats['win_rate']:.1%}")
            
            # Check for fast failures
            symbol_outcomes = [o for o in self.analyzer.outcomes if o.symbol == symbol]
            fast_failures = [o for o in symbol_outcomes if o.result == 'LOSS' and o.runtime_minutes < 10]
            
            if len(symbol_outcomes) > 0:
                fast_failure_rate = len(fast_failures) / len(symbol_outcomes)
                if fast_failure_rate > self.thresholds['fast_failure_rate_limit']:
                    pair_overrides.update({
                        'tcs_penalty': self.thresholds['tcs_penalty_increase'],
                        'min_runtime_minutes': 15,  # Force longer analysis
                        'reason': f"High fast failure rate: {fast_failure_rate:.1%}"
                    })
                    logger.info(f"FAST_FAIL_PENALTY: {symbol} - {fast_failure_rate:.1%} fast failures")
            
            if pair_overrides:
                overrides[symbol.lower()] = pair_overrides
        
        # Global overrides based on overall performance
        if runtime_analysis.get('fast_failure_rate', 0) > 0.5:
            overrides['global']['auto_close_seconds'] = int(self.thresholds['auto_close_hours'] * 3600)
            logger.info(f"GLOBAL: Auto-close enabled - {runtime_analysis['fast_failure_rate']:.1%} fast failures")
        
        # Time-based restrictions
        current_hour = current_time.hour
        current_hour_key = f"{current_hour:02d}:00"
        
        if current_hour_key in time_analysis:
            hour_stats = time_analysis[current_hour_key]
            if (hour_stats['total'] >= self.thresholds['min_sample_size'] and 
                hour_stats['win_rate'] < self.thresholds['min_win_rate_hourly']):
                
                overrides['global']['hour_restriction'] = {
                    'restricted_hour': current_hour,
                    'min_tcs_required': 85.0,
                    'reason': f"Poor hour performance: {hour_stats['win_rate']:.1%}"
                }
                logger.info(f"HOUR_RESTRICTION: Hour {current_hour} - {hour_stats['win_rate']:.1%} win rate")
        
        # Add metadata
        overrides['_metadata'] = {
            'generated_at': current_time.isoformat(),
            'total_outcomes_analyzed': outcomes_count,
            'pairs_analyzed': len(pair_analysis),
            'analysis_summary': {
                'avg_runtime_minutes': runtime_analysis.get('avg_runtime', 0),
                'fast_failure_rate': runtime_analysis.get('fast_failure_rate', 0),
                'total_pairs_with_overrides': len([k for k in overrides.keys() if k not in ['global', '_metadata']])
            }
        }
        
        return overrides
    
    def _get_default_overrides(self) -> Dict[str, Any]:
        """Generate minimal default overrides when no data available"""
        return {
            'global': {
                'auto_close_seconds': 7200,  # 2 hours default
                'default_tcs_minimum': 70.0
            },
            '_metadata': {
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'total_outcomes_analyzed': 0,
                'status': 'no_data_available'
            }
        }
    
    def save_overrides(self, overrides: Dict[str, Any]) -> bool:
        """Save overrides to citadel_state.json"""
        try:
            # Ensure directory exists
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save with pretty formatting
            with open(self.state_path, 'w') as f:
                json.dump(overrides, f, indent=2, sort_keys=True)
            
            logger.info(f"Overrides saved to {self.state_path}")
            
            # Log summary
            pair_overrides = len([k for k in overrides.keys() if k not in ['global', '_metadata']])
            global_overrides = len(overrides.get('global', {}))
            logger.info(f"Generated {pair_overrides} pair overrides, {global_overrides} global overrides")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving overrides: {e}")
            return False
    
    def check_and_lift_cooldowns(self) -> Dict[str, Any]:
        """Check cooldowns and lift expired ones or those with 2+ wins in last 5 trades"""
        try:
            # Load current state
            current_state = self.get_current_overrides()
            if not current_state:
                return {}
            
            current_time = datetime.now(timezone.utc)
            lifted_cooldowns = []
            
            # Check each pair for cooldown status
            for symbol_key, config in list(current_state.items()):
                if symbol_key in ['global', '_metadata']:
                    continue
                
                symbol_upper = symbol_key.upper()
                
                # Skip if not in cooldown
                if config.get('status') != 'cooldown':
                    continue
                
                should_lift = False
                lift_reason = ""
                
                # Check if cooldown time has expired
                cooldown_until = config.get('cooldown_until')
                if cooldown_until:
                    try:
                        cooldown_time = datetime.fromisoformat(cooldown_until.replace('Z', '+00:00'))
                        if current_time >= cooldown_time:
                            should_lift = True
                            lift_reason = "cooldown_expired"
                    except (ValueError, TypeError):
                        # Invalid date format, lift cooldown
                        should_lift = True
                        lift_reason = "invalid_cooldown_date"
                
                # Check recent performance (2+ wins in last 5 trades)
                if not should_lift:
                    symbol_outcomes = [o for o in self.analyzer.outcomes if o.symbol == symbol_upper]
                    if len(symbol_outcomes) >= 5:
                        # Get last 5 trades for this symbol
                        recent_trades = sorted(symbol_outcomes, key=lambda x: x.completed_at)[-5:]
                        wins = sum(1 for trade in recent_trades if trade.result == 'WIN')
                        
                        if wins >= 2:
                            should_lift = True
                            lift_reason = f"performance_recovery_{wins}_wins_in_5_trades"
                
                # Lift cooldown if criteria met
                if should_lift:
                    # Remove cooldown status and reset penalties
                    del current_state[symbol_key]
                    
                    lifted_cooldowns.append({
                        'symbol': symbol_upper,
                        'reason': lift_reason,
                        'lifted_at': current_time.isoformat(),
                        'previous_cooldown_until': cooldown_until
                    })
                    
                    logger.info(f"🔓 COOLDOWN LIFTED: {symbol_upper} - {lift_reason}")
            
            # Save updated state if any cooldowns were lifted
            if lifted_cooldowns:
                # Update metadata
                if '_metadata' not in current_state:
                    current_state['_metadata'] = {}
                
                current_state['_metadata']['last_cooldown_check'] = current_time.isoformat()
                current_state['_metadata']['cooldowns_lifted'] = len(lifted_cooldowns)
                
                # Save the updated state
                self.save_overrides(current_state)
                
                logger.info(f"💫 Lifted {len(lifted_cooldowns)} cooldowns")
            
            return {
                'cooldowns_lifted': lifted_cooldowns,
                'total_lifted': len(lifted_cooldowns),
                'check_time': current_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking cooldowns: {e}")
            return {}
    
    def count_recent_signals(self) -> Dict[str, int]:
        """Count signals from truth_log.jsonl in last 12h and 24h"""
        try:
            current_time = datetime.now(timezone.utc)
            cutoff_12h = current_time - timedelta(hours=12)
            cutoff_24h = current_time - timedelta(hours=24)
            
            count_12h = 0
            count_24h = 0
            
            if not self.truth_log_path.exists():
                logger.warning(f"Truth log not found: {self.truth_log_path}")
                return {'12h': 0, '24h': 0}
            
            with open(self.truth_log_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        completed_at = data.get('completed_at', 0)
                        signal_time = datetime.fromtimestamp(completed_at, tz=timezone.utc)
                        
                        if signal_time >= cutoff_24h:
                            count_24h += 1
                            if signal_time >= cutoff_12h:
                                count_12h += 1
                                
                    except (json.JSONDecodeError, ValueError, OSError):
                        continue
            
            logger.info(f"📊 Signal count: {count_12h} (12h), {count_24h} (24h)")
            return {'12h': count_12h, '24h': count_24h}
            
        except Exception as e:
            logger.error(f"Error counting recent signals: {e}")
            return {'12h': 0, '24h': 0}
    
    def check_pressure_release_needed(self, signal_counts: Dict[str, int]) -> Dict[str, Any]:
        """Check if pressure release is needed due to low signal volume"""
        try:
            count_12h = signal_counts.get('12h', 0)
            count_24h = signal_counts.get('24h', 0)
            
            # Check if below thresholds
            below_12h = count_12h < self.thresholds['min_signal_threshold_12h']
            below_24h = count_24h < self.thresholds['min_signal_threshold_24h']
            
            if not (below_12h or below_24h):
                return {'needed': False}
            
            # Find top performing pair to restore if on cooldown
            current_state = self.get_current_overrides()
            cooled_pairs = [symbol for symbol, config in current_state.items() 
                          if symbol not in ['global', '_metadata'] and config.get('status') == 'cooldown']
            
            restored_pair = None
            if cooled_pairs:
                # Get pair performance from analyzer outcomes
                pair_performance = {}
                for symbol in cooled_pairs:
                    symbol_upper = symbol.upper()
                    symbol_outcomes = [o for o in self.analyzer.outcomes if o.symbol == symbol_upper]
                    if symbol_outcomes:
                        wins = sum(1 for o in symbol_outcomes if o.result == 'WIN')
                        total = len(symbol_outcomes)
                        win_rate = wins / total if total > 0 else 0
                        pair_performance[symbol] = {
                            'win_rate': win_rate,
                            'total_trades': total
                        }
                
                # Select best performing cooled pair
                if pair_performance:
                    best_pair = max(pair_performance.items(), 
                                  key=lambda x: (x[1]['win_rate'], x[1]['total_trades']))
                    restored_pair = best_pair[0].upper()
            
            # Default to EURUSD if no cooled pairs or analysis data
            if not restored_pair:
                restored_pair = "EURUSD"
            
            current_time = datetime.now(timezone.utc)
            pressure_until = current_time + timedelta(hours=self.thresholds['pressure_release_duration_hours'])
            
            result = {
                'needed': True,
                'reason': f"Low signal volume: {count_12h}/12h, {count_24h}/24h",
                'tcs_flex': self.thresholds['tcs_flex_amount'],
                'restored_pair': restored_pair,
                'pressure_until': pressure_until.isoformat(),
                'triggered_at': current_time.isoformat()
            }
            
            logger.warning(f"🚨 PRESSURE RELEASE TRIGGERED: {result['reason']}")
            logger.info(f"🔧 TCS flex: -{result['tcs_flex']}, Restored: {restored_pair}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking pressure release: {e}")
            return {'needed': False}
    
    def apply_pressure_release(self, overrides: Dict[str, Any], pressure_config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply pressure release modifications to overrides"""
        try:
            if not pressure_config.get('needed'):
                return overrides
            
            # Add global pressure release config
            if 'global' not in overrides:
                overrides['global'] = {}
            
            overrides['global'].update({
                'pressure_release': True,
                'tcs_flex': pressure_config['tcs_flex'],
                'restored_pair': pressure_config['restored_pair'],
                'pressure_until': pressure_config['pressure_until'],
                'pressure_reason': pressure_config['reason']
            })
            
            # Remove restored pair from cooldown if it exists
            restored_pair_key = pressure_config['restored_pair'].lower()
            if restored_pair_key in overrides:
                del overrides[restored_pair_key]
                logger.info(f"🔓 PRESSURE RESTORED: {pressure_config['restored_pair']} removed from cooldown")
            
            # Reduce TCS penalties for all pairs by flex amount
            tcs_flex = pressure_config['tcs_flex']
            for symbol, config in overrides.items():
                if symbol in ['global', '_metadata']:
                    continue
                
                if 'tcs_penalty' in config:
                    original_penalty = config['tcs_penalty']
                    config['tcs_penalty'] = max(0, original_penalty - tcs_flex)
                    logger.info(f"🔧 TCS FLEX: {symbol.upper()} penalty {original_penalty} → {config['tcs_penalty']}")
            
            return overrides
            
        except Exception as e:
            logger.error(f"Error applying pressure release: {e}")
            return overrides
    
    def check_pressure_release_expiry(self, current_state: Dict[str, Any]) -> Dict[str, Any]:
        """Check if existing pressure release should be expired"""
        try:
            global_config = current_state.get('global', {})
            if not global_config.get('pressure_release'):
                return current_state
            
            pressure_until = global_config.get('pressure_until')
            if not pressure_until:
                return current_state
            
            try:
                pressure_time = datetime.fromisoformat(pressure_until.replace('Z', '+00:00'))
                current_time = datetime.now(timezone.utc)
                
                if current_time >= pressure_time:
                    # Remove pressure release
                    global_config.pop('pressure_release', None)
                    global_config.pop('tcs_flex', None)
                    global_config.pop('restored_pair', None)
                    global_config.pop('pressure_until', None)
                    global_config.pop('pressure_reason', None)
                    
                    logger.info(f"⏰ PRESSURE RELEASE EXPIRED - returning to normal filtering")
                    
            except (ValueError, TypeError):
                # Invalid date format, remove pressure release
                global_config.pop('pressure_release', None)
                global_config.pop('tcs_flex', None)
                global_config.pop('restored_pair', None)
                global_config.pop('pressure_until', None)
                global_config.pop('pressure_reason', None)
                
                logger.warning("🔧 Invalid pressure release timestamp - removed")
            
            return current_state
            
        except Exception as e:
            logger.error(f"Error checking pressure release expiry: {e}")
            return current_state
    
    def run_analysis(self) -> Dict[str, Any]:
        """Run complete analysis and generate overrides"""
        logger.info("Starting engineer analysis...")
        
        start_time = time.time()
        
        # First check and lift any expired cooldowns
        cooldown_results = self.check_and_lift_cooldowns()
        
        # Count recent signals for pressure release analysis
        signal_counts = self.count_recent_signals()
        
        # Check if pressure release is needed
        pressure_config = self.check_pressure_release_needed(signal_counts)
        
        # Then generate new overrides
        overrides = self.generate_overrides()
        
        # Apply pressure release if needed
        if pressure_config.get('needed'):
            overrides = self.apply_pressure_release(overrides, pressure_config)
        else:
            # Check if existing pressure release should expire
            overrides = self.check_pressure_release_expiry(overrides)
        
        analysis_time = time.time() - start_time
        
        # Save overrides
        success = self.save_overrides(overrides)
        
        if success:
            logger.info(f"Analysis completed in {analysis_time:.2f}s")
            # Add cooldown lift info to results
            if cooldown_results.get('total_lifted', 0) > 0:
                overrides['_cooldown_lifts'] = cooldown_results
            
            # Add pressure release info to results
            if pressure_config.get('needed'):
                overrides['_pressure_release'] = pressure_config
                
            # Add signal counts to metadata
            if '_metadata' not in overrides:
                overrides['_metadata'] = {}
            overrides['_metadata']['signal_counts'] = signal_counts
            
            return overrides
        else:
            logger.error("Failed to save overrides")
            return {}
    
    def get_current_overrides(self) -> Dict[str, Any]:
        """Read current overrides from state file"""
        try:
            if self.state_path.exists():
                with open(self.state_path, 'r') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            logger.error(f"Error reading current overrides: {e}")
            return {}

def main():
    """Main entry point - can run analysis on demand or in loop"""
    agent = EngineerAgent()
    
    import argparse
    parser = argparse.ArgumentParser(description='Engineer Agent - Adaptive Signal Optimization')
    parser.add_argument('--loop', action='store_true', help='Run continuously every 5 minutes')
    parser.add_argument('--interval', type=int, default=300, help='Loop interval in seconds (default: 300)')
    parser.add_argument('--check-cooldowns', action='store_true', help='Only check and lift cooldowns (no full analysis)')
    
    args = parser.parse_args()
    
    try:
        if args.check_cooldowns:
            # Only check cooldowns
            print("🔍 Checking cooldowns...")
            cooldown_results = agent.check_and_lift_cooldowns()
            
            lifted_count = cooldown_results.get('total_lifted', 0)
            if lifted_count > 0:
                print(f"\n🔓 Cooldowns Lifted: {lifted_count}")
                for lift in cooldown_results.get('cooldowns_lifted', []):
                    print(f"   {lift['symbol']}: {lift['reason']}")
            else:
                print("   No cooldowns to lift")
                
        elif args.loop:
            logger.info(f"Starting continuous analysis loop (every {args.interval}s)")
            while True:
                agent.run_analysis()
                logger.info(f"Waiting {args.interval}s until next analysis...")
                time.sleep(args.interval)
        else:
            # Run once
            overrides = agent.run_analysis()
            
            # Print cooldown lifts if any
            cooldown_lifts = overrides.get('_cooldown_lifts', {})
            lifted_count = cooldown_lifts.get('total_lifted', 0)
            if lifted_count > 0:
                print(f"\n🔓 Cooldowns Lifted: {lifted_count}")
                for lift in cooldown_lifts.get('cooldowns_lifted', []):
                    print(f"   {lift['symbol']}: {lift['reason']}")
            
            # Print pressure release if any
            pressure_release = overrides.get('_pressure_release', {})
            if pressure_release.get('needed'):
                print(f"\n🚨 Pressure Release Active:")
                print(f"   Reason: {pressure_release.get('reason')}")
                print(f"   TCS Flex: -{pressure_release.get('tcs_flex')}")
                print(f"   Restored Pair: {pressure_release.get('restored_pair')}")
                print(f"   Until: {pressure_release.get('pressure_until', '').split('T')[0]}")
            
            # Print signal counts
            signal_counts = overrides.get('_metadata', {}).get('signal_counts', {})
            if signal_counts:
                print(f"\n📊 Signal Volume:")
                print(f"   Last 12h: {signal_counts.get('12h', 0)}")
                print(f"   Last 24h: {signal_counts.get('24h', 0)}")
            
            # Print summary
            pair_count = len([k for k in overrides.keys() if k not in ['global', '_metadata', '_cooldown_lifts', '_pressure_release']])
            print(f"\n📋 Analysis Summary:")
            print(f"   Pair overrides: {pair_count}")
            print(f"   Global overrides: {len(overrides.get('global', {}))}")
            print(f"   Outcomes analyzed: {overrides.get('_metadata', {}).get('total_outcomes_analyzed', 0)}")
            
            if pair_count > 0:
                print(f"\n⚠️  Active Overrides:")
                for symbol, override in overrides.items():
                    if symbol not in ['global', '_metadata', '_cooldown_lifts', '_pressure_release']:
                        reason = override.get('reason', 'No reason specified')
                        print(f"   {symbol.upper()}: {reason}")
    
    except KeyboardInterrupt:
        logger.info("Received interrupt signal - shutting down")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()