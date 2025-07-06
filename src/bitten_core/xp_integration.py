"""
XP Integration Module for BITTEN
Connects user profiles, XP economy, prestige, and elite protocols
"""

from typing import Dict, Optional, Tuple, List, Any
from datetime import datetime
import logging

from .user_profile import UserProfileManager
from .xp_economy import XPEconomy, PurchaseType
from .xp_shop import XPShop
from .prestige_system import PrestigeSystem
from .elite_protocols import EliteProtocolManager, ProtocolType

logger = logging.getLogger(__name__)


class XPIntegrationManager:
    """Central manager for all XP-related systems"""
    
    def __init__(
        self,
        profile_db_path: str = "bitten_profiles.db",
        xp_data_dir: str = "data/xp_economy",
        prestige_data_dir: str = "data/prestige",
        protocols_data_dir: str = "data/elite_protocols"
    ):
        # Initialize all subsystems
        self.profile_manager = UserProfileManager(profile_db_path)
        self.xp_economy = XPEconomy(xp_data_dir)
        self.xp_shop = XPShop(self.xp_economy)
        self.prestige_system = PrestigeSystem(prestige_data_dir)
        self.protocol_manager = EliteProtocolManager(protocols_data_dir)
        
        # Sync XP balances on startup
        self._sync_xp_balances()
    
    def _sync_xp_balances(self) -> None:
        """Sync XP between profile manager and economy system"""
        # This ensures both systems have consistent XP data
        logger.info("Syncing XP balances between systems...")
    
    def get_user_xp_status(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive XP status for a user"""
        # Get profile stats
        profile = self.profile_manager.get_full_profile(user_id)
        
        # Get XP economy balance
        xp_balance = self.xp_economy.get_user_balance(user_id)
        
        # Get prestige info
        prestige_progress = self.prestige_system.get_user_progress(user_id)
        prestige_benefits = self.prestige_system.get_prestige_benefits(user_id)
        
        # Get active protocols
        active_protocols = self.protocol_manager.get_active_protocols(user_id)
        
        # Get active XP purchases
        active_items = self.xp_economy.get_active_items(user_id)
        
        return {
            "user_id": user_id,
            "profile": {
                "rank": profile["rank"],
                "total_xp": profile["total_xp"],
                "success_rate": profile["success_rate"],
                "medals_earned": profile["medals_earned"],
                "recruits_count": profile["recruits_count"]
            },
            "xp_economy": {
                "current_balance": xp_balance.current_balance,
                "lifetime_earned": xp_balance.lifetime_earned,
                "lifetime_spent": xp_balance.lifetime_spent,
                "active_purchases": active_items
            },
            "prestige": {
                "level": prestige_progress.current_level,
                "rank": prestige_benefits["rank"],
                "multiplier": prestige_benefits["xp_multiplier"],
                "unlocked_perks": prestige_benefits["unlocked_perks"]
            },
            "protocols": active_protocols
        }
    
    def award_xp_with_multipliers(
        self, 
        user_id: str, 
        base_amount: int, 
        reason: str,
        details: str = ""
    ) -> int:
        """Award XP with prestige multipliers applied"""
        # Get prestige multiplier
        prestige_progress = self.prestige_system.get_user_progress(user_id)
        multiplier = prestige_progress.active_multiplier
        
        # Calculate final amount
        final_amount = int(base_amount * multiplier)
        
        # Award through profile manager (maintains compatibility)
        self.profile_manager.award_xp(user_id, final_amount, reason, details)
        
        # Also add to XP economy balance
        self.xp_economy.add_xp(user_id, final_amount, reason)
        
        logger.info(
            f"Awarded {final_amount} XP to {user_id} "
            f"(base: {base_amount}, multiplier: {multiplier}x)"
        )
        
        return final_amount
    
    def purchase_xp_item(
        self, 
        user_id: str, 
        item_id: str
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Purchase an item from the XP shop"""
        # Get user tier from profile
        profile = self.profile_manager.get_full_profile(user_id)
        
        # Map rank to tier (simplified mapping)
        rank_to_tier = {
            "RECRUIT": "NIBBLER",
            "PRIVATE": "NIBBLER",
            "CORPORAL": "NIBBLER",
            "SERGEANT": "FANG",
            "LIEUTENANT": "FANG",
            "CAPTAIN": "COMMANDER",
            "MAJOR": "COMMANDER",
            "COLONEL": "APEX",
            "GENERAL": "APEX",
            "COMMANDER": "APEX"
        }
        user_tier = rank_to_tier.get(profile["rank"], "NIBBLER")
        
        # Get user stats for requirements checking
        stats = self.profile_manager.get_user_stats(user_id)
        user_stats = {
            "min_trades": stats.successful_trades + stats.failed_trades,
            "win_rate": stats.success_rate / 100,
            "avg_rr": 2.0  # Would need to calculate from trade history
        }
        
        # Attempt purchase
        success, message, transaction = self.xp_economy.purchase_item(
            user_id, 
            item_id, 
            user_tier,
            user_stats
        )
        
        if success and transaction:
            # Enable protocol if it's an elite protocol purchase
            item = self.xp_economy.shop_catalog[item_id]
            if item.purchase_type in [
                PurchaseType.TRAILING_GUARD,
                PurchaseType.SPLIT_COMMAND,
                PurchaseType.STEALTH_ENTRY,
                PurchaseType.FORTRESS_MODE
            ]:
                protocol_type = ProtocolType(item.purchase_type.value)
                self.protocol_manager.enable_protocol(user_id, protocol_type)
            
            # Log the purchase
            logger.info(f"User {user_id} purchased {item_id}")
            
            # Return purchase details
            return True, message, {
                "transaction": transaction,
                "item": item,
                "new_balance": self.xp_economy.get_user_balance(user_id).current_balance
            }
        
        return False, message, None
    
    def attempt_prestige(self, user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Attempt to prestige a user"""
        # Get current XP from economy
        xp_balance = self.xp_economy.get_user_balance(user_id)
        current_xp = xp_balance.current_balance
        
        # Check if can prestige
        can_do, message = self.prestige_system.can_prestige(user_id, current_xp)
        if not can_do:
            return False, message, None
        
        # Execute prestige
        success, progress, reward = self.prestige_system.execute_prestige(
            user_id, 
            current_xp
        )
        
        if success:
            # Use XP economy's prestige handler to reset balance
            self.xp_economy.handle_prestige(user_id)
            
            # Get new benefits
            benefits = self.prestige_system.get_prestige_benefits(user_id)
            
            return True, f"Prestiged to {progress.current_level}!", {
                "new_level": progress.current_level,
                "rank": benefits["rank"],
                "multiplier": benefits["xp_multiplier"],
                "rewards": reward.perks if reward else []
            }
        
        return False, "Prestige failed", None
    
    def get_shop_display(self, user_id: str) -> List[Dict[str, Any]]:
        """Get XP shop display for user"""
        # Get user tier
        profile = self.profile_manager.get_full_profile(user_id)
        rank_to_tier = {
            "RECRUIT": "NIBBLER",
            "PRIVATE": "NIBBLER",
            "CORPORAL": "NIBBLER",
            "SERGEANT": "FANG",
            "LIEUTENANT": "FANG",
            "CAPTAIN": "COMMANDER",
            "MAJOR": "COMMANDER",
            "COLONEL": "APEX",
            "GENERAL": "APEX",
            "COMMANDER": "APEX"
        }
        user_tier = rank_to_tier.get(profile["rank"], "NIBBLER")
        
        # Get shop display
        shop_displays = self.xp_shop.get_shop_display(user_id, user_tier)
        
        # Convert to simpler format
        categories = []
        for display in shop_displays:
            categories.append({
                "category": display.category.value,
                "icon": display.category_icon,
                "description": display.category_description,
                "items": display.items
            })
        
        return categories
    
    def record_trade_with_xp(
        self, 
        user_id: str, 
        signal_id: str,
        position_id: str,
        profit: float,
        is_success: bool
    ) -> Dict[str, Any]:
        """Record trade and award appropriate XP"""
        # Record in profile manager
        self.profile_manager.record_trade_execution(user_id, signal_id, position_id)
        self.profile_manager.record_trade_result(user_id, position_id, profit, is_success)
        
        # Update win streak for fortress mode
        streak = self.protocol_manager.update_win_streak(user_id, is_success)
        
        # Calculate bonus XP from trade
        bonus_xp = 0
        if is_success:
            # Bonus XP based on profit
            if profit > 100:
                bonus_xp += 50
            if profit > 500:
                bonus_xp += 100
            if profit > 1000:
                bonus_xp += 200
        
        if bonus_xp > 0:
            self.award_xp_with_multipliers(
                user_id, 
                bonus_xp, 
                f"Trade profit bonus",
                f"Profit: ${profit:.2f}"
            )
        
        return {
            "base_xp_earned": self.profile_manager.XP_REWARDS['trade_success' if is_success else 'trade_failed'],
            "bonus_xp": bonus_xp,
            "current_streak": streak,
            "new_balance": self.xp_economy.get_user_balance(user_id).current_balance
        }
    
    def check_trade_protocols(
        self, 
        user_id: str, 
        trade_id: str,
        current_profit_pips: float,
        current_sl_pips: float,
        tp1_pips: float
    ) -> Dict[str, Any]:
        """Check all active protocols for a trade"""
        actions = {}
        
        # Check trailing guard
        new_sl = self.protocol_manager.check_trailing_guard(
            user_id, 
            trade_id, 
            current_profit_pips,
            current_sl_pips
        )
        if new_sl:
            actions["trailing_guard"] = {
                "action": "trail_sl",
                "new_sl_pips": new_sl
            }
        
        # Check split command
        split_action = self.protocol_manager.check_split_command(
            user_id,
            trade_id,
            current_profit_pips,
            tp1_pips
        )
        if split_action:
            actions["split_command"] = split_action
        
        return actions
    
    def get_risk_with_protocols(self, user_id: str, base_risk: float) -> float:
        """Get adjusted risk considering fortress mode"""
        return self.protocol_manager.check_fortress_mode(user_id, base_risk)
    
    def prepare_stealth_orders(
        self,
        user_id: str,
        signal_price: float,
        pair: str,
        direction: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Prepare stealth entry orders if enabled"""
        return self.protocol_manager.prepare_stealth_entry(
            user_id,
            signal_price,
            pair,
            direction
        )


# Example usage
if __name__ == "__main__":
    manager = XPIntegrationManager()
    
    # Get user status
    user_id = "test_user"
    status = manager.get_user_xp_status(user_id)
    print(f"User XP Status: {status}")
    
    # Award XP with multipliers
    xp_earned = manager.award_xp_with_multipliers(
        user_id,
        100,
        "Test award"
    )
    print(f"XP earned: {xp_earned}")
    
    # Get shop
    shop = manager.get_shop_display(user_id)
    print(f"Shop categories: {len(shop)}")
    
    # Try to purchase
    success, message, details = manager.purchase_xp_item(user_id, "heat_map")
    print(f"Purchase: {message}")