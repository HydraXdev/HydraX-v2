"""
Shield Logger - Performance tracking and data storage for CITADEL

Purpose: Log all shield decisions, track outcomes, and provide data for
system improvement and user analytics.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import logging
import os
from collections import defaultdict
from dataclasses import dataclass, asdict
import sqlite3

logger = logging.getLogger(__name__)


@dataclass
class ShieldLogEntry:
    """Single shield analysis log entry"""
    signal_id: str
    timestamp: datetime
    pair: str
    direction: str
    shield_score: float
    classification: str
    outcome: Optional[str] = None  # WIN, LOSS, BE, SKIPPED
    pips_result: Optional[float] = None
    user_followed_shield: Optional[bool] = None
    risk_factors: Optional[List[str]] = None
    quality_factors: Optional[List[str]] = None
    

class ShieldLogger:
    """
    Logs and tracks all CITADEL shield analyses for performance monitoring,
    system improvement, and user education.
    """
    
    def __init__(self, db_path: str = "/root/HydraX-v2/data/citadel_shield.db"):
        self.db_path = db_path
        self._ensure_db_exists()
        self._init_database()
        
        # In-memory cache for recent analyses
        self.recent_analyses = []
        self.max_cache_size = 1000
        
        # Performance trackers
        self.classification_outcomes = defaultdict(lambda: {'total': 0, 'wins': 0, 'losses': 0})
        self.user_shield_compliance = defaultdict(lambda: {'followed': 0, 'ignored': 0})
        
    def _ensure_db_exists(self):
        """Ensure database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _init_database(self):
        """Initialize SQLite database with required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Shield analyses table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS shield_analyses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        signal_id TEXT UNIQUE NOT NULL,
                        timestamp DATETIME NOT NULL,
                        pair TEXT NOT NULL,
                        direction TEXT NOT NULL,
                        shield_score REAL NOT NULL,
                        classification TEXT NOT NULL,
                        base_score REAL,
                        risk_factors TEXT,
                        quality_factors TEXT,
                        components TEXT,
                        explanation TEXT,
                        recommendation TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Trade outcomes table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS shield_outcomes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        signal_id TEXT NOT NULL,
                        user_id INTEGER,
                        outcome TEXT NOT NULL,
                        pips_result REAL,
                        user_followed_shield BOOLEAN,
                        execution_time DATETIME,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (signal_id) REFERENCES shield_analyses(signal_id)
                    )
                """)
                
                # User patterns table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_shield_patterns (
                        user_id INTEGER PRIMARY KEY,
                        trust_score REAL DEFAULT 0.5,
                        signals_seen INTEGER DEFAULT 0,
                        shields_followed INTEGER DEFAULT 0,
                        win_rate_following REAL,
                        win_rate_ignoring REAL,
                        favorite_pairs TEXT,
                        weakness_patterns TEXT,
                        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Performance metrics table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS shield_performance (
                        date DATE PRIMARY KEY,
                        total_signals INTEGER,
                        approved_count INTEGER,
                        active_count INTEGER,
                        caution_count INTEGER,
                        unverified_count INTEGER,
                        approved_win_rate REAL,
                        active_win_rate REAL,
                        overall_accuracy REAL,
                        avg_shield_score REAL
                    )
                """)
                
                # Create indices
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_signal_timestamp ON shield_analyses(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_outcome_signal ON shield_outcomes(signal_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_outcome_user ON shield_outcomes(user_id)")
                
                conn.commit()
                logger.info("Shield database initialized successfully")
                
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
    
    def log_shield_analysis(self, signal_id: str, signal_data: Dict[str, Any],
                          shield_analysis: Dict[str, Any]) -> bool:
        """
        Log a new shield analysis.
        
        Args:
            signal_id: Unique signal identifier
            signal_data: Original signal information
            shield_analysis: Complete shield analysis results
            
        Returns:
            Success status
        """
        try:
            # Prepare log entry
            risk_factors = [f['factor'] for f in shield_analysis.get('risk_factors', [])]
            quality_factors = [f['factor'] for f in shield_analysis.get('quality_factors', [])]
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO shield_analyses 
                    (signal_id, timestamp, pair, direction, shield_score, classification,
                     base_score, risk_factors, quality_factors, components, explanation, recommendation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    signal_id,
                    datetime.now(),
                    signal_data.get('pair', ''),
                    signal_data.get('direction', ''),
                    shield_analysis.get('shield_score', 0),
                    shield_analysis.get('classification', 'UNVERIFIED'),
                    shield_analysis.get('base_score', 0),
                    json.dumps(risk_factors),
                    json.dumps(quality_factors),
                    json.dumps(shield_analysis.get('components', [])),
                    shield_analysis.get('explanation', ''),
                    shield_analysis.get('recommendation', '')
                ))
                conn.commit()
            
            # Add to memory cache
            self._add_to_cache(signal_id, signal_data, shield_analysis)
            
            # Update classification tracker
            classification = shield_analysis.get('classification', 'UNVERIFIED')
            self.classification_outcomes[classification]['total'] += 1
            
            logger.info(f"Logged shield analysis for {signal_id}: "
                       f"Score={shield_analysis.get('shield_score', 0)}, "
                       f"Class={classification}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log shield analysis: {str(e)}")
            return False
    
    def log_trade_outcome(self, signal_id: str, user_id: int, outcome: str,
                         pips_result: float, user_followed_shield: bool) -> bool:
        """
        Log the outcome of a trade.
        
        Args:
            signal_id: Signal identifier
            user_id: User who traded
            outcome: WIN, LOSS, BE, or SKIPPED
            pips_result: Pip result (positive or negative)
            user_followed_shield: Whether user followed shield advice
            
        Returns:
            Success status
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Log outcome
                cursor.execute("""
                    INSERT INTO shield_outcomes 
                    (signal_id, user_id, outcome, pips_result, user_followed_shield, execution_time)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (signal_id, user_id, outcome, pips_result, user_followed_shield, datetime.now()))
                
                # Get shield classification for this signal
                cursor.execute("""
                    SELECT classification FROM shield_analyses WHERE signal_id = ?
                """, (signal_id,))
                result = cursor.fetchone()
                
                if result:
                    classification = result[0]
                    # Update classification performance
                    if outcome == 'WIN':
                        self.classification_outcomes[classification]['wins'] += 1
                    elif outcome == 'LOSS':
                        self.classification_outcomes[classification]['losses'] += 1
                
                # Update user compliance tracking
                if user_followed_shield:
                    self.user_shield_compliance[user_id]['followed'] += 1
                else:
                    self.user_shield_compliance[user_id]['ignored'] += 1
                
                conn.commit()
                
            logger.info(f"Logged outcome for {signal_id}: {outcome} "
                       f"({pips_result} pips), followed={user_followed_shield}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log trade outcome: {str(e)}")
            return False
    
    def get_shield_performance(self, days: int = 30) -> Dict[str, Any]:
        """
        Get shield performance statistics.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Performance statistics
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Overall statistics
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_signals,
                        AVG(shield_score) as avg_score,
                        COUNT(CASE WHEN classification = 'SHIELD_APPROVED' THEN 1 END) as approved,
                        COUNT(CASE WHEN classification = 'SHIELD_ACTIVE' THEN 1 END) as active,
                        COUNT(CASE WHEN classification = 'VOLATILITY_ZONE' THEN 1 END) as caution,
                        COUNT(CASE WHEN classification = 'UNVERIFIED' THEN 1 END) as unverified
                    FROM shield_analyses
                    WHERE timestamp >= ?
                """, (cutoff_date,))
                
                stats = cursor.fetchone()
                
                # Win rates by classification
                cursor.execute("""
                    SELECT 
                        sa.classification,
                        COUNT(so.id) as trades,
                        COUNT(CASE WHEN so.outcome = 'WIN' THEN 1 END) as wins,
                        COUNT(CASE WHEN so.outcome = 'LOSS' THEN 1 END) as losses
                    FROM shield_analyses sa
                    JOIN shield_outcomes so ON sa.signal_id = so.signal_id
                    WHERE sa.timestamp >= ?
                    GROUP BY sa.classification
                """, (cutoff_date,))
                
                win_rates = {}
                for row in cursor.fetchall():
                    classification, trades, wins, losses = row
                    win_rate = (wins / trades * 100) if trades > 0 else 0
                    win_rates[classification] = {
                        'trades': trades,
                        'wins': wins,
                        'losses': losses,
                        'win_rate': round(win_rate, 1)
                    }
                
                # Shield following statistics
                cursor.execute("""
                    SELECT 
                        COUNT(CASE WHEN user_followed_shield = 1 THEN 1 END) as followed,
                        COUNT(CASE WHEN user_followed_shield = 0 THEN 1 END) as ignored,
                        COUNT(CASE WHEN user_followed_shield = 1 AND outcome = 'WIN' THEN 1 END) as followed_wins,
                        COUNT(CASE WHEN user_followed_shield = 0 AND outcome = 'WIN' THEN 1 END) as ignored_wins
                    FROM shield_outcomes
                    WHERE execution_time >= ?
                """, (cutoff_date,))
                
                compliance = cursor.fetchone()
                
                return {
                    'period_days': days,
                    'total_signals': stats[0] or 0,
                    'avg_shield_score': round(stats[1] or 0, 1),
                    'classifications': {
                        'SHIELD_APPROVED': stats[2] or 0,
                        'SHIELD_ACTIVE': stats[3] or 0,
                        'VOLATILITY_ZONE': stats[4] or 0,
                        'UNVERIFIED': stats[5] or 0
                    },
                    'win_rates_by_class': win_rates,
                    'shield_compliance': {
                        'followed_count': compliance[0] or 0,
                        'ignored_count': compliance[1] or 0,
                        'follow_rate': round((compliance[0] / (compliance[0] + compliance[1]) * 100) 
                                           if (compliance[0] + compliance[1]) > 0 else 0, 1),
                        'win_rate_when_followed': round((compliance[2] / compliance[0] * 100) 
                                                      if compliance[0] > 0 else 0, 1),
                        'win_rate_when_ignored': round((compliance[3] / compliance[1] * 100) 
                                                     if compliance[1] > 0 else 0, 1)
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get shield performance: {str(e)}")
            return {}
    
    def get_user_shield_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get shield statistics for a specific user.
        
        Args:
            user_id: User identifier
            
        Returns:
            User's shield statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get user's shield following behavior
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_signals,
                        COUNT(CASE WHEN user_followed_shield = 1 THEN 1 END) as followed,
                        COUNT(CASE WHEN user_followed_shield = 0 THEN 1 END) as ignored,
                        COUNT(CASE WHEN outcome = 'WIN' THEN 1 END) as total_wins,
                        COUNT(CASE WHEN user_followed_shield = 1 AND outcome = 'WIN' THEN 1 END) as followed_wins,
                        COUNT(CASE WHEN user_followed_shield = 0 AND outcome = 'WIN' THEN 1 END) as ignored_wins,
                        AVG(CASE WHEN user_followed_shield = 1 THEN pips_result END) as avg_pips_followed,
                        AVG(CASE WHEN user_followed_shield = 0 THEN pips_result END) as avg_pips_ignored
                    FROM shield_outcomes
                    WHERE user_id = ?
                """, (user_id,))
                
                stats = cursor.fetchone()
                
                # Get performance by classification when followed
                cursor.execute("""
                    SELECT 
                        sa.classification,
                        COUNT(*) as count,
                        COUNT(CASE WHEN so.outcome = 'WIN' THEN 1 END) as wins
                    FROM shield_analyses sa
                    JOIN shield_outcomes so ON sa.signal_id = so.signal_id
                    WHERE so.user_id = ? AND so.user_followed_shield = 1
                    GROUP BY sa.classification
                """, (user_id,))
                
                class_performance = {}
                for row in cursor.fetchall():
                    classification, count, wins = row
                    class_performance[classification] = {
                        'trades': count,
                        'wins': wins,
                        'win_rate': round((wins / count * 100) if count > 0 else 0, 1)
                    }
                
                # Calculate trust score
                total = stats[0] or 0
                followed = stats[1] or 0
                trust_score = (followed / total) if total > 0 else 0.5
                
                return {
                    'user_id': user_id,
                    'total_signals_seen': total,
                    'shields_followed': followed,
                    'shields_ignored': stats[2] or 0,
                    'trust_score': round(trust_score, 2),
                    'overall_win_rate': round((stats[3] / total * 100) if total > 0 else 0, 1),
                    'win_rate_when_following': round((stats[4] / followed * 100) if followed > 0 else 0, 1),
                    'win_rate_when_ignoring': round((stats[5] / stats[2] * 100) if stats[2] > 0 else 0, 1),
                    'avg_pips_when_following': round(stats[6] or 0, 1),
                    'avg_pips_when_ignoring': round(stats[7] or 0, 1),
                    'performance_by_classification': class_performance,
                    'recommendation': self._generate_user_recommendation(trust_score, stats)
                }
                
        except Exception as e:
            logger.error(f"Failed to get user shield stats: {str(e)}")
            return {}
    
    def identify_improvement_opportunities(self) -> Dict[str, Any]:
        """
        Analyze shield performance to identify areas for improvement.
        
        Returns:
            Improvement insights and recommendations
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Find problematic score ranges
                cursor.execute("""
                    SELECT 
                        CAST(shield_score AS INTEGER) as score_bucket,
                        COUNT(*) as count,
                        COUNT(CASE WHEN so.outcome = 'WIN' THEN 1 END) as wins
                    FROM shield_analyses sa
                    LEFT JOIN shield_outcomes so ON sa.signal_id = so.signal_id
                    GROUP BY score_bucket
                    ORDER BY score_bucket
                """)
                
                score_performance = {}
                for row in cursor.fetchall():
                    bucket, count, wins = row
                    win_rate = (wins / count * 100) if count > 0 and wins is not None else 0
                    score_performance[bucket] = {
                        'signals': count,
                        'win_rate': round(win_rate, 1)
                    }
                
                # Find risk factors with poor performance
                cursor.execute("""
                    SELECT 
                        risk_factors,
                        COUNT(*) as count,
                        COUNT(CASE WHEN so.outcome = 'WIN' THEN 1 END) as wins
                    FROM shield_analyses sa
                    LEFT JOIN shield_outcomes so ON sa.signal_id = so.signal_id
                    WHERE risk_factors != '[]'
                    GROUP BY risk_factors
                """)
                
                risk_factor_impact = []
                for row in cursor.fetchall():
                    factors = json.loads(row[0])
                    count = row[1]
                    wins = row[2] or 0
                    win_rate = (wins / count * 100) if count > 0 else 0
                    
                    for factor in factors:
                        risk_factor_impact.append({
                            'factor': factor,
                            'occurrences': count,
                            'win_rate': round(win_rate, 1)
                        })
                
                # Identify threshold optimization opportunities
                improvements = {
                    'score_bucket_performance': score_performance,
                    'problematic_risk_factors': sorted(
                        risk_factor_impact, 
                        key=lambda x: x['win_rate']
                    )[:5],
                    'recommendations': []
                }
                
                # Generate recommendations
                if score_performance.get(7, {}).get('win_rate', 0) < 60:
                    improvements['recommendations'].append(
                        "Consider raising SHIELD_ACTIVE threshold - "
                        "Score 7 signals underperforming"
                    )
                
                if score_performance.get(8, {}).get('win_rate', 0) < 70:
                    improvements['recommendations'].append(
                        "Review SHIELD_APPROVED criteria - "
                        "Score 8 signals not meeting expectations"
                    )
                
                return improvements
                
        except Exception as e:
            logger.error(f"Failed to identify improvements: {str(e)}")
            return {}
    
    def _add_to_cache(self, signal_id: str, signal_data: Dict, 
                     shield_analysis: Dict):
        """Add analysis to memory cache."""
        entry = {
            'signal_id': signal_id,
            'timestamp': datetime.now(),
            'pair': signal_data.get('pair'),
            'shield_score': shield_analysis.get('shield_score'),
            'classification': shield_analysis.get('classification')
        }
        
        self.recent_analyses.append(entry)
        
        # Maintain cache size
        if len(self.recent_analyses) > self.max_cache_size:
            self.recent_analyses.pop(0)
    
    def _generate_user_recommendation(self, trust_score: float, 
                                    stats: Tuple) -> str:
        """Generate personalized recommendation for user."""
        if stats[0] == 0:  # No signals yet
            return "Start following shield recommendations to build your track record"
        
        followed_wr = (stats[4] / stats[1] * 100) if stats[1] > 0 else 0
        ignored_wr = (stats[5] / stats[2] * 100) if stats[2] > 0 else 0
        
        if trust_score > 0.8 and followed_wr > 70:
            return "Excellent shield discipline! Keep following the shield guidance."
        elif followed_wr > ignored_wr + 10:
            return "Shield is improving your results. Consider following it more consistently."
        elif trust_score < 0.3:
            return "You rarely follow shield advice. Try trusting it more to see improvement."
        else:
            return "Mixed results. Focus on following shield for high-score (8+) signals."
    
    def get_recent_signals(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent signals from cache or database."""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        # First check cache
        recent = [s for s in self.recent_analyses if s['timestamp'] >= cutoff]
        
        if len(recent) < 10:  # If cache doesn't have enough, query DB
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT signal_id, timestamp, pair, shield_score, classification
                        FROM shield_analyses
                        WHERE timestamp >= ?
                        ORDER BY timestamp DESC
                        LIMIT 50
                    """, (cutoff,))
                    
                    recent = [
                        {
                            'signal_id': row[0],
                            'timestamp': datetime.fromisoformat(row[1]),
                            'pair': row[2],
                            'shield_score': row[3],
                            'classification': row[4]
                        }
                        for row in cursor.fetchall()
                    ]
            except Exception as e:
                logger.error(f"Failed to get recent signals: {str(e)}")
        
        return recent


# Example usage
if __name__ == "__main__":
    logger_instance = ShieldLogger()
    
    # Test logging
    test_signal_id = "TEST_SIGNAL_001"
    test_signal = {
        'pair': 'EURUSD',
        'direction': 'BUY'
    }
    test_analysis = {
        'shield_score': 8.5,
        'classification': 'SHIELD_APPROVED',
        'base_score': 7.0,
        'risk_factors': [{'factor': 'news_proximity', 'penalty': -0.5}],
        'quality_factors': [{'factor': 'post_sweep_entry', 'bonus': 2.0}],
        'components': [],
        'explanation': 'Strong setup with post-sweep confirmation',
        'recommendation': 'Standard position size recommended'
    }
    
    # Log analysis
    logger_instance.log_shield_analysis(test_signal_id, test_signal, test_analysis)
    
    # Log outcome
    logger_instance.log_trade_outcome(test_signal_id, 12345, 'WIN', 25.5, True)
    
    # Get performance
    performance = logger_instance.get_shield_performance(30)
    print("Shield Performance (30 days):")
    print(json.dumps(performance, indent=2))
    
    # Get user stats
    user_stats = logger_instance.get_user_shield_stats(12345)
    print("\nUser Shield Stats:")
    print(json.dumps(user_stats, indent=2))