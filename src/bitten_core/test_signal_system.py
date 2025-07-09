"""
Test Signal System for HydraX - 60 TCS Special Signals
Provides rare "test signals" to reward attentive users
"""

import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import json
import os
import asyncio
from enum import Enum

logger = logging.getLogger(__name__)


class TestSignalResult(Enum):
    """Possible outcomes of taking a test signal"""
    PASSED = "passed"  # User didn't take the signal
    HIT_SL = "hit_sl"  # User took it and hit stop loss
    WON = "won"  # User took it and won (30% chance)
    PENDING = "pending"  # Signal sent, waiting for response


@dataclass
class TestSignalRecord:
    """Record of a test signal"""
    signal_id: str
    timestamp: datetime
    pair: str
    users_sent: List[str] = field(default_factory=list)
    results: Dict[str, TestSignalResult] = field(default_factory=dict)
    user_actions: Dict[str, Dict] = field(default_factory=dict)  # user_id -> action data
    

@dataclass
class TestSignalStats:
    """User statistics for test signals"""
    user_id: str
    total_received: int = 0
    total_passed: int = 0
    total_taken: int = 0
    total_won: int = 0
    total_hit_sl: int = 0
    extra_shots_earned: int = 0
    xp_bonuses_earned: int = 0
    achievement_unlocked: bool = False
    last_test_signal: Optional[datetime] = None
    attention_score: float = 100.0  # How attentive the user is


class TestSignalAchievements:
    """Special achievements for test signals"""
    
    ACHIEVEMENTS = {
        "sharp_eye": {
            "id": "test_signal_sharp_eye",
            "name": "🎯 Sharp Eye",
            "description": "Successfully identified and passed 5 test signals",
            "requirement": {"passed": 5},
            "xp_reward": 100,
            "badge": "🎯"
        },
        "lucky_gambit": {
            "id": "test_signal_lucky_gambit", 
            "name": "🎲 Lucky Gambit",
            "description": "Won a 60 TCS test signal (30% chance)",
            "requirement": {"won": 1},
            "xp_reward": 200,
            "badge": "🎲"
        },
        "master_detector": {
            "id": "test_signal_master_detector",
            "name": "🔍 Master Detector", 
            "description": "Identified and passed 20 test signals",
            "requirement": {"passed": 20},
            "xp_reward": 500,
            "badge": "🔍"
        },
        "risk_taker": {
            "id": "test_signal_risk_taker",
            "name": "⚡ Calculated Risk Taker",
            "description": "Won 3 test signals by taking the gamble",
            "requirement": {"won": 3},
            "xp_reward": 750,
            "badge": "⚡"
        }
    }


