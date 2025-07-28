#!/usr/bin/env python3
"""
Live Performance Tracking System for BITTEN
Tracks real-time performance, ghost mode efficiency, and provides /PERFORMANCE commands
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class SignalStatus(Enum):
    ACTIVE = "active"
    EXECUTED = "executed"
    EXPIRED = "expired"
    BLOCKED = "blocked"

class GhostMode(Enum):
    DISABLED = "disabled"
    ENTRY_DELAY = "entry_delay"
    LOT_VARIANCE = "lot_variance"
    TP_SL_OFFSET = "tp_sl_offset"
    STRATEGIC_SKIP = "strategic_skip"
    FULL_STEALTH = "full_stealth"

@dataclass
class LiveSignal:
    signal_id: str
    timestamp: datetime
    symbol: str
    direction: str
    tcs_score: int
    entry_price: float
    stop_loss: float
    take_profit: float
    tier_generated: str
    status: SignalStatus
    ghost_mode_applied: List[str]
    users_received: int = 0
    users_executed: int = 0
    win_rate_prediction: float = 0.0
    actual_result: Optional[str] = None
    profit_pips: Optional[float] = None
    
@dataclass
class LiveTradeExecution:
    execution_id: str
    signal_id: str
    user_id: str
    tier: str
    timestamp: datetime
    original_entry: float
    actual_entry: float
    original_lot: float
    actual_lot: float
    ghost_modifications: Dict
    result: Optional[str] = None
    profit_pips: Optional[float] = None
    profit_usd: Optional[float] = None
    
@dataclass
class PerformanceMetrics:
    total_signals_generated: int
    signals_last_24h: int
    win_rate_overall: float
    win_rate_24h: float
    ghost_mode_effectiveness: float
    avg_tcs_score: float
    tier_distribution: Dict[str, int]
    top_performing_pairs: List[Tuple[str, float]]

class LivePerformanceTracker:
    """Tracks live performance and ghost mode effectiveness"""
    
    def __init__(self, db_path: str = "data/live_performance.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize the performance tracking database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS live_signals (
                    signal_id TEXT PRIMARY KEY,
                    timestamp TIMESTAMP,
                    symbol TEXT,
                    direction TEXT,
                    tcs_score INTEGER,
                    entry_price REAL,
                    stop_loss REAL,
                    take_profit REAL,
                    tier_generated TEXT,
                    status TEXT,
                    ghost_mode_applied TEXT,
                    users_received INTEGER DEFAULT 0,
                    users_executed INTEGER DEFAULT 0,
                    win_rate_prediction REAL,
                    actual_result TEXT,
                    profit_pips REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS live_executions (
                    execution_id TEXT PRIMARY KEY,
                    signal_id TEXT,
                    user_id TEXT,
                    tier TEXT,
                    timestamp TIMESTAMP,
                    original_entry REAL,
                    actual_entry REAL,
                    original_lot REAL,
                    actual_lot REAL,
                    ghost_modifications TEXT,
                    result TEXT,
                    profit_pips REAL,
                    profit_usd REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (signal_id) REFERENCES live_signals (signal_id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ghost_mode_log (
                    log_id TEXT PRIMARY KEY,
                    signal_id TEXT,
                    user_id TEXT,
                    ghost_action TEXT,
                    original_value REAL,
                    modified_value REAL,
                    effectiveness_score REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_signals_timestamp 
                ON live_signals(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_executions_timestamp 
                ON live_executions(timestamp)
            """)
            
    def track_signal_generation(self, signal: LiveSignal) -> bool:
        """Track a new signal generation with ghost mode applied"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO live_signals (
                        signal_id, timestamp, symbol, direction, tcs_score,
                        entry_price, stop_loss, take_profit, tier_generated,
                        status, ghost_mode_applied, win_rate_prediction
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    signal.signal_id,
                    signal.timestamp,
                    signal.symbol,
                    signal.direction,
                    signal.tcs_score,
                    signal.entry_price,
                    signal.stop_loss,
                    signal.take_profit,
                    signal.tier_generated,
                    signal.status.value,
                    json.dumps(signal.ghost_mode_applied),
                    signal.win_rate_prediction
                ))
                
            logger.info(f"Tracked signal generation: {signal.signal_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking signal: {e}")
            return False
    
    def track_trade_execution(self, execution: LiveTradeExecution) -> bool:
        """Track a trade execution with ghost mode modifications"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO live_executions (
                        execution_id, signal_id, user_id, tier, timestamp,
                        original_entry, actual_entry, original_lot, actual_lot,
                        ghost_modifications, result, profit_pips, profit_usd
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    execution.execution_id,
                    execution.signal_id,
                    execution.user_id,
                    execution.tier,
                    execution.timestamp,
                    execution.original_entry,
                    execution.actual_entry,
                    execution.original_lot,
                    execution.actual_lot,
                    json.dumps(execution.ghost_modifications),
                    execution.result,
                    execution.profit_pips,
                    execution.profit_usd
                ))
                
                # Update signal user counts
                conn.execute("""
                    UPDATE live_signals 
                    SET users_executed = users_executed + 1
                    WHERE signal_id = ?
                """, (execution.signal_id,))
                
            logger.info(f"Tracked trade execution: {execution.execution_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking execution: {e}")
            return False
    
    def log_ghost_mode_action(self, signal_id: str, user_id: str, action: str, 
                            original_value: float, modified_value: float) -> bool:
        """Log individual ghost mode actions for analysis"""
        try:
            effectiveness_score = self._calculate_ghost_effectiveness(
                action, original_value, modified_value
            )
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO ghost_mode_log (
                        log_id, signal_id, user_id, ghost_action,
                        original_value, modified_value, effectiveness_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"{signal_id}_{user_id}_{action}_{datetime.now().strftime('%H%M%S')}",
                    signal_id,
                    user_id,
                    action,
                    original_value,
                    modified_value,
                    effectiveness_score
                ))
                
            return True
            
        except Exception as e:
            logger.error(f"Error logging ghost mode action: {e}")
            return False
    
    def _calculate_ghost_effectiveness(self, action: str, original: float, modified: float) -> float:
        """Calculate effectiveness score for ghost mode actions"""
        if action == "entry_delay":
            # Delay effectiveness based on randomness (0-12 seconds ideal)
            return min(1.0, modified / 12.0) if modified > 0 else 0.0
        elif action == "lot_variance":
            # Variance effectiveness (5-12% ideal)
            variance_pct = abs((modified - original) / original) * 100
            return min(1.0, variance_pct / 12.0) if variance_pct >= 5 else variance_pct / 5.0
        elif action == "tp_sl_offset":
            # TP/SL offset effectiveness (1-3 pips ideal)
            offset_pips = abs(modified - original) * 10000  # Assuming 4-digit precision
            return min(1.0, offset_pips / 3.0) if offset_pips >= 1 else offset_pips
        else:
            return 1.0  # Default effectiveness for other actions
    
    def get_live_performance_metrics(self, hours_back: int = 24) -> PerformanceMetrics:
        """Get comprehensive performance metrics for specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        with sqlite3.connect(self.db_path) as conn:
            # Total signals
            total_signals = conn.execute(
                "SELECT COUNT(*) FROM live_signals"
            ).fetchone()[0]
            
            # Recent signals
            recent_signals = conn.execute(
                "SELECT COUNT(*) FROM live_signals WHERE timestamp >= ?",
                (cutoff_time,)
            ).fetchone()[0]
            
            # Overall win rate
            win_rate_data = conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN actual_result = 'WIN' THEN 1 ELSE 0 END) as wins
                FROM live_signals 
                WHERE actual_result IS NOT NULL
            """).fetchone()
            
            overall_win_rate = (win_rate_data[1] / win_rate_data[0] * 100) if win_rate_data[0] > 0 else 0.0
            
            # Recent win rate
            recent_win_data = conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN actual_result = 'WIN' THEN 1 ELSE 0 END) as wins
                FROM live_signals 
                WHERE actual_result IS NOT NULL AND timestamp >= ?
            """, (cutoff_time,)).fetchone()
            
            recent_win_rate = (recent_win_data[1] / recent_win_data[0] * 100) if recent_win_data[0] > 0 else 0.0
            
            # Ghost mode effectiveness
            ghost_effectiveness = conn.execute("""
                SELECT AVG(effectiveness_score) 
                FROM ghost_mode_log 
                WHERE timestamp >= ?
            """, (cutoff_time,)).fetchone()[0] or 0.0
            
            # Average TCS
            avg_tcs = conn.execute("""
                SELECT AVG(tcs_score) 
                FROM live_signals 
                WHERE timestamp >= ?
            """, (cutoff_time,)).fetchone()[0] or 0.0
            
            # Tier distribution
            tier_dist = conn.execute("""
                SELECT tier_generated, COUNT(*) 
                FROM live_signals 
                WHERE timestamp >= ?
                GROUP BY tier_generated
            """, (cutoff_time,)).fetchall()
            
            tier_distribution = {tier: count for tier, count in tier_dist}
            
            # Top performing pairs
            top_pairs = conn.execute("""
                SELECT 
                    symbol,
                    AVG(CASE WHEN actual_result = 'WIN' THEN 1.0 ELSE 0.0 END) * 100 as win_rate
                FROM live_signals 
                WHERE actual_result IS NOT NULL AND timestamp >= ?
                GROUP BY symbol
                HAVING COUNT(*) >= 3
                ORDER BY win_rate DESC
                LIMIT 5
            """, (cutoff_time,)).fetchall()
            
        return PerformanceMetrics(
            total_signals_generated=total_signals,
            signals_last_24h=recent_signals,
            win_rate_overall=overall_win_rate,
            win_rate_24h=recent_win_rate,
            ghost_mode_effectiveness=ghost_effectiveness * 100,
            avg_tcs_score=avg_tcs,
            tier_distribution=tier_distribution,
            top_performing_pairs=top_pairs
        )
    
    def get_recent_signals(self, limit: int = 10) -> List[Dict]:
        """Get recent signals with their performance"""
        with sqlite3.connect(self.db_path) as conn:
            signals = conn.execute("""
                SELECT 
                    signal_id, timestamp, symbol, direction, tcs_score,
                    entry_price, stop_loss, take_profit, status,
                    users_executed, actual_result, profit_pips
                FROM live_signals 
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,)).fetchall()
            
        return [
            {
                'signal_id': s[0],
                'timestamp': s[1],
                'symbol': s[2],
                'direction': s[3],
                'tcs_score': s[4],
                'entry_price': s[5],
                'stop_loss': s[6],
                'take_profit': s[7],
                'status': s[8],
                'users_executed': s[9],
                'result': s[10],
                'profit_pips': s[11]
            }
            for s in signals
        ]
    
    def update_signal_result(self, signal_id: str, result: str, profit_pips: float) -> bool:
        """Update a signal with its actual trading result"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE live_signals 
                    SET actual_result = ?, profit_pips = ?
                    WHERE signal_id = ?
                """, (result, profit_pips, signal_id))
                
            logger.info(f"Updated signal result: {signal_id} -> {result}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating signal result: {e}")
            return False
    
    def get_ghost_mode_summary(self, hours_back: int = 24) -> Dict:
        """Get summary of ghost mode effectiveness"""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        with sqlite3.connect(self.db_path) as conn:
            ghost_summary = conn.execute("""
                SELECT 
                    ghost_action,
                    COUNT(*) as usage_count,
                    AVG(effectiveness_score) as avg_effectiveness,
                    MIN(effectiveness_score) as min_effectiveness,
                    MAX(effectiveness_score) as max_effectiveness
                FROM ghost_mode_log 
                WHERE timestamp >= ?
                GROUP BY ghost_action
                ORDER BY usage_count DESC
            """, (cutoff_time,)).fetchall()
            
        return {
            action: {
                'usage_count': count,
                'avg_effectiveness': avg_eff * 100,
                'min_effectiveness': min_eff * 100,
                'max_effectiveness': max_eff * 100
            }
            for action, count, avg_eff, min_eff, max_eff in ghost_summary
        }
    
    def get_true_win_rate(self, hours_back: int = 24, include_unfired: bool = True) -> Dict:
        """
        Get true win rate including unfired missions that would have been winners
        
        Args:
            hours_back: Hours to analyze
            include_unfired: Whether to include unfired but winning signals
            
        Returns:
            Dictionary with comprehensive win rate data including TCS bands
        """
        try:
            # Get fired signals win rate
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            with sqlite3.connect(self.db_path) as conn:
                # Fired signals
                fired_data = conn.execute("""
                    SELECT 
                        tcs_score,
                        COUNT(*) as total,
                        SUM(CASE WHEN actual_result = 'WIN' THEN 1 ELSE 0 END) as wins
                    FROM live_signals 
                    WHERE actual_result IS NOT NULL 
                    AND timestamp >= ?
                    AND users_executed > 0
                    GROUP BY (tcs_score / 5) * 5
                    ORDER BY tcs_score
                """, (cutoff_time,)).fetchall()
            
            fired_stats = {}
            total_fired = 0
            total_fired_wins = 0
            
            for tcs_band, total, wins in fired_data:
                tcs_range = f"{int(tcs_band)}-{int(tcs_band) + 4}"
                fired_stats[tcs_range] = {
                    'total': total,
                    'wins': wins,
                    'win_rate': (wins / total * 100) if total > 0 else 0.0
                }
                total_fired += total
                total_fired_wins += wins
            
            fired_win_rate = (total_fired_wins / total_fired * 100) if total_fired > 0 else 0.0
            
            # Get unfired but winning signals if requested
            unfired_stats = {}
            total_unfired_wins = 0
            total_unfired = 0
            
            if include_unfired:
                try:
                    from bitten_core.enhanced_ghost_tracker import enhanced_ghost_tracker
                    missed_summary = enhanced_ghost_tracker.get_missed_win_summary(hours_back)
                    
                    total_unfired = missed_summary.get('total_expired', 0)
                    total_unfired_wins = missed_summary.get('unfired_wins', 0)
                    
                    # Get TCS band breakdown from missed win log
                    unfired_stats = self._get_unfired_tcs_breakdown(hours_back)
                    
                except ImportError:
                    logger.warning("Enhanced ghost tracker not available for unfired analysis")
                except Exception as e:
                    logger.error(f"Error getting unfired analysis: {e}")
            
            # Calculate true win rate
            total_all_signals = total_fired + total_unfired
            total_all_wins = total_fired_wins + total_unfired_wins
            true_win_rate = (total_all_wins / total_all_signals * 100) if total_all_signals > 0 else 0.0
            
            # Combine TCS band data
            combined_tcs_bands = {}
            all_tcs_ranges = set(fired_stats.keys()) | set(unfired_stats.keys())
            
            for tcs_range in all_tcs_ranges:
                fired_data = fired_stats.get(tcs_range, {'total': 0, 'wins': 0, 'win_rate': 0.0})
                unfired_data = unfired_stats.get(tcs_range, {'total': 0, 'wins': 0, 'win_rate': 0.0})
                
                combined_total = fired_data['total'] + unfired_data['total']
                combined_wins = fired_data['wins'] + unfired_data['wins']
                combined_win_rate = (combined_wins / combined_total * 100) if combined_total > 0 else 0.0
                
                combined_tcs_bands[tcs_range] = {
                    'fired_total': fired_data['total'],
                    'fired_wins': fired_data['wins'],
                    'fired_win_rate': fired_data['win_rate'],
                    'unfired_total': unfired_data['total'],
                    'unfired_wins': unfired_data['wins'],
                    'unfired_win_rate': unfired_data['win_rate'],
                    'combined_total': combined_total,
                    'combined_wins': combined_wins,
                    'combined_win_rate': combined_win_rate
                }
            
            return {
                'period_hours': hours_back,
                'include_unfired': include_unfired,
                'fired_signals': {
                    'total': total_fired,
                    'wins': total_fired_wins,
                    'win_rate': fired_win_rate
                },
                'unfired_signals': {
                    'total': total_unfired,
                    'wins': total_unfired_wins,
                    'win_rate': (total_unfired_wins / total_unfired * 100) if total_unfired > 0 else 0.0
                },
                'true_performance': {
                    'total_signals': total_all_signals,
                    'total_wins': total_all_wins,
                    'true_win_rate': true_win_rate
                },
                'tcs_band_breakdown': combined_tcs_bands
            }
            
        except Exception as e:
            logger.error(f"Error calculating true win rate: {e}")
            return {'error': str(e)}
    
    def _get_unfired_tcs_breakdown(self, hours_back: int) -> Dict:
        """
        Get TCS band breakdown for unfired signals from missed win log
        
        Args:
            hours_back: Hours to analyze
            
        Returns:
            Dictionary with unfired signal TCS breakdown
        """
        try:
            missed_log_path = "/root/HydraX-v2/data/missed_win_log.json"
            
            if not os.path.exists(missed_log_path):
                return {}
            
            with open(missed_log_path, 'r') as f:
                missed_data = json.load(f)
            
            results = missed_data.get('results', [])
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            cutoff_timestamp = cutoff_time.timestamp()
            
            # Group by TCS bands
            tcs_bands = {}
            
            for result in results:
                # Check if within time window
                created_ts = result.get('created_timestamp', 0)
                if created_ts < cutoff_timestamp:
                    continue
                
                tcs_score = result.get('tcs_score', 0)
                tcs_band = (tcs_score // 5) * 5
                tcs_range = f"{int(tcs_band)}-{int(tcs_band) + 4}"
                
                if tcs_range not in tcs_bands:
                    tcs_bands[tcs_range] = {'total': 0, 'wins': 0, 'win_rate': 0.0}
                
                tcs_bands[tcs_range]['total'] += 1
                if result.get('result') == 'UNFIRED_WIN':
                    tcs_bands[tcs_range]['wins'] += 1
            
            # Calculate win rates
            for tcs_range, data in tcs_bands.items():
                if data['total'] > 0:
                    data['win_rate'] = (data['wins'] / data['total']) * 100
            
            return tcs_bands
            
        except Exception as e:
            logger.error(f"Error getting unfired TCS breakdown: {e}")
            return {}

# Global instance
live_tracker = LivePerformanceTracker()

def get_performance_command_response(hours_back: int = 24) -> str:
    """Generate formatted response for /PERFORMANCE command"""
    try:
        metrics = live_tracker.get_live_performance_metrics(hours_back)
        recent_signals = live_tracker.get_recent_signals(5)
        ghost_summary = live_tracker.get_ghost_mode_summary(hours_back)
        
        response = f"""
🎯 **BITTEN LIVE PERFORMANCE REPORT**
⏰ **Period**: Last {hours_back} hours

📊 **SIGNAL METRICS:**
• Total Signals Generated: **{metrics.total_signals_generated:}**
• Signals Last {hours_back}h: **{metrics.signals_last_24h}**
• Average TCS Score: **{metrics.avg_tcs_score:.1f}%**

🎲 **WIN RATE PERFORMANCE:**
• Overall Win Rate: **{metrics.win_rate_overall:.1f}%**
• Last {hours_back}h Win Rate: **{metrics.win_rate_24h:.1f}%**
• Target: **85%+** {'✅' if metrics.win_rate_24h >= 85 else '⚠️'}

👻 **GHOST MODE EFFECTIVENESS:**
• Overall Stealth Score: **{metrics.ghost_mode_effectiveness:.1f}%**
• Protection Status: **{'ACTIVE' if metrics.ghost_mode_effectiveness > 50 else 'NEEDS ATTENTION'}**

🏆 **TIER DISTRIBUTION:**"""
        
        for tier, count in metrics.tier_distribution.items():
            response += f"\n• {tier.upper()}: **{count}** signals"
        
        response += f"\n\n📈 **TOP PERFORMING PAIRS:**"
        for symbol, win_rate in metrics.top_performing_pairs[:3]:
            response += f"\n• {symbol}: **{win_rate:.1f}%** win rate"
        
        response += f"\n\n🕐 **RECENT SIGNALS:**"
        for signal in recent_signals[:3]:
            status_emoji = "✅" if signal['result'] == 'WIN' else "❌" if signal['result'] == 'LOSS' else "⏳"
            response += f"\n• {signal['symbol']} {signal['direction']} | TCS {signal['tcs_score']}% {status_emoji}"
        
        if ghost_summary:
            response += f"\n\n👻 **GHOST MODE ACTIVITY:**"
            for action, data in list(ghost_summary.items())[:3]:
                response += f"\n• {action.title()}: {data['usage_count']} uses, {data['avg_effectiveness']:.1f}% effective"
        
        response += f"\n\n🛡️ **System Status**: {'🟢 OPERATIONAL' if metrics.win_rate_24h >= 75 else '🟡 MONITORING'}"
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating performance report: {e}")
        return f"❌ Error generating performance report: {str(e)}"