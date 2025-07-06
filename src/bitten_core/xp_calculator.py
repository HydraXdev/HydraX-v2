"""
XP Calculator for HydraX Trading System

This module centralizes all XP calculations including:
- Base XP rewards for different trading outcomes
- Multiplier stacking with caps
- Early exit penalties
- Milestone progression tracking
"""

from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import math


class ExitType(Enum):
    """Types of trade exits"""
    NORMAL = "normal"
    STOP_LOSS = "stop_loss"
    PARACHUTE = "parachute"
    PANIC = "panic"
    TIMEOUT = "timeout"


class TradingMilestone(Enum):
    """Trading milestones with XP requirements"""
    NOVICE = 0
    APPRENTICE = 1000
    TRADER = 5000
    EXPERT = 15000
    MASTER = 30000
    ELITE = 50000


class EducationActivity(Enum):
    """Types of educational activities"""
    # Core Learning Activities
    COMPLETE_LESSON = "complete_lesson"
    WATCH_VIDEO = "watch_video"
    READ_ARTICLE = "read_article"
    COMPLETE_QUIZ = "complete_quiz"
    COMPLETE_MODULE = "complete_module"
    
    # Interactive Activities
    JOIN_WEBINAR = "join_webinar"
    ATTEND_WORKSHOP = "attend_workshop"
    PARTICIPATE_DISCUSSION = "participate_discussion"
    ASK_QUESTION = "ask_question"
    ANSWER_QUESTION = "answer_question"
    
    # Practice Activities
    PAPER_TRADE = "paper_trade"
    BACKTEST_STRATEGY = "backtest_strategy"
    ANALYZE_CHART = "analyze_chart"
    JOURNAL_ENTRY = "journal_entry"
    
    # Advanced Activities
    CREATE_STRATEGY = "create_strategy"
    MENTOR_SESSION = "mentor_session"
    TEACH_OTHERS = "teach_others"
    CONTENT_CREATION = "content_creation"


@dataclass
class XPCalculation:
    """Result of XP calculation"""
    base_xp: int
    multipliers: Dict[str, float]
    total_multiplier: float
    final_xp: int
    penalties: Dict[str, int]
    net_xp: int
    milestone_progress: Dict[str, any]


