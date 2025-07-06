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
    
    # Multiplier sources and their max values
    MULTIPLIERS = {
        "win_rate": {"max": 2.0, "base": 1.0},  # 1.0-2.0x based on win rate
        "streak": {"max": 2.0, "base": 1.0},     # 1.0-2.0x based on streak
        "volume": {"max": 1.5, "base": 1.0},     # 1.0-1.5x based on volume
        "consistency": {"max": 1.5, "base": 1.0}, # 1.0-1.5x based on consistency
        "risk_reward": {"max": 1.5, "base": 1.0}, # 1.0-1.5x based on R:R
        "special_event": {"max": 2.0, "base": 1.0}, # Special events/challenges
    }
    
    # Maximum total multiplier
    MAX_TOTAL_MULTIPLIER = 10.0
    
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
    
    print(f"Trade XP: {result.net_xp}")
    print(f"Multipliers: {result.multipliers}")
    print(f"Total Multiplier: {result.total_multiplier:.2f}x")
    
    # Example milestone progress
    progress = calc.calculate_milestone_progress(
        current_xp=25000,
        daily_avg_xp=850,
        current_multipliers={"win_rate": 1.5, "consistency": 1.3}
    )
    
    print(f"\nCurrent Milestone: {progress['current_milestone']}")
    print(f"Elite Progress: {progress['elite_progress']['percentage']:.1f}%")
    print(f"Days to Elite: {progress['elite_progress']['days_remaining']}")