class TestSignalSystem:
    """
    Manages the 60 TCS test signal system
    Rewards attentive users who can identify obviously bad signals
    """
    
    def __init__(self, data_dir: str = "data/test_signals"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # File paths
        self.history_file = os.path.join(data_dir, "test_signal_history.json")
        self.stats_file = os.path.join(data_dir, "user_test_stats.json")
        self.config_file = os.path.join(data_dir, "test_signal_config.json")
        
        # Load data
        self.signal_history: List[TestSignalRecord] = self._load_history()
        self.user_stats: Dict[str, TestSignalStats] = self._load_stats()
        self.config = self._load_config()
        
        # Signal generation settings
        self.last_test_signal = None
        self.min_days_between = self.config.get("min_days_between", 3)
        self.max_days_between = self.config.get("max_days_between", 5)
        self.next_signal_time = self._calculate_next_signal_time()
        
        # Achievements
        self.achievements = TestSignalAchievements()
        
    def _load_config(self) -> Dict:
        """Load test signal configuration"""
        default_config = {
            "enabled": True,
            "min_days_between": 3,
            "max_days_between": 5,
            "base_xp_pass_reward": 15,
            "base_xp_win_reward": 50,
            "win_probability": 0.30,
            "sl_distance_pips": 60,
            "tp_distance_pips": 20,  # Intentionally bad R:R
            "max_active_per_week": 2,
            "eligible_pairs": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"],
            "eligible_tiers": ["nibbler", "fang", "commander"],
            "special_hours": [3, 4, 21, 22]  # Hours when test signals are more likely
        }
        
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                loaded = json.load(f)
                default_config.update(loaded)
                
        return default_config
    
    def _load_history(self) -> List[TestSignalRecord]:
        """Load test signal history"""
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f:
                data = json.load(f)
                return [self._dict_to_record(d) for d in data]
        return []
    
    def _load_stats(self) -> Dict[str, TestSignalStats]:
        """Load user statistics"""
        if os.path.exists(self.stats_file):
            with open(self.stats_file, 'r') as f:
                data = json.load(f)
                return {
                    user_id: self._dict_to_stats(d) 
                    for user_id, d in data.items()
                }
        return {}
    
    def _dict_to_record(self, data: Dict) -> TestSignalRecord:
        """Convert dict to TestSignalRecord"""
        record = TestSignalRecord(
            signal_id=data["signal_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            pair=data["pair"],
            users_sent=data.get("users_sent", []),
            user_actions=data.get("user_actions", {})
        )
        
        # Convert result strings to enums
        for user_id, result in data.get("results", {}).items():
            record.results[user_id] = TestSignalResult(result)
            
        return record
    
    def _dict_to_stats(self, data: Dict) -> TestSignalStats:
        """Convert dict to TestSignalStats"""
        stats = TestSignalStats(user_id=data["user_id"])
        for key, value in data.items():
            if key == "last_test_signal" and value:
                setattr(stats, key, datetime.fromisoformat(value))
            else:
                setattr(stats, key, value)
        return stats
    
    def _save_history(self):
        """Save test signal history"""
        data = []
        for record in self.signal_history[-100:]:  # Keep last 100
            d = {
                "signal_id": record.signal_id,
                "timestamp": record.timestamp.isoformat(),
                "pair": record.pair,
                "users_sent": record.users_sent,
                "results": {k: v.value for k, v in record.results.items()},
                "user_actions": record.user_actions
            }
            data.append(d)
            
        with open(self.history_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _save_stats(self):
        """Save user statistics"""
        data = {}
        for user_id, stats in self.user_stats.items():
            d = stats.__dict__.copy()
            if d.get("last_test_signal"):
                d["last_test_signal"] = d["last_test_signal"].isoformat()
            data[user_id] = d
            
        with open(self.stats_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _calculate_next_signal_time(self) -> datetime:
        """Calculate when next test signal should appear"""
        if self.signal_history:
            last_signal = self.signal_history[-1].timestamp
        else:
            last_signal = datetime.now()
            
        days_to_add = random.uniform(self.min_days_between, self.max_days_between)
        next_time = last_signal + timedelta(days=days_to_add)
        
        # Prefer special hours
        if random.random() < 0.7:  # 70% chance to use special hour
            special_hour = random.choice(self.config["special_hours"])
            next_time = next_time.replace(hour=special_hour, minute=random.randint(0, 59))
            
        return next_time
    
    def should_generate_test_signal(self) -> bool:
        """Check if it's time to generate a test signal"""
        if not self.config.get("enabled", True):
            return False
            
        # Check weekly limit
        week_ago = datetime.now() - timedelta(days=7)
        recent_signals = [s for s in self.signal_history if s.timestamp > week_ago]
        if len(recent_signals) >= self.config["max_active_per_week"]:
            return False
            
        # Check if it's time
        return datetime.now() >= self.next_signal_time
    
    def generate_test_signal(self, base_signal: Dict) -> Optional[Dict]:
        """
        Generate a test signal based on a base signal
        Makes it obviously bad with 60 pip SL and terrible R:R
        """
        if not self.should_generate_test_signal():
            return None
            
        # Only use eligible pairs
        if base_signal["pair"] not in self.config["eligible_pairs"]:
            return None
            
        # Create the test signal
        test_signal = base_signal.copy()
        test_signal["is_test_signal"] = True
        test_signal["test_signal_id"] = f"TEST_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Modify SL to be exactly 60 pips
        pip_value = 0.0001 if "JPY" not in base_signal["pair"] else 0.01
        
        if base_signal["action"].upper() == "BUY":
            test_signal["sl"] = base_signal["entry"] - (60 * pip_value)
            test_signal["tp"] = base_signal["entry"] + (20 * pip_value)  # Bad R:R
        else:
            test_signal["sl"] = base_signal["entry"] + (60 * pip_value)
            test_signal["tp"] = base_signal["entry"] - (20 * pip_value)  # Bad R:R
            
        # Add test signal indicators
        test_signal["tcs_distance"] = 60
        test_signal["risk_reward_ratio"] = 0.33  # 1:0.33 terrible ratio
        
        # Add subtle hints it's a test
        test_signal["metadata"]["test_hints"] = {
            "exact_sl_pips": 60,
            "poor_rr": True,
            "generated_at_odd_hour": datetime.now().hour in self.config["special_hours"]
        }
        
        # Record the signal
        record = TestSignalRecord(
            signal_id=test_signal["test_signal_id"],
            timestamp=datetime.now(),
            pair=test_signal["pair"]
        )
        self.signal_history.append(record)
        
        # Update next signal time
        self.next_signal_time = self._calculate_next_signal_time()
        
        # Save history
        self._save_history()
        
        logger.info(f"Generated test signal {test_signal['test_signal_id']} for {test_signal['pair']}")
        
        return test_signal
    
    def record_signal_sent(self, signal_id: str, user_id: str):
        """Record that a test signal was sent to a user"""
        # Find the signal record
        for record in self.signal_history:
            if record.signal_id == signal_id:
                if user_id not in record.users_sent:
                    record.users_sent.append(user_id)
                record.results[user_id] = TestSignalResult.PENDING
                
                # Initialize user stats if needed
                if user_id not in self.user_stats:
                    self.user_stats[user_id] = TestSignalStats(user_id=user_id)
                    
                self.user_stats[user_id].total_received += 1
                self.user_stats[user_id].last_test_signal = datetime.now()
                
                self._save_history()
                self._save_stats()
                break
    
    def record_user_action(self, signal_id: str, user_id: str, action: str, 
                          trade_result: Optional[str] = None) -> Dict[str, Any]:
        """
        Record user's action on a test signal
        Returns rewards earned
        """
        rewards = {
            "xp_earned": 0,
            "extra_shots": 0,
            "achievement": None,
            "message": ""
        }
        
        # Find the signal record
        signal_record = None
        for record in self.signal_history:
            if record.signal_id == signal_id:
                signal_record = record
                break
                
        if not signal_record or user_id not in signal_record.users_sent:
            return rewards
            
        # Get user stats
        if user_id not in self.user_stats:
            self.user_stats[user_id] = TestSignalStats(user_id=user_id)
        
        user_stats = self.user_stats[user_id]
        
        # Process action
        if action == "passed":
            # User correctly identified and passed the test signal
            signal_record.results[user_id] = TestSignalResult.PASSED
            user_stats.total_passed += 1
            
            # XP reward for being attentive
            xp_reward = self.config["base_xp_pass_reward"]
            if user_stats.total_passed % 5 == 0:  # Bonus every 5
                xp_reward *= 2
                
            rewards["xp_earned"] = xp_reward
            user_stats.xp_bonuses_earned += xp_reward
            user_stats.attention_score = min(100, user_stats.attention_score + 5)
            
            rewards["message"] = f"🎯 Well spotted! You correctly identified the test signal. +{xp_reward} XP"
            
        elif action == "taken":
            # User took the bait
            user_stats.total_taken += 1
            user_stats.attention_score = max(0, user_stats.attention_score - 10)
            
            if trade_result == "hit_sl":
                # Hit stop loss - give extra shot as consolation
                signal_record.results[user_id] = TestSignalResult.HIT_SL
                user_stats.total_hit_sl += 1
                user_stats.extra_shots_earned += 1
                rewards["extra_shots"] = 1
                rewards["message"] = "💥 Test signal hit SL! Don't worry, you earned an extra shot for today."
                
            elif trade_result == "won":
                # Lucky win (30% chance)
                signal_record.results[user_id] = TestSignalResult.WON
                user_stats.total_won += 1
                
                # Big XP reward
                xp_reward = self.config["base_xp_win_reward"]
                rewards["xp_earned"] = xp_reward
                user_stats.xp_bonuses_earned += xp_reward
                
                rewards["message"] = f"🎲 Lucky win on the test signal! +{xp_reward} XP"
        
        # Check for achievements
        achievement = self._check_achievements(user_stats)
        if achievement:
            rewards["achievement"] = achievement
            rewards["xp_earned"] += achievement.get("xp_reward", 0)
            user_stats.achievement_unlocked = True
            
        # Record the action
        signal_record.user_actions[user_id] = {
            "action": action,
            "result": trade_result,
            "timestamp": datetime.now().isoformat(),
            "rewards": rewards
        }
        
        # Save everything
        self._save_history()
        self._save_stats()
        
        return rewards
    
    def _check_achievements(self, user_stats: TestSignalStats) -> Optional[Dict]:
        """Check if user earned any achievements"""
        for achievement_id, achievement in self.achievements.ACHIEVEMENTS.items():
            req = achievement["requirement"]
            
            # Check if already earned (simple check - in production would track per achievement)
            if user_stats.achievement_unlocked:
                continue
                
            # Check requirements
            if "passed" in req and user_stats.total_passed >= req["passed"]:
                return achievement
            elif "won" in req and user_stats.total_won >= req["won"]:
                return achievement
                
        return None
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get formatted user statistics"""
        if user_id not in self.user_stats:
            return {
                "has_received_test_signals": False,
                "stats": None
            }
            
        stats = self.user_stats[user_id]
        
        return {
            "has_received_test_signals": True,
            "stats": {
                "total_received": stats.total_received,
                "total_passed": stats.total_passed,
                "total_taken": stats.total_taken,
                "pass_rate": (stats.total_passed / stats.total_received * 100) if stats.total_received > 0 else 0,
                "total_won": stats.total_won,
                "total_hit_sl": stats.total_hit_sl,
                "extra_shots_earned": stats.extra_shots_earned,
                "xp_bonuses_earned": stats.xp_bonuses_earned,
                "attention_score": stats.attention_score,
                "last_test_signal": stats.last_test_signal.isoformat() if stats.last_test_signal else None
            }
        }
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get test signal attention leaderboard"""
        sorted_users = sorted(
            self.user_stats.values(),
            key=lambda x: (x.total_passed, x.attention_score),
            reverse=True
        )
        
        leaderboard = []
        for i, stats in enumerate(sorted_users[:limit]):
            leaderboard.append({
                "rank": i + 1,
                "user_id": stats.user_id,
                "signals_passed": stats.total_passed,
                "attention_score": stats.attention_score,
                "pass_rate": (stats.total_passed / stats.total_received * 100) if stats.total_received > 0 else 0,
                "lucky_wins": stats.total_won
            })
            
        return leaderboard
    
    def should_send_to_user(self, user_id: str, user_tier: str) -> bool:
        """Check if test signal should be sent to this user"""
        # Check if tier is eligible
        if user_tier not in self.config["eligible_tiers"]:
            return False
            
        # Don't spam the same user
        if user_id in self.user_stats:
            stats = self.user_stats[user_id]
            if stats.last_test_signal:
                days_since_last = (datetime.now() - stats.last_test_signal).days
                if days_since_last < 3:  # At least 3 days between test signals per user
                    return False
                    
        # Random selection - not everyone gets it
        return random.random() < 0.3  # 30% chance per eligible user
    
    def simulate_trade_result(self) -> str:
        """Simulate the result of taking a test signal"""
        if random.random() < self.config["win_probability"]:
            return "won"
        else:
            return "hit_sl"


# Create global instance
test_signal_system = TestSignalSystem()