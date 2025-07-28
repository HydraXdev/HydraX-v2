"""
Gear System Integration
Connects gear drops with achievements, milestones, and trading events
"""

import logging
import random
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta

from .gear_system import (
    GearSystem, GearItem, GearRarity, GearType,
    award_gear_for_achievement, award_gear_for_milestone
)
from .achievement_system import AchievementSystem, AchievementTier
from .reward_system import RewardSystem

logger = logging.getLogger(__name__)

class GearDropManager:
    """Manages gear drops from various game events"""
    
    # Drop chances for different events
    DROP_CHANCES = {
        'trade_win': 0.15,  # 15% chance on profitable trade
        'daily_login': 0.25,  # 25% chance on daily login
        'streak_milestone': 1.0,  # Guaranteed on streak milestones
        'level_up': 0.8,  # 80% chance on level up
        'perfect_trade': 1.0,  # Guaranteed on perfect trades
        'achievement_unlock': 1.0,  # Guaranteed on achievements
        'challenge_complete': 0.5,  # 50% on challenge completion
    }
    
    # Luck modifiers based on performance
    PERFORMANCE_LUCK = {
        'win_rate_high': 1.2,  # >70% win rate
        'profit_streak': 1.3,  # 5+ profitable trades in a row
        'vip_member': 1.5,  # VIP members get better drops
        'weekend_warrior': 1.1,  # Weekend bonus
        'happy_hour': 2.0,  # Special event multiplier
    }
    
    def __init__(self, gear_system: GearSystem):
        self.gear_system = gear_system
        self.drop_cooldowns = {}  # Prevent drop spam
        
    def check_drop_eligibility(
        self, 
        user_id: int, 
        event_type: str
    ) -> Tuple[bool, float]:
        """Check if user is eligible for a drop"""
        # Check cooldown
        cooldown_key = f"{user_id}_{event_type}"
        last_drop = self.drop_cooldowns.get(cooldown_key, 0)
        
        cooldown_times = {
            'trade_win': 300,  # 5 minutes
            'daily_login': 86400,  # 24 hours
            'level_up': 0,  # No cooldown
            'achievement_unlock': 0,  # No cooldown
        }
        
        cooldown = cooldown_times.get(event_type, 600)  # Default 10 min
        
        if datetime.now().timestamp() - last_drop < cooldown:
            return False, 0.0
        
        # Get base drop chance
        base_chance = self.DROP_CHANCES.get(event_type, 0.1)
        
        return True, base_chance
    
    def calculate_luck_multiplier(
        self, 
        user_id: int, 
        user_stats: Dict[str, Any]
    ) -> float:
        """Calculate luck multiplier based on user performance"""
        multiplier = 1.0
        
        # Win rate bonus
        if user_stats.get('win_rate', 0) > 0.7:
            multiplier *= self.PERFORMANCE_LUCK['win_rate_high']
        
        # Profit streak bonus
        if user_stats.get('profit_streak', 0) >= 5:
            multiplier *= self.PERFORMANCE_LUCK['profit_streak']
        
        # Weekend bonus
        if datetime.now().weekday() >= 5:  # Saturday or Sunday
            multiplier *= self.PERFORMANCE_LUCK['weekend_warrior']
        
        # VIP bonus (would check actual VIP status)
        if user_stats.get('is_vip', False):
            multiplier *= self.PERFORMANCE_LUCK['vip_member']
        
        return multiplier
    
    def process_trade_completion(
        self,
        user_id: int,
        trade_result: Dict[str, Any]
    ) -> Optional[GearItem]:
        """Process gear drops for trade completion"""
        # Only drop on profitable trades
        if trade_result.get('profit', 0) <= 0:
            return None
        
        eligible, base_chance = self.check_drop_eligibility(user_id, 'trade_win')
        if not eligible:
            return None
        
        # Get user stats for luck calculation
        user_stats = {
            'win_rate': trade_result.get('win_rate', 0.5),
            'profit_streak': trade_result.get('consecutive_wins', 0)}
        
        luck = self.calculate_luck_multiplier(user_id, user_stats)
        
        # Perfect trade bonus
        if trade_result.get('roi', 0) > 0.5:  # 50%+ ROI
            base_chance = self.DROP_CHANCES['perfect_trade']
        
        # Roll for drop
        if random.random() > base_chance:
            return None
        
        # Generate drop with performance-based rarity boost
        user_level = trade_result.get('user_level', 1)
        
        # Higher profit = better drops
        profit_tier = None
        if trade_result['profit'] > 10000:
            profit_tier = GearRarity.LEGENDARY
        elif trade_result['profit'] > 5000:
            profit_tier = GearRarity.EPIC
        elif trade_result['profit'] > 1000:
            profit_tier = GearRarity.RARE
        
        item = self.gear_system.generate_random_drop(
            user_level=user_level,
            luck_multiplier=luck,
            guaranteed_rarity=profit_tier
        )
        
        # Add trade-specific bonuses
        if item.gear_type == GearType.STRATEGY:
            item.stats.damage_bonus += 0.05  # Trading strategies get damage bonus
        elif item.gear_type == GearType.INDICATOR:
            item.stats.accuracy_bonus += 0.05  # Indicators get accuracy bonus
        
        # Add to inventory
        self.gear_system.add_item_to_inventory(
            user_id, 
            item, 
            source=f"trade_profit_{trade_result['profit']:.0f}"
        )
        
        # Update cooldown
        self.drop_cooldowns[f"{user_id}_trade_win"] = datetime.now().timestamp()
        
        logger.info(f"Gear drop for user {user_id}: {item.name} ({item.rarity.name})")
        
        return item
    
    def process_achievement_unlock(
        self,
        user_id: int,
        achievement_id: str,
        achievement_tier: AchievementTier
    ) -> Optional[GearItem]:
        """Process gear drops for achievement unlocks"""
        # Map achievement categories to gear types
        achievement_gear_map = {
            'first_blood': GearType.STRATEGY,
            'marksman': GearType.INDICATOR,
            'elite_sniper': GearType.INDICATOR,
            'mogul': GearType.BOOST,
            'speed_demon': GearType.CONSUMABLE,
            'professor': GearType.INDICATOR}
        
        # Determine gear type based on achievement
        preferred_type = achievement_gear_map.get(achievement_id)
        
        # Award gear
        item = award_gear_for_achievement(
            self.gear_system,
            user_id,
            achievement_id,
            achievement_tier.value
        )
        
        if item and preferred_type:
            # Try to match the gear type to achievement theme
            if random.random() < 0.7:  # 70% chance to match theme
                themed_item = self._create_themed_item(
                    achievement_id,
                    achievement_tier,
                    preferred_type
                )
                if themed_item:
                    self.gear_system.add_item_to_inventory(
                        user_id,
                        themed_item,
                        source=f"achievement_{achievement_id}"
                    )
                    return themed_item
        
        return item
    
    def process_daily_login(
        self,
        user_id: int,
        consecutive_days: int
    ) -> Optional[GearItem]:
        """Process gear drops for daily logins"""
        eligible, base_chance = self.check_drop_eligibility(user_id, 'daily_login')
        if not eligible:
            return None
        
        # Increase chance with consecutive days
        chance = base_chance + (consecutive_days * 0.05)
        chance = min(chance, 0.8)  # Cap at 80%
        
        if random.random() > chance:
            return None
        
        # Better items for longer streaks
        guaranteed_rarity = None
        if consecutive_days >= 30:
            guaranteed_rarity = GearRarity.EPIC
        elif consecutive_days >= 14:
            guaranteed_rarity = GearRarity.RARE
        elif consecutive_days >= 7:
            guaranteed_rarity = GearRarity.UNCOMMON
        
        item = self.gear_system.generate_random_drop(
            user_level=1,  # Would get actual level
            luck_multiplier=1.0 + (consecutive_days * 0.1),
            guaranteed_rarity=guaranteed_rarity
        )
        
        # Daily login items often have XP bonuses
        if random.random() < 0.3:
            item.stats.xp_multiplier *= 1.1
        
        self.gear_system.add_item_to_inventory(
            user_id,
            item,
            source=f"daily_login_day_{consecutive_days}"
        )
        
        self.drop_cooldowns[f"{user_id}_daily_login"] = datetime.now().timestamp()
        
        return item
    
    def process_level_up(
        self,
        user_id: int,
        new_level: int,
        level_data: Dict[str, Any]
    ) -> Optional[GearItem]:
        """Process gear drops for level ups"""
        eligible, base_chance = self.check_drop_eligibility(user_id, 'level_up')
        if not eligible:
            return None
        
        if random.random() > base_chance:
            return None
        
        # Milestone levels guarantee better gear
        guaranteed_rarity = None
        if new_level % 50 == 0:  # Every 50 levels
            guaranteed_rarity = GearRarity.LEGENDARY
        elif new_level % 25 == 0:  # Every 25 levels
            guaranteed_rarity = GearRarity.EPIC
        elif new_level % 10 == 0:  # Every 10 levels
            guaranteed_rarity = GearRarity.RARE
        
        item = self.gear_system.generate_random_drop(
            user_level=new_level,
            luck_multiplier=1.5,  # Level ups are lucky
            guaranteed_rarity=guaranteed_rarity
        )
        
        # Level-appropriate stats
        level_bonus = new_level * 0.001
        item.stats.accuracy_bonus += level_bonus
        item.stats.damage_bonus += level_bonus
        
        self.gear_system.add_item_to_inventory(
            user_id,
            item,
            source=f"level_up_{new_level}"
        )
        
        return item
    
    def process_challenge_completion(
        self,
        user_id: int,
        challenge_id: str,
        challenge_data: Dict[str, Any]
    ) -> Optional[GearItem]:
        """Process gear drops for challenge completions"""
        eligible, base_chance = self.check_drop_eligibility(user_id, 'challenge_complete')
        if not eligible:
            return None
        
        # Harder challenges have better drop rates
        difficulty_multiplier = {
            'easy': 0.5,
            'medium': 1.0,
            'hard': 1.5,
            'extreme': 2.0
        }
        
        difficulty = challenge_data.get('difficulty', 'medium')
        chance = base_chance * difficulty_multiplier.get(difficulty, 1.0)
        
        if random.random() > chance:
            return None
        
        # Generate challenge-themed item
        item = self.gear_system.generate_random_drop(
            user_level=challenge_data.get('user_level', 1),
            luck_multiplier=difficulty_multiplier.get(difficulty, 1.0)
        )
        
        # Add challenge completion bonus
        if challenge_data.get('perfect_completion', False):
            item.stats.xp_multiplier *= 1.2
            item.stats.reward_multiplier *= 1.1
        
        self.gear_system.add_item_to_inventory(
            user_id,
            item,
            source=f"challenge_{challenge_id}"
        )
        
        return item
    
    def _create_themed_item(
        self,
        theme: str,
        tier: AchievementTier,
        gear_type: GearType
    ) -> Optional[GearItem]:
        """Create a themed item for specific achievements"""
        # Theme-specific items
        themed_items = {
            'first_blood': {
                'name': "Rookie's Lucky Charm",
                'description': "Your first victory, preserved in gear form",
                'stats': GearStats(accuracy_bonus=0.1, xp_multiplier=1.2)
            },
            'marksman': {
                'name': "Precision Scope",
                'description': "For those who never miss their target",
                'stats': GearStats(accuracy_bonus=0.25, critical_chance=0.1)
            },
            'elite_sniper': {
                'name': "Elite Marksman Badge",
                'description': "Proof of exceptional trading accuracy",
                'stats': GearStats(accuracy_bonus=0.4, damage_bonus=0.2)
            },
            'mogul': {
                'name': "Golden Calculator",
                'description': "Counts profits faster than light",
                'stats': GearStats(reward_multiplier=1.5, damage_bonus=0.3)
            }
        }
        
        theme_data = themed_items.get(theme)
        if not theme_data:
            return None
        
        # Map achievement tier to gear rarity
        tier_to_rarity = {
            AchievementTier.BRONZE: GearRarity.UNCOMMON,
            AchievementTier.SILVER: GearRarity.RARE,
            AchievementTier.GOLD: GearRarity.EPIC,
            AchievementTier.PLATINUM: GearRarity.LEGENDARY,
            AchievementTier.DIAMOND: GearRarity.LEGENDARY,
            AchievementTier.MASTER: GearRarity.MYTHIC
        }
        
        rarity = tier_to_rarity.get(tier, GearRarity.RARE)
        
        import hashlib
        item_id = f"themed_{theme}_{hashlib.md5(theme.encode()).hexdigest()[:8]}"
        
        return GearItem(
            item_id=item_id,
            name=theme_data['name'],
            gear_type=gear_type,
            rarity=rarity,
            level=1,
            stats=theme_data['stats'],
            description=theme_data['description'],
            icon="🏆",
            special_effects=[f"Achievement Reward: {theme}"],
            tradeable=False  # Achievement items are soulbound
        )

