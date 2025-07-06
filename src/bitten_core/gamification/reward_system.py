# reward_system.py
"""
BITTEN Positive Reinforcement Reward System
A healthy gamification system that encourages good trading practices through positive reinforcement.
"""

import random
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

class RewardState(Enum):
    """The user's current engagement state"""
    MOTIVATED = "motivated"        # Ready to learn and improve
    ACCOMPLISHED = "accomplished"  # Feeling successful
    LEARNING = "learning"         # In growth phase
    CONSISTENT = "consistent"     # Building good habits

@dataclass
class XPReward:
    """A positive XP reward event"""
    base_xp: int
    multiplier: float
    total_xp: int
    achievement_type: str
    encouraging_message: str
    next_goal: str

class PositiveRewardEngine:
    """
    Encourages good trading habits through positive reinforcement and achievement recognition.
    """
    
    def __init__(self):
        self.user_progress = {}  # user_id -> progress data
        self.achievement_history = {}  # user_id -> List[XPReward]
        
        # Positive achievement patterns
        self.achievement_types = {
            "consistency": "Building consistent trading habits",
            "risk_management": "Excellent risk management",
            "learning": "Continuous learning and improvement", 
            "patience": "Demonstrating trading patience",
            "discipline": "Following trading plan",
            "milestone": "Reaching important milestone"
        }
        
        # Encouraging bot messages
        self.encouraging_messages = {
            "consistency": [
                "Great job maintaining consistent trading habits!",
                "Your discipline is paying off - keep it up!",
                "Consistency is the key to long-term success!"
            ],
            "risk_management": [
                "Excellent risk management - protecting your capital!",
                "Smart position sizing - you're learning well!",
                "Good job managing your exposure!"
            ],
            "learning": [
                "Your progress shows real learning - well done!",
                "Every trade teaches us something valuable!",
                "You're developing real trading skills!"
            ],
            "patience": [
                "Patience in trading shows real maturity!",
                "Good trades come to those who wait!",
                "Your patience is a valuable trading asset!"
            ],
            "discipline": [
                "Following your plan shows great discipline!",
                "Stick to your strategy - it's working!",
                "Disciplined traders are successful traders!"
            ]
        }
    
    def calculate_achievement_reward(self, user_id: str, achievement_data: Dict) -> XPReward:
        """
        Calculate XP rewards for positive achievements
        """
        achievement_type = achievement_data.get('type', 'consistency')
        base_xp = achievement_data.get('base_xp', 50)
        
        # Multipliers for different achievements
        multipliers = {
            "consistency": 1.2,      # 20% bonus for consistency
            "risk_management": 1.5,  # 50% bonus for good risk management
            "learning": 1.3,         # 30% bonus for learning
            "patience": 1.4,         # 40% bonus for patience
            "discipline": 1.6,       # 60% bonus for discipline
            "milestone": 2.0         # 100% bonus for milestones
        }
        
        multiplier = multipliers.get(achievement_type, 1.0)
        final_xp = int(base_xp * multiplier)
        
        # Generate encouraging message
        messages = self.encouraging_messages.get(achievement_type, ["Great job!"])
        message = random.choice(messages)
        
        # Set next goal
        next_goal = self.generate_next_goal(user_id, achievement_type)
        
        reward = XPReward(
            base_xp=base_xp,
            multiplier=multiplier,
            total_xp=final_xp,
            achievement_type=achievement_type,
            encouraging_message=message,
            next_goal=next_goal
        )
        
        # Track progress
        if user_id not in self.achievement_history:
            self.achievement_history[user_id] = []
        self.achievement_history[user_id].append(reward)
        
        return reward
    
    def generate_next_goal(self, user_id: str, current_achievement: str) -> str:
        """Generate next positive goal for the user"""
        goals = {
            "consistency": "Continue your consistent trading for 5 more days",
            "risk_management": "Try to maintain this risk level for the next week",
            "learning": "Explore a new trading concept or strategy",
            "patience": "Practice patience in your next 3 trades",
            "discipline": "Follow your trading plan for another week",
            "milestone": "Set your next meaningful trading milestone"
        }
        
        return goals.get(current_achievement, "Keep up the great work!")
    
    def get_user_progress_summary(self, user_id: str) -> Dict:
        """Get positive progress summary for user"""
        if user_id not in self.achievement_history:
            return {
                "total_achievements": 0,
                "total_xp_earned": 0,
                "favorite_achievement": "None yet",
                "encouragement": "Welcome! Start trading to earn your first achievements!"
            }
        
        history = self.achievement_history[user_id]
        
        # Calculate stats
        total_xp = sum(achievement.total_xp for achievement in history)
        achievement_counts = {}
        for achievement in history:
            achievement_type = achievement.achievement_type
            achievement_counts[achievement_type] = achievement_counts.get(achievement_type, 0) + 1
        
        favorite = max(achievement_counts.items(), key=lambda x: x[1])[0] if achievement_counts else "None"
        
        return {
            "total_achievements": len(history),
            "total_xp_earned": total_xp,
            "favorite_achievement": favorite,
            "achievement_breakdown": achievement_counts,
            "encouragement": "You're making great progress! Keep up the positive momentum!"
        }

# Simple motivation system without manipulation
class MotivationSystem:
    """Provides positive motivation and encouragement"""
    
    def __init__(self):
        self.motivational_quotes = [
            "Every expert was once a beginner!",
            "Success in trading comes from learning, not luck!",
            "Your discipline today builds your success tomorrow!",
            "Good traders are made through practice and patience!",
            "Risk management is your best friend in trading!",
            "Consistency beats perfection every time!",
            "Learn from every trade, win or lose!",
            "Trading is a marathon, not a sprint!"
        ]
    
    def get_daily_motivation(self) -> str:
        """Get positive daily motivation"""
        return random.choice(self.motivational_quotes)
    
    def get_achievement_celebration(self, achievement_type: str) -> str:
        """Celebrate user achievements positively"""
        celebrations = {
            "consistency": "🎉 Consistency Champion! Your steady approach is building real skills!",
            "risk_management": "🛡️ Risk Master! You're protecting your capital like a pro!",
            "learning": "📚 Knowledge Seeker! Your commitment to learning is impressive!",
            "patience": "⏰ Patience Pays! Your measured approach shows real wisdom!",
            "discipline": "💪 Discipline Warrior! Following your plan shows real strength!"
        }
        
        return celebrations.get(achievement_type, "🌟 Great achievement! Keep up the excellent work!")