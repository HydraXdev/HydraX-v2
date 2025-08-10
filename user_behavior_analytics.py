#!/usr/bin/env python3
"""
User Behavior Analytics - Track how users interact with signals

Tracks which signals users execute vs skip, analyzes user success rates by tier,
identifies power users vs struggling users, and generates user insights reports.
"""

import json
import time
import redis
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
import statistics

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('UserBehaviorAnalytics')

class UserBehaviorAnalytics:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.truth_log_path = '/root/HydraX-v2/truth_log.jsonl'
        self.user_registry_path = '/root/HydraX-v2/user_registry.json'
        
        # User classification thresholds
        self.power_user_thresholds = {'execution_rate': 70, 'win_rate': 60}
        self.struggling_user_thresholds = {'execution_rate': 20, 'win_rate': 40}
        
        # Track user actions
        self.user_actions = defaultdict(list)
        self.user_performance = defaultdict(dict)
        
    def load_user_registry(self) -> Dict:
        """Load user registry for tier information"""
        
        try:
            with open(self.user_registry_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("User registry not found")
            return {}
        except Exception as e:
            logger.error(f"Error loading user registry: {e}")
            return {}
    
    def track_signal_presented(self, user_id: str, signal_id: str, signal_data: Dict = None):
        """Track when signal is shown to user"""
        
        key = f"user:{user_id}:signals_presented"
        self.redis_client.sadd(key, signal_id)
        self.redis_client.expire(key, 2592000)  # 30 days
        
        # Store signal metadata for analysis
        if signal_data:
            signal_key = f"signal_presented:{user_id}:{signal_id}"
            signal_meta = {
                'timestamp': time.time(),
                'confidence': signal_data.get('confidence', 0),
                'pattern': signal_data.get('signal_type', 'UNKNOWN'),
                'symbol': signal_data.get('symbol', 'UNKNOWN'),
                'session': signal_data.get('session', 'UNKNOWN')
            }
            self.redis_client.hset(signal_key, mapping=signal_meta)
            self.redis_client.expire(signal_key, 2592000)  # 30 days
        
        logger.debug(f"Tracked signal presentation: {user_id} - {signal_id}")
    
    def track_signal_executed(self, user_id: str, signal_id: str, execution_time: float = None):
        """Track when user fires on signal"""
        
        key = f"user:{user_id}:signals_executed"
        self.redis_client.sadd(key, signal_id)
        self.redis_client.expire(key, 2592000)  # 30 days
        
        # Track execution timing
        execution_key = f"signal_executed:{user_id}:{signal_id}"
        execution_data = {
            'execution_time': execution_time or time.time(),
            'decision_speed': 'unknown'  # Can be calculated if presentation time is known
        }
        
        # Calculate decision speed if presentation data exists
        presentation_key = f"signal_presented:{user_id}:{signal_id}"
        presentation_data = self.redis_client.hgetall(presentation_key)
        if presentation_data and 'timestamp' in presentation_data:
            presentation_time = float(presentation_data['timestamp'])
            decision_time = (execution_time or time.time()) - presentation_time
            
            if decision_time < 30:
                execution_data['decision_speed'] = 'fast'
            elif decision_time < 300:
                execution_data['decision_speed'] = 'normal' 
            else:
                execution_data['decision_speed'] = 'slow'
                
            execution_data['decision_time_seconds'] = decision_time
        
        self.redis_client.hset(execution_key, mapping=execution_data)
        self.redis_client.expire(execution_key, 2592000)
        
        logger.info(f"Tracked signal execution: {user_id} - {signal_id}")
    
    def track_signal_skipped(self, user_id: str, signal_id: str, reason: str = 'user_choice'):
        """Track when user passes on signal"""
        
        key = f"user:{user_id}:signals_skipped"
        self.redis_client.sadd(key, signal_id)
        self.redis_client.expire(key, 2592000)
        
        # Track skip reason
        skip_key = f"signal_skipped:{user_id}:{signal_id}"
        skip_data = {
            'timestamp': time.time(),
            'reason': reason  # user_choice, expired, low_confidence, etc.
        }
        self.redis_client.hset(skip_key, mapping=skip_data)
        self.redis_client.expire(skip_key, 2592000)
        
        logger.debug(f"Tracked signal skip: {user_id} - {signal_id} (reason: {reason})")
    
    def get_user_trades(self, user_id: str) -> List[Dict]:
        """Get user's trade history from truth tracker"""
        
        trades = []
        
        try:
            with open(self.truth_log_path, 'r') as f:
                for line in f:
                    if line.strip():
                        trade = json.loads(line)
                        
                        # Check if trade belongs to user (simplified check)
                        if (user_id in trade.get('users_fired', []) or 
                            trade.get('user_count', 0) > 0):  # Assuming user executed
                            trades.append(trade)
                            
        except FileNotFoundError:
            logger.warning("Truth log not found")
        except Exception as e:
            logger.error(f"Error loading user trades: {e}")
        
        return trades
    
    def calculate_user_win_rate(self, trades: List[Dict]) -> float:
        """Calculate user's win rate from trades"""
        
        if not trades:
            return 0.0
            
        wins = sum(1 for trade in trades if 
                  trade.get('outcome') == 'WIN' or 
                  trade.get('hit_tp_first', False) or 
                  trade.get('pips_result', 0) > 0)
        
        return wins / len(trades) * 100
    
    def analyze_user_patterns(self, user_id: str) -> Dict:
        """Analyze individual user behavior"""
        
        # Get user's signal interaction data
        presented = self.redis_client.smembers(f"user:{user_id}:signals_presented")
        executed = self.redis_client.smembers(f"user:{user_id}:signals_executed")
        skipped = self.redis_client.smembers(f"user:{user_id}:signals_skipped")
        
        execution_rate = len(executed) / len(presented) * 100 if presented else 0
        skip_rate = len(skipped) / len(presented) * 100 if presented else 0
        
        # Get user's trade outcomes
        user_trades = self.get_user_trades(user_id)
        win_rate = self.calculate_user_win_rate(user_trades)
        
        # Analyze decision patterns
        decision_analysis = self.analyze_decision_patterns(user_id, executed)
        confidence_preferences = self.analyze_confidence_preferences(user_id, executed)
        pattern_preferences = self.analyze_pattern_preferences(user_id, executed)
        
        # Get user tier from registry
        user_registry = self.load_user_registry()
        user_tier = user_registry.get(user_id, {}).get('tier', 'UNKNOWN')
        
        return {
            'user_id': user_id,
            'user_tier': user_tier,
            'signals_presented': len(presented),
            'signals_executed': len(executed),
            'signals_skipped': len(skipped),
            'execution_rate': round(execution_rate, 1),
            'skip_rate': round(skip_rate, 1),
            'win_rate': round(win_rate, 1),
            'total_trades': len(user_trades),
            'user_type': self.classify_user(execution_rate, win_rate, len(user_trades)),
            'decision_patterns': decision_analysis,
            'confidence_preferences': confidence_preferences,
            'pattern_preferences': pattern_preferences,
            'recommendations': self.get_user_recommendations(execution_rate, win_rate, len(user_trades))
        }
    
    def analyze_decision_patterns(self, user_id: str, executed_signals: set) -> Dict:
        """Analyze user's decision-making patterns"""
        
        decision_speeds = []
        execution_times = []
        
        for signal_id in executed_signals:
            execution_key = f"signal_executed:{user_id}:{signal_id}"
            execution_data = self.redis_client.hgetall(execution_key)
            
            if execution_data and 'decision_speed' in execution_data:
                decision_speeds.append(execution_data['decision_speed'])
                
            if execution_data and 'decision_time_seconds' in execution_data:
                execution_times.append(float(execution_data['decision_time_seconds']))
        
        # Count decision speed types
        speed_counts = defaultdict(int)
        for speed in decision_speeds:
            speed_counts[speed] += 1
        
        return {
            'decision_speed_distribution': dict(speed_counts),
            'avg_decision_time': statistics.mean(execution_times) if execution_times else None,
            'median_decision_time': statistics.median(execution_times) if execution_times else None,
            'decision_style': self.determine_decision_style(speed_counts, execution_times)
        }
    
    def analyze_confidence_preferences(self, user_id: str, executed_signals: set) -> Dict:
        """Analyze user's confidence threshold preferences"""
        
        confidences = []
        
        for signal_id in executed_signals:
            presentation_key = f"signal_presented:{user_id}:{signal_id}"
            signal_data = self.redis_client.hgetall(presentation_key)
            
            if signal_data and 'confidence' in signal_data:
                confidences.append(float(signal_data['confidence']))
        
        if confidences:
            return {
                'avg_executed_confidence': round(statistics.mean(confidences), 1),
                'min_executed_confidence': min(confidences),
                'max_executed_confidence': max(confidences),
                'confidence_preference': self.determine_confidence_preference(confidences)
            }
        else:
            return {'error': 'No confidence data available'}
    
    def analyze_pattern_preferences(self, user_id: str, executed_signals: set) -> Dict:
        """Analyze user's pattern preferences"""
        
        patterns = []
        symbols = []
        sessions = []
        
        for signal_id in executed_signals:
            presentation_key = f"signal_presented:{user_id}:{signal_id}"
            signal_data = self.redis_client.hgetall(presentation_key)
            
            if signal_data:
                patterns.append(signal_data.get('pattern', 'UNKNOWN'))
                symbols.append(signal_data.get('symbol', 'UNKNOWN'))
                sessions.append(signal_data.get('session', 'UNKNOWN'))
        
        # Count preferences
        pattern_counts = defaultdict(int)
        symbol_counts = defaultdict(int)
        session_counts = defaultdict(int)
        
        for pattern in patterns:
            pattern_counts[pattern] += 1
        for symbol in symbols:
            symbol_counts[symbol] += 1
        for session in sessions:
            session_counts[session] += 1
        
        # Find favorites
        favorite_pattern = max(pattern_counts.items(), key=lambda x: x[1])[0] if pattern_counts else None
        favorite_symbol = max(symbol_counts.items(), key=lambda x: x[1])[0] if symbol_counts else None
        favorite_session = max(session_counts.items(), key=lambda x: x[1])[0] if session_counts else None
        
        return {
            'pattern_distribution': dict(pattern_counts),
            'symbol_distribution': dict(symbol_counts),
            'session_distribution': dict(session_counts),
            'favorite_pattern': favorite_pattern,
            'favorite_symbol': favorite_symbol,
            'favorite_session': favorite_session
        }
    
    def determine_decision_style(self, speed_counts: Dict, execution_times: List[float]) -> str:
        """Determine user's decision-making style"""
        
        if not speed_counts:
            return 'UNKNOWN'
            
        total_decisions = sum(speed_counts.values())
        
        if speed_counts.get('fast', 0) / total_decisions > 0.6:
            return 'IMPULSIVE'
        elif speed_counts.get('slow', 0) / total_decisions > 0.5:
            return 'ANALYTICAL'
        else:
            return 'BALANCED'
    
    def determine_confidence_preference(self, confidences: List[float]) -> str:
        """Determine user's confidence threshold preference"""
        
        avg_confidence = statistics.mean(confidences)
        
        if avg_confidence >= 85:
            return 'HIGH_CONFIDENCE_ONLY'
        elif avg_confidence >= 75:
            return 'SELECTIVE'
        elif avg_confidence >= 65:
            return 'MODERATE_RISK'
        else:
            return 'AGGRESSIVE_RISK_TAKER'
    
    def classify_user(self, execution_rate: float, win_rate: float, total_trades: int) -> str:
        """Classify user based on behavior and performance"""
        
        if total_trades < 5:
            return "NEW_TRADER"
        elif (execution_rate >= self.power_user_thresholds['execution_rate'] and 
              win_rate >= self.power_user_thresholds['win_rate']):
            return "POWER_USER"
        elif execution_rate < self.struggling_user_thresholds['execution_rate']:
            return "CAUTIOUS"
        elif win_rate < self.struggling_user_thresholds['win_rate']:
            return "STRUGGLING"
        elif execution_rate > 80:
            return "HIGH_ACTIVITY"
        elif win_rate > 60:
            return "SKILLED"
        else:
            return "DEVELOPING"
    
    def get_user_recommendations(self, execution_rate: float, win_rate: float, total_trades: int) -> List[str]:
        """Generate personalized recommendations for user"""
        
        recommendations = []
        
        user_type = self.classify_user(execution_rate, win_rate, total_trades)
        
        if user_type == "NEW_TRADER":
            recommendations.append("Start with high-confidence signals (80%+) to build experience")
            recommendations.append("Focus on learning pattern recognition before increasing volume")
            
        elif user_type == "POWER_USER":
            recommendations.append("Consider advanced strategies and position sizing optimization")
            recommendations.append("Your performance suggests readiness for higher-tier features")
            
        elif user_type == "CAUTIOUS":
            recommendations.append("Your low execution rate suggests hesitation - consider starting with demo trades")
            recommendations.append("Focus on building confidence with smaller position sizes")
            
        elif user_type == "STRUGGLING":
            recommendations.append("Review risk management principles - win rate needs improvement")
            recommendations.append("Consider focusing on fewer, higher-quality signals")
            recommendations.append("Educational resources on pattern recognition recommended")
            
        elif user_type == "HIGH_ACTIVITY":
            if win_rate < 50:
                recommendations.append("High activity but poor results - focus on quality over quantity")
            else:
                recommendations.append("Good activity level - maintain current execution pace")
                
        elif user_type == "SKILLED":
            recommendations.append("Good performance - consider increasing position sizes gradually")
            recommendations.append("You may benefit from more frequent trading opportunities")
        
        # Execution rate specific recommendations
        if execution_rate < 20:
            recommendations.append("Very low execution rate - consider reviewing missed opportunities")
        elif execution_rate > 90:
            recommendations.append("Very high execution rate - ensure proper signal selection")
        
        return recommendations
    
    def identify_user_education_needs(self) -> Dict[str, List[str]]:
        """Identify what education each user type needs"""
        
        education_map = {
            "NEW_TRADER": [
                "Basic pattern recognition course",
                "Risk management fundamentals",
                "Platform navigation tutorial",
                "Demo account practice"
            ],
            "CAUTIOUS": [
                "Confidence building exercises",
                "Signal quality assessment guide",
                "Position sizing psychology",
                "Success story case studies"
            ],
            "STRUGGLING": [
                "Advanced risk management course",
                "Trade analysis and review process", 
                "Psychology of trading mistakes",
                "One-on-one mentoring session"
            ],
            "POWER_USER": [
                "Advanced trading strategies",
                "Portfolio optimization techniques",
                "Market regime analysis",
                "Mentoring other traders"
            ],
            "HIGH_ACTIVITY": [
                "Quality vs quantity training",
                "Signal filtering techniques",
                "Overtrading prevention strategies"
            ],
            "SKILLED": [
                "Advanced pattern analysis",
                "Multi-timeframe strategies",
                "Position sizing optimization"
            ]
        }
        
        return education_map
    
    def generate_cohort_analysis(self) -> Dict:
        """Generate analysis across all users"""
        
        user_registry = self.load_user_registry()
        cohort_stats = defaultdict(list)
        
        for user_id in user_registry.keys():
            user_analysis = self.analyze_user_patterns(user_id)
            user_type = user_analysis['user_type']
            
            cohort_stats[user_type].append({
                'user_id': user_id,
                'execution_rate': user_analysis['execution_rate'],
                'win_rate': user_analysis['win_rate'],
                'total_trades': user_analysis['total_trades']
            })
        
        # Calculate cohort averages
        cohort_summary = {}
        for user_type, users in cohort_stats.items():
            if users:
                cohort_summary[user_type] = {
                    'count': len(users),
                    'avg_execution_rate': statistics.mean(u['execution_rate'] for u in users),
                    'avg_win_rate': statistics.mean(u['win_rate'] for u in users),
                    'avg_total_trades': statistics.mean(u['total_trades'] for u in users),
                    'users': users
                }
        
        return cohort_summary

def main():
    """Run user behavior analysis"""
    analytics = UserBehaviorAnalytics()
    
    print("=== USER BEHAVIOR ANALYTICS ===")
    
    # Example: Analyze specific user (replace with actual user ID)
    user_registry = analytics.load_user_registry()
    
    if user_registry:
        # Analyze all users
        for user_id in list(user_registry.keys())[:5]:  # Limit to first 5 for demo
            print(f"\nAnalyzing user: {user_id}")
            user_analysis = analytics.analyze_user_patterns(user_id)
            print(json.dumps(user_analysis, indent=2))
    
    # Generate cohort analysis
    print("\n=== COHORT ANALYSIS ===")
    cohort_analysis = analytics.generate_cohort_analysis()
    print(json.dumps(cohort_analysis, indent=2))
    
    # Save report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(f'/root/HydraX-v2/reports/user_behavior_analysis_{timestamp}.json', 'w') as f:
        json.dump(cohort_analysis, f, indent=2)
    
    print(f"\n✅ User behavior analysis complete. Report saved to reports/user_behavior_analysis_{timestamp}.json")

if __name__ == "__main__":
    main()