class GearEventScheduler:
    """Schedules special gear drop events"""
    
    def __init__(self, gear_system: GearSystem, drop_manager: GearDropManager):
        self.gear_system = gear_system
        self.drop_manager = drop_manager
        self.active_events = {}
        
    def start_happy_hour(self, duration_minutes: int = 60):
        """Start a happy hour event with increased drop rates"""
        event_id = "happy_hour"
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        
        self.active_events[event_id] = {
            'type': 'happy_hour',
            'multiplier': 2.0,
            'end_time': end_time,
            'description': "2x drop rates for all activities!"
        }
        
        logger.info(f"Started happy hour event for {duration_minutes} minutes")
        
    def start_themed_event(
        self,
        theme: str,
        duration_hours: int,
        bonus_gear_type: GearType
    ):
        """Start a themed event with specific gear drops"""
        event_id = f"themed_{theme}"
        end_time = datetime.now() + timedelta(hours=duration_hours)
        
        self.active_events[event_id] = {
            'type': 'themed',
            'theme': theme,
            'bonus_type': bonus_gear_type,
            'end_time': end_time,
            'description': f"{theme.title()} event - Increased {bonus_gear_type.value} drops!"
        }
        
    def get_active_events(self) -> List[Dict[str, Any]]:
        """Get list of currently active events"""
        current_time = datetime.now()
        active = []
        
        # Clean up expired events
        expired = []
        for event_id, event_data in self.active_events.items():
            if current_time > event_data['end_time']:
                expired.append(event_id)
            else:
                active.append({
                    'id': event_id,
                    **event_data,
                    'time_remaining': (event_data['end_time'] - current_time).seconds
                })
        
        for event_id in expired:
            del self.active_events[event_id]
        
        return active
    
    def apply_event_modifiers(
        self,
        base_chance: float,
        gear_type: Optional[GearType] = None
    ) -> float:
        """Apply active event modifiers to drop chances"""
        modified_chance = base_chance
        
        for event_data in self.active_events.values():
            if event_data['type'] == 'happy_hour':
                modified_chance *= event_data['multiplier']
            
            elif event_data['type'] == 'themed' and gear_type:
                if gear_type == event_data['bonus_type']:
                    modified_chance *= 1.5
        
        return min(modified_chance, 1.0)  # Cap at 100%

