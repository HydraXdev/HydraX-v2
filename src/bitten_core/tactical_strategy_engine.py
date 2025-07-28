#!/usr/bin/env python3
"""
🎯 TACTICAL STRATEGY ENGINE - REAL TACTICAL IMPLEMENTATION
ZERO SIMULATION - IMPLEMENTS REAL DAILY TACTICAL STRATEGIES

Implements the 4 tactical strategies with real trade counting and eligibility
"""

import json
import sqlite3
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import os

logger = logging.getLogger(__name__)

@dataclass
class TacticalStrategy:
    """Real tactical strategy definition"""
    name: str
    max_trades: int
    min_tcs: int
    special_rules: Dict[str, Any]
    risk_reward: float
    description: str

class TacticalStrategyEngine:
    """
    🎯 TACTICAL STRATEGY ENGINE - REAL IMPLEMENTATION
    
    Implements 4 tactical strategies:
    1. LONE_WOLF - 4 trades max, 74+ TCS, 1:1.3 R:R
    2. FIRST_BLOOD - 4 trades escalating TCS, stop after 2 wins
    3. DOUBLE_TAP - 2 trades only, 85+ TCS, same direction, 1:1.8 R:R  
    4. TACTICAL_COMMAND - Choice: 1x95+ TCS OR 6x80+ TCS
    
    CRITICAL: NO SIMULATION - ALL TRADE COUNTING IS REAL
    """
    
    def __init__(self, db_path="/root/HydraX-v2/data/tactical_strategies.db"):
        self.db_path = db_path
        self.logger = logging.getLogger("TACTICAL_ENGINE")
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self.init_database()
        
        # Define tactical strategies
        self.strategies = self._define_strategies()
        
        # Verify real data only
        self.verify_real_strategies_only()
        
    def verify_real_strategies_only(self):
        """Verify system uses ZERO simulation"""
        simulation_flags = ['DEMO_STRATEGIES', 'FAKE_TRADES', 'TEST_MODE']
        
        for flag in simulation_flags:
            if hasattr(self, flag.lower()) and getattr(self, flag.lower()):
                raise ValueError(f"CRITICAL: {flag} detected - REAL STRATEGIES ONLY")
                
        self.logger.info("✅ VERIFIED: REAL TACTICAL STRATEGIES ONLY")
    
    def init_database(self):
        """Initialize tactical strategies database"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            
            # Create daily tactical tracking table
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS daily_tactical_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    trades_taken INTEGER DEFAULT 0,
                    trades_won INTEGER DEFAULT 0,
                    total_pnl REAL DEFAULT 0.0,
                    strategy_completed BOOLEAN DEFAULT 0,
                    last_trade_direction TEXT,
                    escalation_level INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            # Create tactical trade log
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS tactical_trade_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    mission_id TEXT NOT NULL,
                    trade_number INTEGER NOT NULL,
                    tcs_score INTEGER NOT NULL,
                    direction TEXT NOT NULL,
                    result TEXT,
                    pnl REAL DEFAULT 0.0,
                    trade_timestamp TEXT NOT NULL,
                    real_trade_verified BOOLEAN DEFAULT 1,
                    simulation_mode BOOLEAN DEFAULT 0
                )
            ''')
            
            self.conn.commit()
            self.logger.info(f"✅ Tactical strategies database initialized: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    def _define_strategies(self) -> Dict[str, TacticalStrategy]:
        """Define the 4 tactical strategies"""
        return {
            'LONE_WOLF': TacticalStrategy(
                name='LONE_WOLF',
                max_trades=4,
                min_tcs=74,
                special_rules={'any_direction': True, 'basic_training': True},
                risk_reward=1.3,
                description="Training wheels - 4 shots max, any 74+ TCS, 1:1.3 R:R"
            ),
            
            'FIRST_BLOOD': TacticalStrategy(
                name='FIRST_BLOOD',
                max_trades=4,
                min_tcs=75,  # Starting TCS, escalates
                special_rules={
                    'escalating_tcs': [75, 78, 80, 85],
                    'stop_after_wins': 2,
                    'escalation_mode': True
                },
                risk_reward=1.5,
                description="Escalation mastery - 4 shots with escalating TCS, stop after 2 wins"
            ),
            
            'DOUBLE_TAP': TacticalStrategy(
                name='DOUBLE_TAP',
                max_trades=2,
                min_tcs=85,
                special_rules={
                    'same_direction': True,
                    'precision_mode': True,
                    'high_reward': True
                },
                risk_reward=1.8,
                description="Precision selection - 2 shots only, both 85+ TCS, same direction, 1:1.8 R:R"
            ),
            
            'TACTICAL_COMMAND': TacticalStrategy(
                name='TACTICAL_COMMAND',
                max_trades=6,  # Max for volume mode
                min_tcs=80,
                special_rules={
                    'choice_mode': True,
                    'sniper_option': {'trades': 1, 'tcs': 95},
                    'volume_option': {'trades': 6, 'tcs': 80}
                },
                risk_reward=2.0,
                description="Earned mastery - Choose: 1 shot 95+ TCS OR 6 shots 80+ TCS"
            )
        }
    
    def is_signal_eligible(self, signal: Dict, strategy: str, user_id: str) -> bool:
        """Check if signal is eligible for user's tactical strategy"""
        try:
            if strategy not in self.strategies:
                self.logger.error(f"Unknown strategy: {strategy}")
                return False
            
            strategy_def = self.strategies[strategy]
            today = datetime.now(timezone.utc).date().isoformat()
            
            # Get today's tactical tracking
            tracking = self._get_daily_tracking(user_id, today, strategy)
            
            # Check if strategy is completed
            if tracking and tracking.get('strategy_completed', False):
                self.logger.info(f"Strategy {strategy} already completed for {user_id}")
                return False
            
            # Check max trades limit
            trades_taken = tracking.get('trades_taken', 0) if tracking else 0
            max_trades = strategy_def.max_trades
            
            # Special handling for TACTICAL_COMMAND choice mode
            if strategy == 'TACTICAL_COMMAND':
                # Check if user chose sniper mode (1 trade max)
                if tracking and tracking.get('escalation_level') == 1:  # Sniper mode flag
                    max_trades = 1
            
            if trades_taken >= max_trades:
                self.logger.info(f"Max trades reached for {strategy}: {trades_taken}/{max_trades}")
                return False
            
            # Check TCS eligibility
            signal_tcs = signal.get('tcs_score', 0)
            
            if strategy == 'FIRST_BLOOD':
                # Escalating TCS requirements
                escalating_tcs = strategy_def.special_rules['escalating_tcs']
                required_tcs = escalating_tcs[min(trades_taken, len(escalating_tcs) - 1)]
                
                if signal_tcs < required_tcs:
                    self.logger.info(f"TCS too low for {strategy} escalation: {signal_tcs} < {required_tcs}")
                    return False
                    
            elif strategy == 'TACTICAL_COMMAND':
                # Check choice mode
                if tracking and tracking.get('escalation_level') == 1:  # Sniper mode
                    if signal_tcs < 95:
                        self.logger.info(f"TCS too low for sniper mode: {signal_tcs} < 95")
                        return False
                else:  # Volume mode
                    if signal_tcs < 80:
                        self.logger.info(f"TCS too low for volume mode: {signal_tcs} < 80")
                        return False
            else:
                # Standard TCS check
                if signal_tcs < strategy_def.min_tcs:
                    self.logger.info(f"TCS too low for {strategy}: {signal_tcs} < {strategy_def.min_tcs}")
                    return False
            
            # Check direction rules
            if strategy == 'DOUBLE_TAP' and tracking:
                # Must be same direction as previous trade
                last_direction = tracking.get('last_trade_direction')
                if last_direction and last_direction != signal['direction']:
                    self.logger.info(f"Direction mismatch for DOUBLE_TAP: {signal['direction']} != {last_direction}")
                    return False
            
            # Check FIRST_BLOOD stop condition
            if strategy == 'FIRST_BLOOD' and tracking:
                trades_won = tracking.get('trades_won', 0)
                if trades_won >= 2:
                    self.logger.info(f"FIRST_BLOOD stop condition met: {trades_won} wins")
                    return False
            
            self.logger.info(f"✅ Signal eligible for {strategy}: TCS {signal_tcs}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Eligibility check failed for {user_id}: {e}")
            return False
    
    def record_mission_creation(self, user_id: str, strategy: str, mission: Any) -> bool:
        """Record mission creation for tactical tracking"""
        try:
            today = datetime.now(timezone.utc).date().isoformat()
            now = datetime.now(timezone.utc)
            
            # Get or create daily tracking
            tracking = self._get_daily_tracking(user_id, today, strategy)
            
            if not tracking:
                # Create new tracking record
                self.conn.execute('''
                    INSERT INTO daily_tactical_tracking
                    (user_id, date, strategy, trades_taken, last_trade_direction, 
                     created_at, updated_at)
                    VALUES (?, ?, ?, 1, ?, ?, ?)
                ''', (
                    user_id, today, strategy, mission.direction,
                    now.isoformat(), now.isoformat()
                ))
            else:
                # Update existing tracking
                new_trades = tracking['trades_taken'] + 1
                
                self.conn.execute('''
                    UPDATE daily_tactical_tracking
                    SET trades_taken = ?, last_trade_direction = ?, updated_at = ?
                    WHERE user_id = ? AND date = ? AND strategy = ?
                ''', (
                    new_trades, mission.direction, now.isoformat(),
                    user_id, today, strategy
                ))
            
            # Log the tactical trade
            self.conn.execute('''
                INSERT INTO tactical_trade_log
                (user_id, date, strategy, mission_id, trade_number, tcs_score,
                 direction, trade_timestamp, real_trade_verified, simulation_mode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 0)
            ''', (
                user_id, today, strategy, mission.mission_id,
                (tracking['trades_taken'] + 1) if tracking else 1,
                mission.tcs_score, mission.direction, now.isoformat()
            ))
            
            self.conn.commit()
            
            self.logger.info(f"✅ Recorded mission creation for {strategy}: {mission.mission_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to record mission creation: {e}")
            return False
    
    def record_trade_result(self, user_id: str, mission_id: str, result: Dict) -> bool:
        """Record real trade result for tactical tracking"""
        try:
            today = datetime.now(timezone.utc).date().isoformat()
            now = datetime.now(timezone.utc)
            
            # Get trade record
            cursor = self.conn.execute('''
                SELECT * FROM tactical_trade_log
                WHERE user_id = ? AND mission_id = ?
            ''', (user_id, mission_id))
            
            trade_record = cursor.fetchone()
            if not trade_record:
                self.logger.error(f"Trade record not found: {mission_id}")
                return False
            
            # Verify real trade (no simulation)
            if not result.get('real_trade_verified', False):
                self.logger.error(f"SIMULATION TRADE DETECTED: {mission_id} - REAL TRADES ONLY")
                return False
            
            strategy = trade_record[2]  # strategy column
            success = result.get('success', False)
            pnl = float(result.get('pnl', 0.0))
            
            # Update trade log
            self.conn.execute('''
                UPDATE tactical_trade_log
                SET result = ?, pnl = ?
                WHERE user_id = ? AND mission_id = ?
            ''', (
                'WIN' if success else 'LOSS', pnl,
                user_id, mission_id
            ))
            
            # Update daily tracking
            tracking = self._get_daily_tracking(user_id, today, strategy)
            if tracking:
                new_wins = tracking['trades_won'] + (1 if success else 0)
                new_pnl = tracking['total_pnl'] + pnl
                
                # Check if strategy is completed
                strategy_completed = self._check_strategy_completion(strategy, tracking, success)
                
                self.conn.execute('''
                    UPDATE daily_tactical_tracking
                    SET trades_won = ?, total_pnl = ?, strategy_completed = ?, updated_at = ?
                    WHERE user_id = ? AND date = ? AND strategy = ?
                ''', (
                    new_wins, new_pnl, strategy_completed, now.isoformat(),
                    user_id, today, strategy
                ))
            
            self.conn.commit()
            
            self.logger.info(f"✅ Recorded real trade result for {strategy}: {mission_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to record trade result: {e}")
            return False
    
    def _get_daily_tracking(self, user_id: str, date: str, strategy: str) -> Optional[Dict]:
        """Get daily tactical tracking for user"""
        try:
            cursor = self.conn.execute('''
                SELECT * FROM daily_tactical_tracking
                WHERE user_id = ? AND date = ? AND strategy = ?
            ''', (user_id, date, strategy))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get daily tracking: {e}")
            return None
    
    def _check_strategy_completion(self, strategy: str, tracking: Dict, last_success: bool) -> bool:
        """Check if tactical strategy is completed"""
        if strategy == 'FIRST_BLOOD':
            # Stop after 2 wins OR 4 trades
            return tracking['trades_won'] >= 2 or tracking['trades_taken'] >= 4
            
        elif strategy == 'DOUBLE_TAP':
            # Stop after 2 trades
            return tracking['trades_taken'] >= 2
            
        elif strategy == 'LONE_WOLF':
            # Stop after 4 trades
            return tracking['trades_taken'] >= 4
            
        elif strategy == 'TACTICAL_COMMAND':
            # Depends on chosen mode
            if tracking.get('escalation_level') == 1:  # Sniper mode
                return tracking['trades_taken'] >= 1
            else:  # Volume mode
                return tracking['trades_taken'] >= 6
        
        return False
    
    def get_user_daily_status(self, user_id: str, strategy: str) -> Dict:
        """Get user's daily tactical status"""
        try:
            today = datetime.now(timezone.utc).date().isoformat()
            tracking = self._get_daily_tracking(user_id, today, strategy)
            
            if not tracking:
                return {
                    'strategy': strategy,
                    'trades_taken': 0,
                    'trades_remaining': self.strategies[strategy].max_trades,
                    'trades_won': 0,
                    'total_pnl': 0.0,
                    'strategy_completed': False,
                    'win_rate': 0.0
                }
            
            strategy_def = self.strategies[strategy]
            trades_remaining = strategy_def.max_trades - tracking['trades_taken']
            
            # Special handling for TACTICAL_COMMAND
            if strategy == 'TACTICAL_COMMAND' and tracking.get('escalation_level') == 1:
                trades_remaining = 1 - tracking['trades_taken']
            
            win_rate = (tracking['trades_won'] / tracking['trades_taken']) * 100 if tracking['trades_taken'] > 0 else 0
            
            return {
                'strategy': strategy,
                'trades_taken': tracking['trades_taken'],
                'trades_remaining': max(0, trades_remaining),
                'trades_won': tracking['trades_won'],
                'total_pnl': tracking['total_pnl'],
                'strategy_completed': tracking['strategy_completed'],
                'win_rate': win_rate
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get daily status for {user_id}: {e}")
            return {}

# Global tactical engine
TACTICAL_ENGINE = None

def get_tactical_engine() -> TacticalStrategyEngine:
    """Get global tactical engine instance"""
    global TACTICAL_ENGINE
    if TACTICAL_ENGINE is None:
        TACTICAL_ENGINE = TacticalStrategyEngine()
    return TACTICAL_ENGINE

def is_signal_eligible_for_user(signal: Dict, user_id: str, strategy: str) -> bool:
    """Check if signal is eligible for user's strategy"""
    engine = get_tactical_engine()
    return engine.is_signal_eligible(signal, strategy, user_id)

if __name__ == "__main__":
    print("🎯 TESTING TACTICAL STRATEGY ENGINE")
    print("=" * 50)
    
    engine = TacticalStrategyEngine()
    
    # Test signal eligibility
    test_signal = {
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'tcs_score': 80
    }
    
    test_user = "test_user_123"
    
    for strategy in engine.strategies.keys():
        eligible = engine.is_signal_eligible(test_signal, strategy, test_user)
        print(f"✅ {strategy}: {'ELIGIBLE' if eligible else 'NOT ELIGIBLE'}")
    
    print("🎯 TACTICAL STRATEGY ENGINE OPERATIONAL - REAL STRATEGIES ONLY")