#!/usr/bin/env python3
"""
Pattern Optimizer v2 - Automatic Pattern Performance Management
Monitors and optimizes pattern performance in real-time
"""

import sqlite3
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import threading

class PatternOptimizerV2:
    """Auto-optimize pattern performance based on real results"""
    
    def __init__(self):
        # Logging
        self.logger = logging.getLogger('PatternOptimizer')
        self.logger.setLevel(logging.INFO)
        fh = logging.FileHandler('pattern_optimizer_v2.log')
        fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(fh)
        
        # Database
        self.db_path = '/root/HydraX-v2/bitten.db'
        
        # Pattern status tracking
        self.pattern_status = {
            'LIQUIDITY_SWEEP_REVERSAL': 'ACTIVE',
            'SUPPORT_RESISTANCE_BOUNCE': 'ACTIVE',
            'BREAKOUT_MOMENTUM': 'ACTIVE',
            'FAIR_VALUE_GAP_FILL': 'ACTIVE',
            'VOLUME_CLIMAX_REVERSAL': 'ACTIVE'
        }
        
        # Performance thresholds
        self.disable_threshold = 0.40  # Disable if win rate < 40% after 20 trades
        self.promote_threshold = 0.70  # Promote if win rate > 70% after 20 trades
        self.min_trades_for_decision = 20
        
        # Position sizing multipliers based on performance
        self.performance_multipliers = {}
        
        # Session-specific enabling
        self.session_pattern_config = self.load_session_config()
        
        # Optimization decisions log
        self.optimization_log = []
        
        self.logger.info("Pattern Optimizer v2 initialized")
    
    def load_session_config(self) -> Dict:
        """Load session-specific pattern configuration"""
        return {
            'ASIAN': {
                'enabled_patterns': [
                    'SUPPORT_RESISTANCE_BOUNCE',
                    'FAIR_VALUE_GAP_FILL'
                ],
                'disabled_patterns': ['BREAKOUT_MOMENTUM']
            },
            'LONDON': {
                'enabled_patterns': [
                    'LIQUIDITY_SWEEP_REVERSAL',
                    'BREAKOUT_MOMENTUM',
                    'VOLUME_CLIMAX_REVERSAL'
                ],
                'disabled_patterns': []
            },
            'NY': {
                'enabled_patterns': [
                    'BREAKOUT_MOMENTUM',
                    'VOLUME_CLIMAX_REVERSAL',
                    'LIQUIDITY_SWEEP_REVERSAL'
                ],
                'disabled_patterns': []
            },
            'OVERLAP': {
                'enabled_patterns': 'ALL',  # All patterns active
                'disabled_patterns': []
            },
            'OFF_HOURS': {
                'enabled_patterns': ['SUPPORT_RESISTANCE_BOUNCE'],
                'disabled_patterns': [
                    'BREAKOUT_MOMENTUM',
                    'VOLUME_CLIMAX_REVERSAL'
                ]
            }
        }
    
    def analyze_pattern_performance(self) -> Dict[str, Dict]:
        """Analyze performance of each pattern"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get performance stats for each pattern
            cursor.execute("""
                SELECT 
                    pattern_type,
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN achieved_rr > 0 THEN 1 ELSE 0 END) as wins,
                    AVG(achieved_rr) as avg_rr,
                    AVG(efficiency_score) as avg_efficiency,
                    MAX(entry_time) as last_trade_time
                FROM signal_performance_v2
                WHERE exit_time IS NOT NULL
                GROUP BY pattern_type
            """)
            
            results = cursor.fetchall()
            
            performance = {}
            for row in results:
                pattern, total, wins, avg_rr, avg_efficiency, last_trade = row
                win_rate = (wins / total) if total > 0 else 0
                
                performance[pattern] = {
                    'total_trades': total,
                    'wins': wins,
                    'win_rate': win_rate,
                    'avg_rr': avg_rr or 0,
                    'avg_efficiency': avg_efficiency or 0,
                    'last_trade_time': last_trade,
                    'status': self.pattern_status.get(pattern, 'UNKNOWN')
                }
            
            # Get per-symbol performance
            cursor.execute("""
                SELECT 
                    pattern_type,
                    symbol,
                    COUNT(*) as total,
                    SUM(CASE WHEN achieved_rr > 0 THEN 1 ELSE 0 END) as wins
                FROM signal_performance_v2
                WHERE exit_time IS NOT NULL
                GROUP BY pattern_type, symbol
                HAVING COUNT(*) >= 5
            """)
            
            symbol_performance = {}
            for row in cursor.fetchall():
                pattern, symbol, total, wins = row
                if pattern not in symbol_performance:
                    symbol_performance[pattern] = {}
                symbol_performance[pattern][symbol] = {
                    'total': total,
                    'win_rate': (wins / total) if total > 0 else 0
                }
            
            conn.close()
            
            # Add symbol performance to main performance dict
            for pattern in performance:
                performance[pattern]['symbol_performance'] = symbol_performance.get(pattern, {})
            
            return performance
            
        except Exception as e:
            self.logger.error(f"Error analyzing performance: {e}")
            return {}
    
    def make_optimization_decisions(self, performance: Dict[str, Dict]) -> List[Dict]:
        """Make optimization decisions based on performance"""
        decisions = []
        
        for pattern, stats in performance.items():
            total_trades = stats['total_trades']
            win_rate = stats['win_rate']
            avg_rr = stats['avg_rr']
            current_status = stats['status']
            
            # Only make decisions after minimum trades
            if total_trades < self.min_trades_for_decision:
                continue
            
            # Disable poor performers
            if win_rate < self.disable_threshold and current_status == 'ACTIVE':
                self.pattern_status[pattern] = 'DISABLED'
                decision = {
                    'pattern': pattern,
                    'action': 'DISABLE',
                    'reason': f'Win rate {win_rate:.1%} below {self.disable_threshold:.0%}',
                    'stats': stats,
                    'timestamp': datetime.now().isoformat()
                }
                decisions.append(decision)
                self.logger.warning(f"DISABLING {pattern}: Win rate {win_rate:.1%} after {total_trades} trades")
            
            # Promote high performers
            elif win_rate > self.promote_threshold and current_status == 'ACTIVE':
                self.pattern_status[pattern] = 'PROMOTED'
                self.performance_multipliers[pattern] = 1.5  # 50% larger positions
                decision = {
                    'pattern': pattern,
                    'action': 'PROMOTE',
                    'reason': f'Win rate {win_rate:.1%} above {self.promote_threshold:.0%}',
                    'stats': stats,
                    'timestamp': datetime.now().isoformat()
                }
                decisions.append(decision)
                self.logger.info(f"PROMOTING {pattern}: Win rate {win_rate:.1%} after {total_trades} trades")
            
            # Re-enable if performance improves
            elif win_rate > 0.50 and current_status == 'DISABLED':
                self.pattern_status[pattern] = 'TESTING'
                decision = {
                    'pattern': pattern,
                    'action': 'RE-ENABLE',
                    'reason': f'Win rate improved to {win_rate:.1%}',
                    'stats': stats,
                    'timestamp': datetime.now().isoformat()
                }
                decisions.append(decision)
                self.logger.info(f"RE-ENABLING {pattern}: Win rate improved to {win_rate:.1%}")
            
            # Analyze per-symbol performance
            symbol_perf = stats.get('symbol_performance', {})
            for symbol, sym_stats in symbol_perf.items():
                if sym_stats['total'] >= 10:
                    if sym_stats['win_rate'] < 0.30:
                        decision = {
                            'pattern': pattern,
                            'symbol': symbol,
                            'action': 'DISABLE_PAIR',
                            'reason': f'{symbol} win rate {sym_stats["win_rate"]:.1%} too low',
                            'timestamp': datetime.now().isoformat()
                        }
                        decisions.append(decision)
                    elif sym_stats['win_rate'] > 0.75:
                        decision = {
                            'pattern': pattern,
                            'symbol': symbol,
                            'action': 'BOOST_PAIR',
                            'reason': f'{symbol} win rate {sym_stats["win_rate"]:.1%} excellent',
                            'timestamp': datetime.now().isoformat()
                        }
                        decisions.append(decision)
        
        return decisions
    
    def apply_session_rules(self) -> Dict:
        """Apply session-specific pattern enabling/disabling"""
        hour = datetime.utcnow().hour
        
        # Determine current session
        if 7 <= hour < 16:
            if 12 <= hour < 16:
                session = 'OVERLAP'
            else:
                session = 'LONDON'
        elif 12 <= hour < 21:
            session = 'NY'
        elif hour >= 23 or hour < 8:
            session = 'ASIAN'
        else:
            session = 'OFF_HOURS'
        
        # Get session config
        config = self.session_pattern_config.get(session, {})
        enabled = config.get('enabled_patterns', [])
        disabled = config.get('disabled_patterns', [])
        
        session_status = {}
        
        for pattern in self.pattern_status:
            if enabled == 'ALL':
                session_status[pattern] = True
            elif pattern in disabled:
                session_status[pattern] = False
            elif pattern in enabled:
                session_status[pattern] = True
            else:
                session_status[pattern] = False
        
        return {
            'session': session,
            'pattern_status': session_status,
            'timestamp': datetime.now().isoformat()
        }
    
    def calculate_position_multiplier(self, pattern: str, symbol: str) -> float:
        """Calculate position size multiplier based on performance"""
        base_multiplier = 1.0
        
        # Pattern performance multiplier
        if pattern in self.performance_multipliers:
            base_multiplier *= self.performance_multipliers[pattern]
        
        # Status-based multiplier
        status = self.pattern_status.get(pattern, 'ACTIVE')
        if status == 'PROMOTED':
            base_multiplier *= 1.2
        elif status == 'TESTING':
            base_multiplier *= 0.5
        elif status == 'DISABLED':
            return 0  # No position
        
        # Cap at 2x
        return min(2.0, base_multiplier)
    
    def save_optimization_state(self):
        """Save current optimization state to file"""
        state = {
            'pattern_status': self.pattern_status,
            'performance_multipliers': self.performance_multipliers,
            'optimization_log': self.optimization_log[-100:],  # Keep last 100 decisions
            'timestamp': datetime.now().isoformat()
        }
        
        with open('/root/HydraX-v2/pattern_optimization_state.json', 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_optimization_state(self):
        """Load previous optimization state"""
        try:
            with open('/root/HydraX-v2/pattern_optimization_state.json', 'r') as f:
                state = json.load(f)
                self.pattern_status = state.get('pattern_status', self.pattern_status)
                self.performance_multipliers = state.get('performance_multipliers', {})
                self.optimization_log = state.get('optimization_log', [])
                self.logger.info("Loaded previous optimization state")
        except FileNotFoundError:
            self.logger.info("No previous state found, starting fresh")
        except Exception as e:
            self.logger.error(f"Error loading state: {e}")
    
    def generate_report(self) -> str:
        """Generate optimization report"""
        performance = self.analyze_pattern_performance()
        
        report = []
        report.append("="*60)
        report.append("PATTERN OPTIMIZATION REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("="*60)
        
        # Overall stats
        total_trades = sum(p['total_trades'] for p in performance.values())
        total_wins = sum(p['wins'] for p in performance.values())
        overall_win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
        
        report.append(f"\nOVERALL PERFORMANCE:")
        report.append(f"Total Trades: {total_trades}")
        report.append(f"Win Rate: {overall_win_rate:.1f}%")
        
        # Pattern-specific stats
        report.append(f"\nPATTERN PERFORMANCE:")
        report.append("-"*60)
        
        for pattern, stats in sorted(performance.items(), 
                                    key=lambda x: x[1].get('win_rate', 0), 
                                    reverse=True):
            status = self.pattern_status.get(pattern, 'UNKNOWN')
            trades = stats['total_trades']
            win_rate = stats['win_rate'] * 100
            avg_rr = stats['avg_rr']
            
            report.append(f"\n{pattern}")
            report.append(f"  Status: {status}")
            report.append(f"  Trades: {trades}")
            report.append(f"  Win Rate: {win_rate:.1f}%")
            report.append(f"  Avg R:R: {avg_rr:.2f}")
            
            # Top performing symbols
            symbol_perf = stats.get('symbol_performance', {})
            if symbol_perf:
                top_symbols = sorted(symbol_perf.items(), 
                                   key=lambda x: x[1]['win_rate'], 
                                   reverse=True)[:3]
                if top_symbols:
                    top_pairs = ', '.join([f"{s[0]} ({s[1]['win_rate']*100:.0f}%)" for s in top_symbols])
                    report.append(f"  Top Pairs: {top_pairs}")
        
        # Recent decisions
        if self.optimization_log:
            report.append(f"\nRECENT OPTIMIZATION DECISIONS:")
            report.append("-"*60)
            for decision in self.optimization_log[-5:]:
                report.append(f"{decision['timestamp']}: {decision['action']} {decision.get('pattern', '')} - {decision['reason']}")
        
        report.append("\n" + "="*60)
        
        return "\n".join(report)
    
    def run_optimization_cycle(self):
        """Run one optimization cycle"""
        try:
            # Analyze current performance
            performance = self.analyze_pattern_performance()
            
            # Make optimization decisions
            decisions = self.make_optimization_decisions(performance)
            
            # Log decisions
            self.optimization_log.extend(decisions)
            
            # Apply session rules
            session_rules = self.apply_session_rules()
            
            # Save state
            self.save_optimization_state()
            
            # Generate and log report
            if decisions:
                report = self.generate_report()
                self.logger.info(f"Optimization cycle complete:\n{report}")
                
                # Save report to file
                with open('/root/HydraX-v2/optimization_report.txt', 'w') as f:
                    f.write(report)
            
            return {
                'decisions': decisions,
                'session_rules': session_rules,
                'performance': performance
            }
            
        except Exception as e:
            self.logger.error(f"Error in optimization cycle: {e}")
            return {}
    
    def run(self):
        """Main optimization loop"""
        self.logger.info("Starting pattern optimizer...")
        
        # Load previous state
        self.load_optimization_state()
        
        # Run optimization every 5 minutes
        while True:
            try:
                # Run optimization
                results = self.run_optimization_cycle()
                
                # Log summary
                if results.get('decisions'):
                    self.logger.info(f"Made {len(results['decisions'])} optimization decisions")
                
                # Wait 5 minutes
                time.sleep(300)
                
            except KeyboardInterrupt:
                self.logger.info("Optimizer stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                time.sleep(60)


if __name__ == "__main__":
    optimizer = PatternOptimizerV2()
    optimizer.run()