class GearRewardIntegration:
    """Integrates gear drops with the reward system"""
    
    def __init__(
        self,
        gear_system: GearSystem,
        reward_system: RewardSystem,
        drop_manager: GearDropManager
    ):
        self.gear_system = gear_system
        self.reward_system = reward_system
        self.drop_manager = drop_manager
        
    def process_trade_rewards(
        self,
        user_id: int,
        trade_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process both XP rewards and gear drops for trades"""
        results = {
            'xp_earned': 0,
            'rewards_earned': 0,
            'gear_dropped': None,
            'bonuses_applied': []
        }
        
        # Calculate XP and rewards
        profit = trade_data.get('profit', 0)
        if profit > 0:
            # Get reward calculation
            reward_calc = self.reward_system.calculate_reward(
                user_id,
                profit,
                trade_data.get('risk_tier', 'STANDARD')
            )
            
            results['rewards_earned'] = reward_calc.total_amount
            results['bonuses_applied'] = list(reward_calc.breakdown.keys())
            
            # Update reward system records
            self.reward_system.record_period_activity(
                user_id,
                trades=1,
                profit=profit,
                xp=trade_data.get('xp_earned', 0),
                rewards=reward_calc.total_amount
            )
        
        # Check for gear drops
        gear_drop = self.drop_manager.process_trade_completion(
            user_id,
            trade_data
        )
        
        if gear_drop:
            results['gear_dropped'] = {
                'item_id': gear_drop.item_id,
                'name': gear_drop.name,
                'rarity': gear_drop.rarity.name,
                'power': gear_drop.get_power_score()
            }
        
        return results
    
    def get_gear_enhanced_stats(
        self,
        user_id: int
    ) -> Dict[str, float]:
        """Get user's stats enhanced by equipped gear"""
        base_stats = {
            'accuracy': 0.5,  # Base 50% accuracy
            'damage': 1.0,  # Base damage multiplier
            'fire_rate': 1.0,  # Base fire rate
            'xp_rate': 1.0,  # Base XP rate
            'reward_rate': 1.0,  # Base reward rate
        }
        
        # Get active loadout
        active_loadout = self.gear_system.get_active_loadout(user_id)
        if not active_loadout:
            return base_stats
        
        # Get gear stats
        inventory = self.gear_system.get_user_inventory(user_id)
        gear_stats = active_loadout.get_total_stats(inventory)
        
        # Apply gear bonuses
        enhanced_stats = {
            'accuracy': base_stats['accuracy'] + gear_stats.accuracy_bonus,
            'damage': base_stats['damage'] * (1 + gear_stats.damage_bonus),
            'fire_rate': base_stats['fire_rate'] * (1 + gear_stats.fire_rate_bonus),
            'xp_rate': base_stats['xp_rate'] * gear_stats.xp_multiplier,
            'reward_rate': base_stats['reward_rate'] * gear_stats.reward_multiplier,
            'critical_chance': gear_stats.critical_chance,
            'cooldown_reduction': gear_stats.cooldown_reduction
        }
        
        # Apply set bonuses
        set_bonus = self.gear_system.get_gear_set_bonus(user_id, active_loadout)
        if set_bonus:
            enhanced_stats['accuracy'] += set_bonus.accuracy_bonus
            enhanced_stats['damage'] *= (1 + set_bonus.damage_bonus)
            enhanced_stats['critical_chance'] += set_bonus.critical_chance
        
        return enhanced_stats

# Example usage in main bot
def setup_gear_system(bot_instance):
    """Setup gear system for the bot"""
    gear_system = GearSystem()
    drop_manager = GearDropManager(gear_system)
    event_scheduler = GearEventScheduler(gear_system, drop_manager)
    
    # Store in bot data
    bot_instance.bot_data['gear_system'] = gear_system
    bot_instance.bot_data['gear_drop_manager'] = drop_manager
    bot_instance.bot_data['gear_event_scheduler'] = event_scheduler
    
    # Add command handlers
    from .gear_commands import (
        GearCommands, equip_command, salvage_command, 
        gear_drop_command, handle_salvage_confirmation
    )
    
    gear_commands = GearCommands(gear_system)
    
    # Add conversation handler
    bot_instance.add_handler(gear_commands.get_conversation_handler())
    
    # Add quick commands
    bot_instance.add_handler(CommandHandler('equip', equip_command))
    bot_instance.add_handler(CommandHandler('salvage', salvage_command))
    bot_instance.add_handler(CommandHandler('geardrop', gear_drop_command))
    
    # Add callback handlers
    bot_instance.add_handler(
        CallbackQueryHandler(handle_salvage_confirmation, pattern='^(confirm_salvage_|cancel_salvage)')
    )
    
    logger.info("Gear system initialized and ready for combat!")
    
    return gear_system, drop_manager, event_scheduler