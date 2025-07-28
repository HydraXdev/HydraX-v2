"""
BITTEN Perk System Integration
Connects perks with all other BITTEN systems
"""

import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime

from .perk_system import PerkSystem, PerkBranch
from .user_profile import UserProfileManager
from .reward_system import RewardSystem
from .xp_economy import XPEconomy
from .trade_manager import TradeManager
from .engagement_system import EngagementSystem
from .achievement_system import AchievementManager
from .squad_radar import SquadRadar
from .signal_alerts import SignalAlertSystem

logger = logging.getLogger(__name__)

class PerkIntegration:
    """Integrates perk effects across all BITTEN systems"""
    
    def __init__(self, perk_system: PerkSystem):
        self.perk_system = perk_system
        
        # System references (to be injected)
        self.profile_manager: Optional[UserProfileManager] = None
        self.reward_system: Optional[RewardSystem] = None
        self.xp_economy: Optional[XPEconomy] = None
        self.trade_manager: Optional[TradeManager] = None
        self.engagement_system: Optional[EngagementSystem] = None
        self.achievement_manager: Optional[AchievementManager] = None
        self.squad_radar: Optional[SquadRadar] = None
        self.signal_alerts: Optional[SignalAlertSystem] = None
    
    def inject_systems(self, **systems):
        """Inject system dependencies"""
        for name, system in systems.items():
            setattr(self, name, system)
    
    # TRADING BRANCH INTEGRATIONS
    
    def apply_trading_fee_reduction(self, user_id: int, base_fee: float) -> Tuple[float, List[str]]:
        """Apply fee reduction perks"""
        return self.perk_system.apply_perk_effects(
            user_id, "trading_fee", base_fee
        )
    
    def apply_spread_improvement(self, user_id: int, base_spread: float) -> Tuple[float, List[str]]:
        """Apply spread improvement perks"""
        return self.perk_system.apply_perk_effects(
            user_id, "spread", base_spread
        )
    
    def check_ghost_protocol(self, user_id: int) -> bool:
        """Check if user has ghost protocol active"""
        effects = self.perk_system.get_active_effects(user_id)
        return "trade_privacy" in effects
    
    def check_double_tap(self, user_id: int, signal_id: str, 
                        last_execution_time: datetime) -> Tuple[bool, str]:
        """Check if user can reuse signal with double tap"""
        effects = self.perk_system.get_active_effects(user_id)
        
        if "signal_reuse" not in effects:
            return False, "Double Tap perk not active"
        
        # Check 30 minute cooldown
        time_diff = (datetime.now() - last_execution_time).total_seconds()
        if time_diff < 1800:  # 30 minutes
            remaining = 1800 - time_diff
            return False, f"Double Tap on cooldown: {int(remaining/60)} minutes"
        
        return True, "Double Tap available"
    
    def apply_risk_shield(self, user_id: int, loss_amount: float, 
                         is_first_daily_loss: bool) -> Tuple[float, List[str]]:
        """Apply risk shield to first daily loss"""
        if not is_first_daily_loss:
            return loss_amount, []
        
        effects = self.perk_system.get_active_effects(user_id)
        if "loss_reduction" in effects:
            for effect in effects["loss_reduction"]:
                reduced_loss = loss_amount * (1 - effect.value)
                return reduced_loss, [effect.description]
        
        return loss_amount, []
    
    def get_execution_speed_multiplier(self, user_id: int) -> float:
        """Get execution speed multiplier from perks"""
        effects = self.perk_system.get_active_effects(user_id)
        
        if "execution_speed" in effects:
            return effects["execution_speed"][0].value
        
        return 1.0
    
    def check_market_oracle(self, user_id: int, signal_time: datetime) -> Optional[float]:
        """Check if user can see early win probability"""
        effects = self.perk_system.get_active_effects(user_id)
        
        if "early_insight" not in effects:
            return None
        
        # Check if within 1 hour window
        time_until = (signal_time - datetime.now()).total_seconds()
        if 0 < time_until <= 3600:  # Within 1 hour
            # Return simulated win probability (would be calculated by ML model)
            return 0.72  # Example: 72% win probability
        
        return None
    
    # ANALYSIS BRANCH INTEGRATIONS
    
    def get_signal_priority_delay(self, user_id: int) -> int:
        """Get signal priority delay in seconds"""
        effects = self.perk_system.get_active_effects(user_id)
        
        if "signal_priority" in effects:
            return -int(effects["signal_priority"][0].value)  # Negative for early
        
        return 0
    
    def get_extra_indicators(self, user_id: int) -> List[str]:
        """Get list of extra indicators user can see"""
        effects = self.perk_system.get_active_effects(user_id)
        
        extra_indicators = []
        if "extra_indicators" in effects:
            count = int(effects["extra_indicators"][0].value)
            # Return specific indicators based on count
            all_extras = ["RSI_DIVERGENCE", "VOLUME_PROFILE", "MARKET_STRUCTURE", 
                         "SUPPLY_DEMAND", "ORDER_FLOW", "SENTIMENT"]
            extra_indicators = all_extras[:count]
        
        return extra_indicators
    
    def check_pattern_recognition(self, user_id: int, current_setup: Dict) -> List[Dict]:
        """Get similar historical patterns if perk active"""
        effects = self.perk_system.get_active_effects(user_id)
        
        if "pattern_analysis" not in effects:
            return []
        
        # Would query historical database for similar setups
        # This is a simplified example
        similar_patterns = [
            {
                "date": "2024-01-15",
                "similarity": 0.89,
                "outcome": "WIN",
                "profit_pips": 45
            },
            {
                "date": "2024-02-03", 
                "similarity": 0.85,
                "outcome": "WIN",
                "profit_pips": 38
            }
        ]
        
        return similar_patterns
    
    def check_volatility_alerts(self, user_id: int) -> bool:
        """Check if user has volatility radar active"""
        effects = self.perk_system.get_active_effects(user_id)
        return "volatility_alerts" in effects
    
    def get_confluence_score(self, user_id: int, signal_data: Dict) -> Optional[Dict]:
        """Get multi-timeframe confluence score if quantum analysis active"""
        effects = self.perk_system.get_active_effects(user_id)
        
        if "confluence_score" not in effects:
            return None
        
        # Calculate confluence across timeframes
        return {
            "overall_score": 0.82,
            "timeframes": {
                "M5": 0.75,
                "M15": 0.88,
                "H1": 0.90,
                "H4": 0.78
            },
            "strength": "STRONG"
        }
    
    def get_prophet_predictions(self, user_id: int) -> List[Dict]:
        """Get next signal predictions if prophet mode active"""
        effects = self.perk_system.get_active_effects(user_id)
        
        if "signal_prediction" not in effects:
            return []
        
        # Return predicted signals (would use ML model)
        predictions = [
            {
                "pair": "EURUSD",
                "direction": "BUY",
                "confidence": 0.72,
                "estimated_time": "2 hours"
            },
            {
                "pair": "GBPJPY",
                "direction": "SELL", 
                "confidence": 0.68,
                "estimated_time": "4 hours"
            },
            {
                "pair": "GOLD",
                "direction": "BUY",
                "confidence": 0.71,
                "estimated_time": "6 hours"
            }
        ]
        
        return predictions[:int(effects["signal_prediction"][0].value)]
    
    # SOCIAL BRANCH INTEGRATIONS
    
    def apply_squad_xp_bonus(self, user_id: int, base_xp: int, 
                            is_squad_win: bool) -> Tuple[int, List[str]]:
        """Apply squad synergy XP bonus"""
        if not is_squad_win:
            return base_xp, []
        
        effects = self.perk_system.get_active_effects(user_id)
        if "squad_xp_bonus" in effects:
            bonus_xp = int(base_xp * effects["squad_xp_bonus"][0].value)
            total_xp = base_xp + bonus_xp
            return total_xp, [f"+{bonus_xp} XP from Squad Synergy"]
        
        return base_xp, []
    
    def apply_recruit_xp_bonus(self, user_id: int, base_xp: int) -> Tuple[int, List[str]]:
        """Apply mentor bonus to recruit XP"""
        effects = self.perk_system.get_active_effects(user_id)
        
        if "recruit_xp_bonus" in effects:
            bonus_xp = int(base_xp * effects["recruit_xp_bonus"][0].value)
            total_xp = base_xp + bonus_xp
            return total_xp, [f"+{bonus_xp} XP from Mentor bonus"]
        
        return base_xp, []
    
    def check_rally_cry_available(self, user_id: int, 
                                 last_use: Optional[datetime]) -> Tuple[bool, str]:
        """Check if rally cry boost is available"""
        effects = self.perk_system.get_active_effects(user_id)
        
        if "squad_boost" not in effects:
            return False, "Rally Cry perk not active"
        
        # Check daily cooldown
        if last_use:
            time_diff = (datetime.now() - last_use).total_seconds()
            if time_diff < 86400:  # 24 hours
                remaining = 86400 - time_diff
                return False, f"Rally Cry on cooldown: {int(remaining/3600)} hours"
        
        return True, "Rally Cry available"
    
    def apply_rally_cry_boost(self, squad_members: List[int], 
                             boost_value: float = 0.10) -> Dict[int, float]:
        """Apply rally cry boost to squad members"""
        boosted_members = {}
        
        for member_id in squad_members:
            # Each member gets the boost for their next trade
            boosted_members[member_id] = boost_value
        
        return boosted_members
    
    def check_instant_share(self, user_id: int) -> bool:
        """Check if user has instant trade sharing"""
        effects = self.perk_system.get_active_effects(user_id)
        return "instant_share" in effects
    
    def apply_squad_leader_rewards(self, user_id: int, win_bonus: float) -> Dict[int, float]:
        """Distribute squad leader win bonus"""
        effects = self.perk_system.get_active_effects(user_id)
        
        if "squad_reward_share" not in effects:
            return {}
        
        share_rate = effects["squad_reward_share"][0].value
        
        # Get squad members
        if self.squad_radar:
            squad_members = self.squad_radar.get_squad_members(user_id)
            shared_amount = win_bonus * share_rate / len(squad_members)
            
            return {member: shared_amount for member in squad_members}
        
        return {}
    
    def get_recruit_starting_bonus(self, recruiter_id: int) -> Dict[str, Any]:
        """Get starting bonus for recruits if legacy builder active"""
        effects = self.perk_system.get_active_effects(recruiter_id)
        
        if "recruit_boost" not in effects:
            return {"level": 1, "bonus_gear": []}
        
        boost_level = int(effects["recruit_boost"][0].value)
        
        return {
            "level": boost_level,
            "bonus_gear": [
                "starter_pack_premium",
                "early_access_signals",
                "mentor_direct_line"
            ],
            "bonus_xp": 500,
            "bonus_ammo": 10
        }
    
    # ECONOMY BRANCH INTEGRATIONS
    
    def apply_xp_multipliers(self, user_id: int, base_xp: int, 
                           context: str = "general") -> Tuple[int, List[str]]:
        """Apply all XP multiplier perks"""
        final_xp, effects_applied = self.perk_system.apply_perk_effects(
            user_id, "xp_gain", float(base_xp)
        )
        
        return int(final_xp), effects_applied
    
    def apply_reward_multipliers(self, user_id: int, 
                               base_reward: float) -> Tuple[float, List[str]]:
        """Apply reward multiplier perks"""
        return self.perk_system.apply_perk_effects(
            user_id, "reward", base_reward
        )
    
    def apply_streak_acceleration(self, user_id: int, 
                                 base_streak_progress: int) -> Tuple[int, List[str]]:
        """Apply compound interest to streak progression"""
        effects = self.perk_system.get_active_effects(user_id)
        
        if "streak_multiplier" in effects:
            multiplier = effects["streak_multiplier"][0].value
            accelerated = int(base_streak_progress * multiplier)
            return accelerated, [f"Streak progress x{multiplier}"]
        
        return base_streak_progress, []
    
    def calculate_daily_interest(self, user_id: int, 
                               yesterday_xp: int) -> Tuple[int, List[str]]:
        """Calculate daily compound XP interest"""
        effects = self.perk_system.get_active_effects(user_id)
        
        if "xp_interest" not in effects:
            return 0, []
        
        interest_rate = effects["xp_interest"][0].value
        interest_xp = int(yesterday_xp * interest_rate)
        
        return interest_xp, [f"+{interest_xp} XP daily interest"]
    
    def calculate_prestige_retention(self, user_id: int, 
                                   current_xp: int) -> Tuple[int, List[str]]:
        """Calculate XP retained on prestige"""
        effects = self.perk_system.get_active_effects(user_id)
        
        if "prestige_retention" not in effects:
            return 0, []
        
        retention_rate = effects["prestige_retention"][0].value
        retained_xp = int(current_xp * retention_rate)
        
        return retained_xp, [f"Kept {int(retention_rate * 100)}% XP on prestige"]
    
    def calculate_passive_income(self, user_id: int, 
                               hours_elapsed: float) -> Tuple[int, List[str]]:
        """Calculate passive XP income"""
        effects = self.perk_system.get_active_effects(user_id)
        
        if "passive_xp" not in effects:
            return 0, []
        
        hourly_rate = effects["passive_xp"][0].value
        earned_xp = int(hourly_rate * hours_elapsed)
        
        return earned_xp, [f"+{earned_xp} XP passive income"]
    
    # SEASONAL PERK INTEGRATIONS
    
    def check_seasonal_bonuses(self, user_id: int, 
                             current_date: datetime) -> List[Dict]:
        """Check active seasonal bonuses"""
        effects = self.perk_system.get_active_effects(user_id)
        seasonal_bonuses = []
        
        # Winter Warrior
        if "seasonal_xp" in effects:
            if current_date.month in [12, 1, 2]:  # Winter months
                seasonal_bonuses.append({
                    "name": "Winter Warrior",
                    "bonus": "+50% XP",
                    "active": True
                })
        
        # Halloween Hunter
        if current_date.month == 10 and current_date.day == 31:
            effects = self.perk_system.get_active_effects(user_id)
            if "spooky_bonus" in effects:
                seasonal_bonuses.append({
                    "name": "Halloween Hunter",
                    "bonus": "2x rewards",
                    "active": True
                })
        
        return seasonal_bonuses
    
    # SYNERGY CALCULATIONS
    
    def calculate_total_bonuses(self, user_id: int) -> Dict[str, float]:
        """Calculate all active bonuses from perks"""
        effects = self.perk_system.get_active_effects(user_id)
        
        total_bonuses = {
            "xp_multiplier": 1.0,
            "reward_multiplier": 1.0,
            "fee_reduction": 0.0,
            "spread_improvement": 0.0,
            "execution_speed": 1.0,
            "synergy_bonus": 0.0
        }
        
        # Aggregate all effects
        for effect_type, effect_list in effects.items():
            if effect_type == "xp_multiplier":
                for effect in effect_list:
                    total_bonuses["xp_multiplier"] *= (1 + effect.value)
            elif effect_type == "reward_multiplier":
                for effect in effect_list:
                    total_bonuses["reward_multiplier"] *= (1 + effect.value)
            elif effect_type == "fee_reduction":
                for effect in effect_list:
                    total_bonuses["fee_reduction"] += effect.value
            elif effect_type == "spread_improvement":
                for effect in effect_list:
                    total_bonuses["spread_improvement"] += effect.value
            elif effect_type == "execution_speed":
                total_bonuses["execution_speed"] = effect_list[0].value
            elif effect_type == "synergy_bonus":
                total_bonuses["synergy_bonus"] = effect_list[0].value
        
        return total_bonuses
    
    # ACHIEVEMENT INTEGRATION
    
    def check_perk_achievements(self, user_id: int) -> List[str]:
        """Check for perk-related achievements"""
        player_data = self.perk_system.get_player_data(user_id)
        achievements = []
        
        # Check various milestones
        if len(player_data.unlocked_perks) >= 10:
            achievements.append("perk_collector_bronze")
        if len(player_data.unlocked_perks) >= 25:
            achievements.append("perk_collector_silver")
        if len(player_data.unlocked_perks) >= 50:
            achievements.append("perk_collector_gold")
        
        # Check for full branch unlock
        branch_counts = {}
        for perk_id in player_data.unlocked_perks:
            perk = self.perk_system.perk_catalog.get(perk_id)
            if perk:
                branch = perk.branch.value
                branch_counts[branch] = branch_counts.get(branch, 0) + 1
        
        for branch, count in branch_counts.items():
            if count >= 10:  # Assuming ~10 perks per branch
                achievements.append(f"{branch.lower()}_master")
        
        # Check for legendary perks
        legendary_count = 0
        for perk_id in player_data.unlocked_perks:
            perk = self.perk_system.perk_catalog.get(perk_id)
            if perk and perk.tier.value == 4:
                legendary_count += 1
        
        if legendary_count >= 1:
            achievements.append("legendary_holder")
        if legendary_count >= 4:
            achievements.append("legendary_master")
        
        return achievements
    
    # NOTIFICATION HELPERS
    
    def get_perk_notifications(self, user_id: int) -> List[Dict]:
        """Get perk-related notifications"""
        player_data = self.perk_system.get_player_data(user_id)
        notifications = []
        
        # Check for available points
        if player_data.available_points > 0:
            notifications.append({
                "type": "perk_points",
                "message": f"You have {player_data.available_points} unspent perk points!",
                "priority": "medium"
            })
        
        # Check for newly unlockable perks
        for perk_id, perk in self.perk_system.perk_catalog.items():
            if perk_id in player_data.unlocked_perks:
                continue
            
            can_unlock, _ = self.perk_system.unlock_perk(
                user_id, perk_id, 0, []
            )
            if can_unlock:
                notifications.append({
                    "type": "perk_available",
                    "message": f"{perk.name} is now available to unlock!",
                    "priority": "low",
                    "perk_id": perk_id
                })
        
        # Check for expiring seasonal perks
        for perk_id in player_data.seasonal_perks:
            perk = self.perk_system.perk_catalog.get(perk_id)
            if perk and perk.seasonal_end:
                days_left = (perk.seasonal_end - datetime.now()).days
                if days_left <= 7:
                    notifications.append({
                        "type": "seasonal_expiring",
                        "message": f"{perk.name} expires in {days_left} days!",
                        "priority": "high",
                        "perk_id": perk_id
                    })
        
        return notifications