class XPCalculator:
    """Centralized XP calculation system"""
    
    # Base XP rewards
    BASE_XP = {
        "win": 100,
        "loss": 50,
        "breakeven": 75,
        "streak_bonus": 25,  # per win in streak
        "performance_bonus": 50,  # for exceptional trades
    }
    
    # Education XP rewards (balanced to encourage learning without exploitation)
    EDUCATION_XP_TABLE = {
        # Core Learning Activities (5-25 XP base)
        EducationActivity.COMPLETE_LESSON: {"base": 15, "cooldown_hours": 0, "daily_cap": 150},
        EducationActivity.WATCH_VIDEO: {"base": 10, "cooldown_hours": 0, "daily_cap": 100},
        EducationActivity.READ_ARTICLE: {"base": 5, "cooldown_hours": 0, "daily_cap": 50},
        EducationActivity.COMPLETE_QUIZ: {"base": 20, "cooldown_hours": 1, "daily_cap": 100},
        EducationActivity.COMPLETE_MODULE: {"base": 50, "cooldown_hours": 4, "daily_cap": 150},
        
        # Interactive Activities (10-30 XP base)
        EducationActivity.JOIN_WEBINAR: {"base": 25, "cooldown_hours": 24, "daily_cap": 50},
        EducationActivity.ATTEND_WORKSHOP: {"base": 30, "cooldown_hours": 24, "daily_cap": 60},
        EducationActivity.PARTICIPATE_DISCUSSION: {"base": 10, "cooldown_hours": 0.5, "daily_cap": 80},
        EducationActivity.ASK_QUESTION: {"base": 15, "cooldown_hours": 1, "daily_cap": 60},
        EducationActivity.ANSWER_QUESTION: {"base": 20, "cooldown_hours": 0.5, "daily_cap": 100},
        
        # Practice Activities (15-35 XP base)
        EducationActivity.PAPER_TRADE: {"base": 20, "cooldown_hours": 0, "daily_cap": 200},
        EducationActivity.BACKTEST_STRATEGY: {"base": 25, "cooldown_hours": 2, "daily_cap": 100},
        EducationActivity.ANALYZE_CHART: {"base": 15, "cooldown_hours": 0.5, "daily_cap": 120},
        EducationActivity.JOURNAL_ENTRY: {"base": 20, "cooldown_hours": 12, "daily_cap": 40},
        
        # Advanced Activities (30-75 XP base)
        EducationActivity.CREATE_STRATEGY: {"base": 50, "cooldown_hours": 24, "daily_cap": 100},
        EducationActivity.MENTOR_SESSION: {"base": 40, "cooldown_hours": 24, "daily_cap": 80},
        EducationActivity.TEACH_OTHERS: {"base": 35, "cooldown_hours": 4, "daily_cap": 140},
        EducationActivity.CONTENT_CREATION: {"base": 75, "cooldown_hours": 48, "daily_cap": 150},
    }
    
    # Education multipliers
    EDUCATION_MULTIPLIERS = {
        # Streak multipliers (compound bonuses)
        "daily_streak": {
            "base": 1.0,
            "increment": 0.05,  # +5% per day
            "max": 2.0,  # Cap at 100% bonus (20 days)
            "reset_hours": 48  # Reset if missed 2 days
        },
        
        # Group activity multipliers
        "squad_bonus": {
            "small": 1.1,  # 2-4 people
            "medium": 1.2,  # 5-9 people
            "large": 1.3,   # 10+ people
            "max": 1.3
        },
        
        # Mentor/teaching multipliers
        "mentor_bonus": {
            "helping_others": 1.25,
            "receiving_help": 1.15,
            "verified_answer": 1.5  # When answer is marked as helpful
        },
        
        # Excellence multipliers
        "perfect_score": {
            "quiz": 1.5,
            "module": 1.75,
            "assessment": 2.0
        },
        
        # Tier progression multipliers
        "difficulty_bonus": {
            "beginner": 1.0,
            "intermediate": 1.25,
            "advanced": 1.5,
            "expert": 1.75
        },
        
        # Special event multipliers
        "event_multiplier": {
            "double_xp_weekend": 2.0,
            "learning_marathon": 1.5,
            "community_challenge": 1.75
        }
    }
    
    # Achievement-based XP bonuses (one-time rewards)
    ACHIEVEMENT_BONUSES = {
        "first_lesson": 50,
        "first_perfect_quiz": 100,
        "week_streak": 200,
        "month_streak": 500,
        "help_10_traders": 300,
        "complete_course": 1000,
        "create_popular_content": 500,  # 50+ likes/views
        "mentor_badge": 750,
        "scholar_badge": 1000,  # Complete all courses in tier
    }
    
    # Multiplier sources and their max values
    MULTIPLIERS = {
        "win_rate": {"max": 2.0, "base": 1.0},  # 1.0-2.0x based on win rate
        "streak": {"max": 2.0, "base": 1.0},     # 1.0-2.0x based on streak
        "volume": {"max": 1.5, "base": 1.0},     # 1.0-1.5x based on volume
        "consistency": {"max": 1.5, "base": 1.0}, # 1.0-1.5x based on consistency
        "risk_reward": {"max": 1.5, "base": 1.0}, # 1.0-1.5x based on R:R
        "special_event": {"max": 2.0, "base": 1.0}, # Special events/challenges
    }
    
    # Maximum total multipliers
    MAX_TOTAL_MULTIPLIER = 10.0
    MAX_EDUCATION_MULTIPLIER = 5.0  # Lower cap for education to prevent exploitation
    
    # Penalties
    PENALTIES = {
        "panic_exit": -50,
        "overtrading": -25,
        "revenge_trading": -30,
    }
    
    # Approved exit protocols (no penalty)
    APPROVED_EXITS = {ExitType.STOP_LOSS, ExitType.PARACHUTE, ExitType.TIMEOUT}
    
    def __init__(self):
        self.milestone_xp = {milestone: milestone.value for milestone in TradingMilestone}
        self.education_activity_tracker = {}  # Track last activity times for cooldowns
        self.daily_education_xp = {}  # Track daily XP earned per activity
    
    def calculate_trade_xp(
        self,
        trade_result: str,  # "win", "loss", "breakeven"
        exit_type: ExitType,
        multipliers: Optional[Dict[str, float]] = None,
        current_streak: int = 0,
        performance_metrics: Optional[Dict[str, float]] = None
    ) -> XPCalculation:
        """
        Calculate XP for a single trade
        
        Args:
            trade_result: Outcome of the trade
            exit_type: How the trade was exited
            multipliers: Active multipliers to apply
            current_streak: Current win streak
            performance_metrics: Additional performance data
            
        Returns:
            XPCalculation with detailed breakdown
        """
        # Base XP
        base_xp = self.BASE_XP.get(trade_result, 0)
        
        # Add streak bonus for wins
        if trade_result == "win" and current_streak > 0:
            base_xp += self.BASE_XP["streak_bonus"] * min(current_streak, 5)  # Cap at 5
        
        # Calculate multipliers
        active_multipliers = self._calculate_multipliers(
            multipliers or {},
            performance_metrics or {}
        )
        
        # Apply multiplier cap
        total_multiplier = self._apply_multiplier_cap(active_multipliers)
        
        # Calculate final XP
        final_xp = int(base_xp * total_multiplier)
        
        # Apply penalties
        penalties = self._calculate_penalties(exit_type, performance_metrics or {})
        net_xp = final_xp + sum(penalties.values())
        
        # Ensure non-negative XP
        net_xp = max(0, net_xp)
        
        return XPCalculation(
            base_xp=base_xp,
            multipliers=active_multipliers,
            total_multiplier=total_multiplier,
            final_xp=final_xp,
            penalties=penalties,
            net_xp=net_xp,
            milestone_progress={}
        )
    
    def _calculate_multipliers(
        self,
        active_multipliers: Dict[str, float],
        performance_metrics: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate all active multipliers with bounds checking"""
        calculated = {}
        
        for mult_type, config in self.MULTIPLIERS.items():
            if mult_type in active_multipliers:
                # Clamp to allowed range
                value = max(config["base"], min(config["max"], active_multipliers[mult_type]))
                calculated[mult_type] = value
        
        # Calculate performance-based multipliers
        if "win_rate" in performance_metrics:
            win_rate = performance_metrics["win_rate"]
            # Linear scale: 50% = 1.0x, 80% = 2.0x
            calculated["win_rate"] = 1.0 + (win_rate - 0.5) * (1.0 / 0.3)
            calculated["win_rate"] = max(1.0, min(2.0, calculated["win_rate"]))
        
        if "avg_rr" in performance_metrics:
            avg_rr = performance_metrics["avg_rr"]
            # Scale based on average R:R (2:1 = 1.25x, 3:1 = 1.5x)
            calculated["risk_reward"] = 1.0 + min(0.5, (avg_rr - 1.0) * 0.25)
        
        return calculated
    
    def _apply_multiplier_cap(self, multipliers: Dict[str, float]) -> float:
        """Apply stacking cap to total multiplier"""
        if not multipliers:
            return 1.0
        
        # Multiplicative stacking
        total = 1.0
        for value in multipliers.values():
            total *= value
        
        # Apply cap
        return min(total, self.MAX_TOTAL_MULTIPLIER)
    
    def _calculate_penalties(
        self,
        exit_type: ExitType,
        performance_metrics: Dict[str, float]
    ) -> Dict[str, int]:
        """Calculate any penalties to apply"""
        penalties = {}
        
        # Early exit penalty
        if exit_type == ExitType.PANIC and exit_type not in self.APPROVED_EXITS:
            penalties["panic_exit"] = self.PENALTIES["panic_exit"]
        
        # Overtrading penalty
        if performance_metrics.get("trades_today", 0) > 10:
            penalties["overtrading"] = self.PENALTIES["overtrading"]
        
        # Revenge trading detection
        if performance_metrics.get("losses_in_row", 0) >= 3:
            penalties["revenge_trading"] = self.PENALTIES["revenge_trading"]
        
        return penalties
    
    def calculate_milestone_progress(
        self,
        current_xp: int,
        daily_avg_xp: float,
        current_multipliers: Dict[str, float]
    ) -> Dict[str, any]:
        """
        Calculate progress towards milestones and time estimates
        
        Args:
            current_xp: Current total XP
            daily_avg_xp: Average XP earned per day
            current_multipliers: Currently active multipliers
            
        Returns:
            Dict with milestone progress and estimates
        """
        current_milestone = self._get_current_milestone(current_xp)
        next_milestone = self._get_next_milestone(current_xp)
        
        progress = {
            "current_milestone": current_milestone.name,
            "current_milestone_xp": current_milestone.value,
            "total_xp": current_xp,
            "milestones": {}
        }
        
        # Calculate progress for each milestone
        for milestone in TradingMilestone:
            if milestone.value <= current_xp:
                progress["milestones"][milestone.name] = {
                    "reached": True,
                    "xp_required": milestone.value,
                    "progress": 100.0
                }
            else:
                xp_needed = milestone.value - current_xp
                days_estimate = self._estimate_days_to_milestone(
                    xp_needed,
                    daily_avg_xp,
                    current_multipliers
                )
                
                progress["milestones"][milestone.name] = {
                    "reached": False,
                    "xp_required": milestone.value,
                    "xp_needed": xp_needed,
                    "progress": (current_xp / milestone.value) * 100,
                    "estimated_days": days_estimate,
                    "estimated_date": (datetime.now() + timedelta(days=days_estimate)).date()
                }
        
        # Overall Elite progression
        elite_progress = (current_xp / TradingMilestone.ELITE.value) * 100
        days_to_elite = self._estimate_days_to_milestone(
            max(0, TradingMilestone.ELITE.value - current_xp),
            daily_avg_xp,
            current_multipliers
        )
        
        progress["elite_progress"] = {
            "percentage": elite_progress,
            "days_remaining": days_to_elite,
            "on_track": 30 <= days_to_elite <= 60 if current_xp < TradingMilestone.ELITE.value else True
        }
        
        return progress
    
    def _get_current_milestone(self, xp: int) -> TradingMilestone:
        """Get the current milestone based on XP"""
        current = TradingMilestone.NOVICE
        for milestone in TradingMilestone:
            if xp >= milestone.value:
                current = milestone
        return current
    
    def _get_next_milestone(self, xp: int) -> Optional[TradingMilestone]:
        """Get the next milestone to reach"""
        for milestone in TradingMilestone:
            if xp < milestone.value:
                return milestone
        return None
    
    def _estimate_days_to_milestone(
        self,
        xp_needed: int,
        daily_avg_xp: float,
        multipliers: Dict[str, float]
    ) -> int:
        """Estimate days to reach a milestone with current progression"""
        if daily_avg_xp <= 0:
            return 999  # Max estimate
        
        # Apply current multiplier average to estimate
        avg_multiplier = self._apply_multiplier_cap(multipliers) if multipliers else 1.0
        effective_daily_xp = daily_avg_xp * avg_multiplier
        
        days = math.ceil(xp_needed / effective_daily_xp)
        return min(days, 999)  # Cap at 999 days
    
    def validate_progression_rate(
        self,
        current_xp: int,
        start_date: datetime,
        target_milestone: TradingMilestone = TradingMilestone.ELITE
    ) -> Dict[str, any]:
        """
        Validate if progression rate is reasonable (30-60 days to Elite)
        
        Args:
            current_xp: Current XP amount
            start_date: When trading started
            target_milestone: Milestone to check against
            
        Returns:
            Validation results and recommendations
        """
        days_elapsed = (datetime.now() - start_date).days or 1
        daily_rate = current_xp / days_elapsed
        
        # Project to target
        projected_days = target_milestone.value / daily_rate if daily_rate > 0 else 999
        
        validation = {
            "current_rate": daily_rate,
            "days_elapsed": days_elapsed,
            "projected_days_to_target": projected_days,
            "is_reasonable": 30 <= projected_days <= 60,
            "recommendation": ""
        }
        
        if projected_days < 30:
            validation["recommendation"] = "Progression too fast - consider reducing multipliers"
        elif projected_days > 60:
            validation["recommendation"] = "Progression too slow - consider increasing base XP or multipliers"
        else:
            validation["recommendation"] = "Progression rate is optimal"
        
        return validation
    
    def calculate_session_summary(
        self,
        trades: List[Dict[str, any]],
        session_multipliers: Dict[str, float]
    ) -> Dict[str, any]:
        """
        Calculate XP summary for a trading session
        
        Args:
            trades: List of trade results
            session_multipliers: Multipliers active for the session
            
        Returns:
            Session XP summary
        """
        total_xp = 0
        total_penalties = 0
        trade_breakdown = []
        
        for trade in trades:
            calc = self.calculate_trade_xp(
                trade_result=trade["result"],
                exit_type=ExitType(trade["exit_type"]),
                multipliers=session_multipliers,
                current_streak=trade.get("streak", 0),
                performance_metrics=trade.get("metrics", {})
            )
            
            total_xp += calc.net_xp
            total_penalties += sum(calc.penalties.values())
            trade_breakdown.append({
                "trade_id": trade.get("id"),
                "xp_earned": calc.net_xp,
                "breakdown": calc
            })
        
        return {
            "session_xp": total_xp,
            "total_penalties": total_penalties,
            "average_xp_per_trade": total_xp / len(trades) if trades else 0,
            "trade_count": len(trades),
            "trade_breakdown": trade_breakdown,
            "effective_multiplier": session_multipliers
        }
    
    def calculate_education_xp(
        self,
        activity: EducationActivity,
        user_id: str,
        performance_data: Optional[Dict[str, any]] = None,
        group_size: int = 0,
        streak_days: int = 0,
        active_events: Optional[List[str]] = None
    ) -> XPCalculation:
        """
        Calculate XP for educational activities with anti-abuse measures
        
        Args:
            activity: Type of educational activity
            user_id: User identifier for tracking
            performance_data: Activity performance (quiz score, etc)
            group_size: Number of participants in group activities
            streak_days: Current daily learning streak
            active_events: List of active special events
            
        Returns:
            XPCalculation with detailed breakdown
        """
        # Check cooldown
        if not self._check_education_cooldown(activity, user_id):
            return XPCalculation(
                base_xp=0,
                multipliers={},
                total_multiplier=0,
                final_xp=0,
                penalties={"cooldown_active": 0},
                net_xp=0,
                milestone_progress={"reason": "Activity on cooldown"}
            )
        
        # Check daily cap
        activity_config = self.EDUCATION_XP_TABLE[activity]
        if not self._check_daily_cap(activity, user_id, activity_config["daily_cap"]):
            return XPCalculation(
                base_xp=0,
                multipliers={},
                total_multiplier=0,
                final_xp=0,
                penalties={"daily_cap_reached": 0},
                net_xp=0,
                milestone_progress={"reason": "Daily cap reached for this activity"}
            )
        
        # Base XP
        base_xp = activity_config["base"]
        
        # Calculate education multipliers
        multipliers = self._calculate_education_multipliers(
            activity=activity,
            performance_data=performance_data or {},
            group_size=group_size,
            streak_days=streak_days,
            active_events=active_events or []
        )
        
        # Apply education multiplier cap
        total_multiplier = min(
            self._apply_multiplier_cap(multipliers),
            self.MAX_EDUCATION_MULTIPLIER
        )
        
        # Calculate final XP
        final_xp = int(base_xp * total_multiplier)
        
        # No penalties for education activities (we want to encourage learning)
        penalties = {}
        
        # Update tracking
        self._update_education_tracking(activity, user_id, final_xp)
        
        return XPCalculation(
            base_xp=base_xp,
            multipliers=multipliers,
            total_multiplier=total_multiplier,
            final_xp=final_xp,
            penalties=penalties,
            net_xp=final_xp,
            milestone_progress={"activity": activity.value}
        )
    
    def _calculate_education_multipliers(
        self,
        activity: EducationActivity,
        performance_data: Dict[str, any],
        group_size: int,
        streak_days: int,
        active_events: List[str]
    ) -> Dict[str, float]:
        """Calculate all education-specific multipliers"""
        multipliers = {}
        
        # Daily streak multiplier (compound bonus)
        if streak_days > 0:
            streak_config = self.EDUCATION_MULTIPLIERS["daily_streak"]
            streak_mult = min(
                streak_config["base"] + (streak_days * streak_config["increment"]),
                streak_config["max"]
            )
            multipliers["daily_streak"] = streak_mult
        
        # Group activity bonus
        if group_size > 1:
            squad_config = self.EDUCATION_MULTIPLIERS["squad_bonus"]
            if group_size <= 4:
                multipliers["squad_bonus"] = squad_config["small"]
            elif group_size <= 9:
                multipliers["squad_bonus"] = squad_config["medium"]
            else:
                multipliers["squad_bonus"] = squad_config["large"]
        
        # Mentor/teaching bonuses
        if activity in [EducationActivity.TEACH_OTHERS, EducationActivity.ANSWER_QUESTION]:
            multipliers["mentor_bonus"] = self.EDUCATION_MULTIPLIERS["mentor_bonus"]["helping_others"]
            if performance_data.get("verified_helpful", False):
                multipliers["mentor_bonus"] = self.EDUCATION_MULTIPLIERS["mentor_bonus"]["verified_answer"]
        elif activity == EducationActivity.MENTOR_SESSION and performance_data.get("is_student", False):
            multipliers["mentor_bonus"] = self.EDUCATION_MULTIPLIERS["mentor_bonus"]["receiving_help"]
        
        # Perfect score bonuses
        score = performance_data.get("score", 0)
        if score >= 100:
            if activity == EducationActivity.COMPLETE_QUIZ:
                multipliers["perfect_score"] = self.EDUCATION_MULTIPLIERS["perfect_score"]["quiz"]
            elif activity == EducationActivity.COMPLETE_MODULE:
                multipliers["perfect_score"] = self.EDUCATION_MULTIPLIERS["perfect_score"]["module"]
        
        # Difficulty tier bonus
        difficulty = performance_data.get("difficulty", "beginner")
        if difficulty in self.EDUCATION_MULTIPLIERS["difficulty_bonus"]:
            multipliers["difficulty_bonus"] = self.EDUCATION_MULTIPLIERS["difficulty_bonus"][difficulty]
        
        # Special event multipliers
        for event in active_events:
            if event in self.EDUCATION_MULTIPLIERS["event_multiplier"]:
                multipliers["event_multiplier"] = max(
                    multipliers.get("event_multiplier", 1.0),
                    self.EDUCATION_MULTIPLIERS["event_multiplier"][event]
                )
        
        return multipliers
    
    def _check_education_cooldown(self, activity: EducationActivity, user_id: str) -> bool:
        """Check if activity is on cooldown for user"""
        key = f"{user_id}_{activity.value}"
        if key not in self.education_activity_tracker:
            return True
        
        last_activity = self.education_activity_tracker[key]
        cooldown_hours = self.EDUCATION_XP_TABLE[activity]["cooldown_hours"]
        
        if cooldown_hours == 0:
            return True
        
        time_since = datetime.now() - last_activity
        return time_since >= timedelta(hours=cooldown_hours)
    
    def _check_daily_cap(self, activity: EducationActivity, user_id: str, cap: int) -> bool:
        """Check if daily XP cap is reached for activity"""
        today = datetime.now().date()
        key = f"{user_id}_{activity.value}_{today}"
        
        current_xp = self.daily_education_xp.get(key, 0)
        return current_xp < cap
    
    def _update_education_tracking(self, activity: EducationActivity, user_id: str, xp_earned: int):
        """Update activity tracking for cooldowns and caps"""
        # Update last activity time
        key = f"{user_id}_{activity.value}"
        self.education_activity_tracker[key] = datetime.now()
        
        # Update daily XP tracking
        today = datetime.now().date()
        daily_key = f"{user_id}_{activity.value}_{today}"
        self.daily_education_xp[daily_key] = self.daily_education_xp.get(daily_key, 0) + xp_earned
    
    def calculate_achievement_bonus(self, achievement: str, user_achievements: List[str]) -> int:
        """
        Calculate one-time achievement bonus XP
        
        Args:
            achievement: Achievement unlocked
            user_achievements: List of previously earned achievements
            
        Returns:
            Bonus XP amount (0 if already earned)
        """
        if achievement in user_achievements:
            return 0  # Already earned
        
        return self.ACHIEVEMENT_BONUSES.get(achievement, 0)
    
    def get_education_daily_summary(self, user_id: str) -> Dict[str, any]:
        """Get summary of education XP earned today"""
        today = datetime.now().date()
        summary = {
            "date": today,
            "total_education_xp": 0,
            "activities": {},
            "caps_reached": [],
            "available_activities": []
        }
        
        # Calculate totals per activity
        for activity in EducationActivity:
            daily_key = f"{user_id}_{activity.value}_{today}"
            earned = self.daily_education_xp.get(daily_key, 0)
            cap = self.EDUCATION_XP_TABLE[activity]["daily_cap"]
            
            if earned > 0:
                summary["activities"][activity.value] = {
                    "earned": earned,
                    "cap": cap,
                    "remaining": max(0, cap - earned)
                }
                summary["total_education_xp"] += earned
                
                if earned >= cap:
                    summary["caps_reached"].append(activity.value)
            
            # Check if activity is available
            if self._check_education_cooldown(activity, user_id) and earned < cap:
                summary["available_activities"].append(activity.value)
        
        return summary
    
    def reset_daily_education_tracking(self):
        """Reset daily education XP tracking (call at midnight)"""
        yesterday = (datetime.now() - timedelta(days=1)).date()
        keys_to_remove = [k for k in self.daily_education_xp.keys() if str(yesterday) in k]
        for key in keys_to_remove:
            del self.daily_education_xp[key]


# Example usage
if __name__ == "__main__":
    calc = XPCalculator()
    
    # Example trade calculation
    result = calc.calculate_trade_xp(
        trade_result="win",
        exit_type=ExitType.NORMAL,
        multipliers={"win_rate": 1.5, "streak": 1.2},
        current_streak=3,
        performance_metrics={"win_rate": 0.65, "avg_rr": 2.5}
    )
    
    print("=== TRADING XP ===")
    print(f"Trade XP: {result.net_xp}")
    print(f"Multipliers: {result.multipliers}")
    print(f"Total Multiplier: {result.total_multiplier:.2f}x")
    
    # Example education XP calculations
    print("\n=== EDUCATION XP ===")
    
    # Complete a quiz with perfect score
    edu_result = calc.calculate_education_xp(
        activity=EducationActivity.COMPLETE_QUIZ,
        user_id="user123",
        performance_data={"score": 100, "difficulty": "intermediate"},
        streak_days=5,
        active_events=["double_xp_weekend"]
    )
    print(f"\nQuiz XP (perfect score): {edu_result.net_xp}")
    print(f"Base: {edu_result.base_xp}, Multipliers: {edu_result.multipliers}")
    print(f"Total Multiplier: {edu_result.total_multiplier:.2f}x")
    
    # Group learning activity
    group_result = calc.calculate_education_xp(
        activity=EducationActivity.ATTEND_WORKSHOP,
        user_id="user123",
        group_size=8,
        streak_days=10
    )
    print(f"\nWorkshop XP (group of 8): {group_result.net_xp}")
    print(f"Multipliers: {group_result.multipliers}")
    
    # Helping others
    help_result = calc.calculate_education_xp(
        activity=EducationActivity.ANSWER_QUESTION,
        user_id="user123",
        performance_data={"verified_helpful": True},
        streak_days=15
    )
    print(f"\nHelping Others XP: {help_result.net_xp}")
    print(f"Multipliers: {help_result.multipliers}")
    
    # Daily education summary
    print("\n=== DAILY EDUCATION SUMMARY ===")
    summary = calc.get_education_daily_summary("user123")
    print(f"Total Education XP Today: {summary['total_education_xp']}")
    print(f"Activities Completed: {list(summary['activities'].keys())}")
    print(f"Available Activities: {len(summary['available_activities'])}")
    
    # Achievement bonus
    achievement_xp = calc.calculate_achievement_bonus("week_streak", [])
    print(f"\n=== ACHIEVEMENT BONUS ===")
    print(f"Week Streak Achievement: +{achievement_xp} XP")
    
    # Example milestone progress
    progress = calc.calculate_milestone_progress(
        current_xp=25000,
        daily_avg_xp=850,
        current_multipliers={"win_rate": 1.5, "consistency": 1.3}
    )
    
    print(f"\n=== MILESTONE PROGRESS ===")
    print(f"Current Milestone: {progress['current_milestone']}")
    print(f"Elite Progress: {progress['elite_progress']['percentage']:.1f}%")
    print(f"Days to Elite: {progress['elite_progress']['days_remaining']}")