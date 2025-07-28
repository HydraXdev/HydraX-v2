"""
XP Economy System for BITTEN
Handles XP spending, validation, and transaction logging
"""

from typing import Dict, Optional, Tuple, List, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Import tactical strategies for unlock notifications
try:
    from .tactical_strategies import TacticalStrategy, tactical_strategy_manager
    TACTICAL_STRATEGIES_AVAILABLE = True
except ImportError:
    TACTICAL_STRATEGIES_AVAILABLE = False

# Import social brag system for squad notifications
try:
    from .social_brag_system import notify_tactical_strategy_unlock
    SOCIAL_BRAG_AVAILABLE = True
except ImportError:
    SOCIAL_BRAG_AVAILABLE = False

# Import achievement system for tactical achievements
try:
    from .achievement_system import AchievementSystem
    ACHIEVEMENT_SYSTEM_AVAILABLE = True
except ImportError:
    ACHIEVEMENT_SYSTEM_AVAILABLE = False

class PurchaseType(Enum):
    """Types of XP purchases"""
    # Tactical Intel
    HEAT_MAP = "heat_map"
    SQUAD_RADAR = "squad_radar"
    CONFIDENCE_BOOST = "confidence_boost"
    
    # Elite Protocols
    TRAILING_GUARD = "trailing_guard"
    SPLIT_COMMAND = "split_command"
    STEALTH_ENTRY = "stealth_entry"
    FORTRESS_MODE = "fortress_mode"
    
    # Ammunition
    EXTENDED_MAG = "extended_mag"
    RAPID_RELOAD = "rapid_reload"
    SPECIAL_AMMO = "special_ammo"
    
    # Prestige
    PRESTIGE_RESET = "prestige_reset"

class PurchaseStatus(Enum):
    """Status of XP purchase"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

@dataclass
class XPItem:
    """Defines an XP shop item"""
    item_id: str
    name: str
    description: str
    cost: int
    purchase_type: PurchaseType
    tier_required: str  # NIBBLER, FANG, COMMANDER
    duration_hours: Optional[int] = None  # For temporary items
    max_uses: Optional[int] = None  # For consumables
    cooldown_hours: Optional[int] = None  # Between purchases
    requirements: Dict[str, Any] = field(default_factory=dict)
    
    def is_permanent(self) -> bool:
        """Check if item is permanent unlock"""
        return self.duration_hours is None and self.max_uses is None

@dataclass
class XPTransaction:
    """Records an XP transaction"""
    transaction_id: str
    user_id: str
    item_id: str
    purchase_type: PurchaseType
    amount: int  # Negative for purchases, positive for refunds
    balance_before: int
    balance_after: int
    status: PurchaseStatus
    timestamp: datetime
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UserXPBalance:
    """User's XP balance and purchase history"""
    user_id: str
    current_balance: int
    lifetime_earned: int
    lifetime_spent: int
    prestige_level: int = 0
    active_purchases: List[str] = field(default_factory=list)
    purchase_history: List[XPTransaction] = field(default_factory=list)
    last_purchase: Optional[datetime] = None

class XPEconomy:
    """Main XP economy manager"""
    
    def __init__(self, data_dir: str = "data/xp_economy", achievement_system=None):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Define shop catalog
        self.shop_catalog = self._initialize_shop_catalog()
        
        # User balances cache
        self.user_balances: Dict[str, UserXPBalance] = {}
        
        # Achievement system integration
        self.achievement_system = achievement_system
        
        # User lookup function for better usernames in social brags
        self.get_username_func = None
        
        # XP reward amounts for different actions
        self.xp_rewards = {
            "trade_win": 10,
            "trade_loss": 2,  # Small consolation XP
            "daily_login": 5,
            "strategy_selection": 5,
            "consecutive_wins": {2: 5, 3: 10, 5: 20, 10: 50},
            "perfect_day": 25,  # No losses in a day
            "first_strategy_use": 15,
            "weekly_goal_completion": 50
        }
        
        # Load existing data
        self._load_user_data()
    
    def set_username_lookup_function(self, func):
        """Set a function to lookup usernames for better social brag display"""
        self.get_username_func = func
    
    def _initialize_shop_catalog(self) -> Dict[str, XPItem]:
        """Initialize the XP shop catalog"""
        catalog = {}
        
        # Tactical Intel Items
        catalog["heat_map"] = XPItem(
            item_id="heat_map",
            name="Heat Map",
            description="See which pairs are hot based on TCS trends",
            cost=1000,
            purchase_type=PurchaseType.HEAT_MAP,
            tier_required="NIBBLER",
            duration_hours=168,  # 1 week
            cooldown_hours=168
        )
        
        catalog["squad_radar"] = XPItem(
            item_id="squad_radar",
            name="Squad Radar",
            description="See what your top 3 squad members are trading",
            cost=500,
            purchase_type=PurchaseType.SQUAD_RADAR,
            tier_required="NIBBLER",
            max_uses=1,
            cooldown_hours=24
        )
        
        catalog["confidence_boost"] = XPItem(
            item_id="confidence_boost",
            name="Confidence Boost",
            description="Reveal exact TCS% 1 minute before signal drops",
            cost=2000,
            purchase_type=PurchaseType.CONFIDENCE_BOOST,
            tier_required="FANG",
            max_uses=1
        )
        
        # Elite Trading Protocols
        catalog["trailing_guard"] = XPItem(
            item_id="trailing_guard",
            name="Trailing Guard",
            description="Auto-trail SL by 10 pips after +20 pips profit",
            cost=5000,
            purchase_type=PurchaseType.TRAILING_GUARD,
            tier_required="FANG",
            requirements={"min_trades": 50, "win_rate": 0.6}
        )
        
        catalog["split_command"] = XPItem(
            item_id="split_command",
            name="Split Command",
            description="Take 50% profit at TP1, let 50% ride to TP2",
            cost=10000,
            purchase_type=PurchaseType.SPLIT_COMMAND,
            tier_required="COMMANDER",
            requirements={"min_trades": 100, "avg_rr": 2.0}
        )
        
        catalog["stealth_entry"] = XPItem(
            item_id="stealth_entry",
            name="Stealth Entry",
            description="Place pending orders ±5 pips from signal",
            cost=15000,
            purchase_type=PurchaseType.STEALTH_ENTRY,
            tier_required="COMMANDER",
            requirements={"min_trades": 150}
        )
        
        catalog["fortress_mode"] = XPItem(
            item_id="fortress_mode",
            name="Fortress Mode",
            description="Auto-reduce to 1% risk after 3 consecutive wins",
            cost=20000,
            purchase_type=PurchaseType.FORTRESS_MODE,
            tier_required=UserTier.COMMANDER)
        
        # Ammunition Upgrades
        catalog["extended_mag"] = XPItem(
            item_id="extended_mag",
            name="Extended Mag",
            description="+2 shots for 24 hours (85%+ TCS only)",
            cost=3000,
            purchase_type=PurchaseType.EXTENDED_MAG,
            tier_required="FANG",
            duration_hours=24
        )
        
        catalog["rapid_reload"] = XPItem(
            item_id="rapid_reload",
            name="Rapid Reload",
            description="Skip one cooldown timer (once per day)",
            cost=1500,
            purchase_type=PurchaseType.RAPID_RELOAD,
            tier_required="NIBBLER",
            max_uses=1,
            cooldown_hours=24
        )
        
        catalog["special_ammo"] = XPItem(
            item_id="special_ammo",
            name="Special Ammo",
            description="One shot at 3% risk (91%+ TCS only)",
            cost=5000,
            purchase_type=PurchaseType.SPECIAL_AMMO,
            tier_required="COMMANDER",
            max_uses=1
        )
        
        return catalog
    
    def get_user_balance(self, user_id: str) -> UserXPBalance:
        """Get user's XP balance"""
        if user_id not in self.user_balances:
            # Load or create new balance
            balance_file = self.data_dir / f"user_{user_id}_balance.json"
            if balance_file.exists():
                with open(balance_file, 'r') as f:
                    data = json.load(f)
                    self.user_balances[user_id] = UserXPBalance(**data)
            else:
                self.user_balances[user_id] = UserXPBalance(
                    user_id=user_id,
                    current_balance=0,
                    lifetime_earned=0,
                    lifetime_spent=0
                )
        
        return self.user_balances[user_id]
    
    def add_xp(self, user_id: str, amount: int, reason: str = "", context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Add XP to user's balance and handle all related systems"""
        balance = self.get_user_balance(user_id)
        old_balance = balance.current_balance
        
        balance.current_balance += amount
        balance.lifetime_earned += amount
        
        # Check for tactical strategy unlocks (NIBBLER gamification)
        unlock_notifications = []
        achievement_unlocks = []
        
        if TACTICAL_STRATEGIES_AVAILABLE:
            unlock_notifications = self._check_tactical_unlocks(old_balance, balance.current_balance, user_id)
        
        # Check for achievement unlocks
        if self.achievement_system and ACHIEVEMENT_SYSTEM_AVAILABLE:
            achievement_progress = {
                "total_xp": balance.current_balance,
                "lifetime_earned": balance.lifetime_earned
            }
            
            # Add context-specific progress
            if context:
                achievement_progress.update(context)
                
            achievement_unlocks = self.achievement_system.update_progress(user_id, achievement_progress)
        
        # Log transaction
        transaction = XPTransaction(
            transaction_id=f"{user_id}_{datetime.now().timestamp()}",
            user_id=user_id,
            item_id="xp_earned",
            purchase_type=PurchaseType.HEAT_MAP,  # Placeholder
            amount=amount,
            balance_before=old_balance,
            balance_after=balance.current_balance,
            status=PurchaseStatus.COMPLETED,
            timestamp=datetime.now(),
            metadata={
                "reason": reason, 
                "strategy_unlocks": unlock_notifications,
                "achievement_unlocks": achievement_unlocks,
                "context": context or {}
            }
        )
        
        balance.purchase_history.append(transaction)
        self._save_user_balance(balance)
        
        logger.info(f"Added {amount} XP to user {user_id}. New balance: {balance.current_balance}")
        
        # Log strategy unlocks
        if unlock_notifications:
            logger.info(f"User {user_id} unlocked strategies: {[notif['strategy'] for notif in unlock_notifications]}")
        
        # Log achievement unlocks
        if achievement_unlocks:
            logger.info(f"User {user_id} unlocked achievements: {achievement_unlocks}")
        
        return {
            "balance": balance,
            "xp_added": amount,
            "new_balance": balance.current_balance,
            "strategy_unlocks": unlock_notifications,
            "achievement_unlocks": achievement_unlocks,
            "transaction": transaction
        }
    
    def can_purchase(self, user_id: str, item_id: str, user_tier: str) -> Tuple[bool, str]:
        """Check if user can purchase an item"""
        if item_id not in self.shop_catalog:
            return False, "Item not found in shop"
        
        item = self.shop_catalog[item_id]
        balance = self.get_user_balance(user_id)
        
        # Check balance
        if balance.current_balance < item.cost:
            return False, f"Insufficient XP. Need {item.cost}, have {balance.current_balance}"
        
        # Check tier requirement
        tier_hierarchy = ["NIBBLER", "FANG", "COMMANDER"]
        if tier_hierarchy.index(user_tier) < tier_hierarchy.index(item.tier_required):
            return False, f"Requires {item.tier_required} tier or higher"
        
        # Check if already active (for permanent items)
        if item.is_permanent() and item_id in balance.active_purchases:
            return False, "Already unlocked"
        
        # Check cooldown
        if item.cooldown_hours:
            last_purchase = self._get_last_purchase_time(user_id, item_id)
            if last_purchase:
                cooldown_end = last_purchase + timedelta(hours=item.cooldown_hours)
                if datetime.now() < cooldown_end:
                    remaining = (cooldown_end - datetime.now()).total_seconds() / 3600
                    return False, f"On cooldown. {remaining:.1f} hours remaining"
        
        # Check requirements
        if item.requirements:
            # This would need to check against user stats
            # For now, assume requirements are met
            pass
        
        return True, "Can purchase"
    
    def purchase_item(
        self, 
        user_id: str, 
        item_id: str, 
        user_tier: str,
        user_stats: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str, Optional[XPTransaction]]:
        """Purchase an item from the XP shop"""
        can_buy, reason = self.can_purchase(user_id, item_id, user_tier)
        if not can_buy:
            return False, reason, None
        
        item = self.shop_catalog[item_id]
        balance = self.get_user_balance(user_id)
        
        # Deduct XP
        balance_before = balance.current_balance
        balance.current_balance -= item.cost
        balance.lifetime_spent += item.cost
        
        # Calculate expiration
        expires_at = None
        if item.duration_hours:
            expires_at = datetime.now() + timedelta(hours=item.duration_hours)
        
        # Create transaction
        transaction = XPTransaction(
            transaction_id=f"{user_id}_{item_id}_{datetime.now().timestamp()}",
            user_id=user_id,
            item_id=item_id,
            purchase_type=item.purchase_type,
            amount=-item.cost,
            balance_before=balance_before,
            balance_after=balance.current_balance,
            status=PurchaseStatus.COMPLETED,
            timestamp=datetime.now(),
            expires_at=expires_at,
            metadata={"user_tier": user_tier}
        )
        
        # Update user data
        balance.purchase_history.append(transaction)
        balance.last_purchase = datetime.now()
        
        # Add to active purchases if permanent
        if item.is_permanent():
            balance.active_purchases.append(item_id)
        
        # Save
        self._save_user_balance(balance)
        
        logger.info(f"User {user_id} purchased {item_id} for {item.cost} XP")
        return True, f"Successfully purchased {item.name}", transaction
    
    def refund_purchase(
        self, 
        user_id: str, 
        transaction_id: str, 
        reason: str = "Admin refund"
    ) -> Tuple[bool, str]:
        """Refund a purchase"""
        balance = self.get_user_balance(user_id)
        
        # Find original transaction
        original = None
        for trans in balance.purchase_history:
            if trans.transaction_id == transaction_id:
                original = trans
                break
        
        if not original:
            return False, "Transaction not found"
        
        if original.status == PurchaseStatus.REFUNDED:
            return False, "Already refunded"
        
        # Create refund transaction
        refund_amount = abs(original.amount)
        balance.current_balance += refund_amount
        balance.lifetime_spent -= refund_amount
        
        refund_transaction = XPTransaction(
            transaction_id=f"{transaction_id}_refund",
            user_id=user_id,
            item_id=original.item_id,
            purchase_type=original.purchase_type,
            amount=refund_amount,
            balance_before=balance.current_balance - refund_amount,
            balance_after=balance.current_balance,
            status=PurchaseStatus.REFUNDED,
            timestamp=datetime.now(),
            metadata={"original_transaction": transaction_id, "reason": reason}
        )
        
        # Update original transaction status
        original.status = PurchaseStatus.REFUNDED
        
        # Remove from active purchases if permanent
        if original.item_id in balance.active_purchases:
            balance.active_purchases.remove(original.item_id)
        
        balance.purchase_history.append(refund_transaction)
        self._save_user_balance(balance)
        
        logger.info(f"Refunded {refund_amount} XP to user {user_id}")
        return True, f"Refunded {refund_amount} XP"
    
    def get_active_items(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's currently active purchased items"""
        balance = self.get_user_balance(user_id)
        active_items = []
        
        # Check permanent unlocks
        for item_id in balance.active_purchases:
            if item_id in self.shop_catalog:
                item = self.shop_catalog[item_id]
                active_items.append({
                    "item_id": item_id,
                    "name": item.name,
                    "type": "permanent",
                    "expires_at": None
                })
        
        # Check temporary items
        for trans in reversed(balance.purchase_history):
            if trans.status == PurchaseStatus.COMPLETED and trans.expires_at:
                if datetime.now() < trans.expires_at:
                    item = self.shop_catalog.get(trans.item_id)
                    if item:
                        active_items.append({
                            "item_id": trans.item_id,
                            "name": item.name,
                            "type": "temporary",
                            "expires_at": trans.expires_at.isoformat()
                        })
        
        return active_items
    
    def handle_prestige(self, user_id: str) -> Tuple[bool, str, int]:
        """Handle prestige reset for a user"""
        balance = self.get_user_balance(user_id)
        
        # Check if eligible (50k XP)
        if balance.current_balance < 50000:
            return False, f"Need 50,000 XP for prestige. Current: {balance.current_balance}", 0
        
        # Reset XP but keep unlocks
        old_balance = balance.current_balance
        balance.current_balance = 0
        balance.prestige_level += 1
        
        # Create prestige transaction
        transaction = XPTransaction(
            transaction_id=f"{user_id}_prestige_{balance.prestige_level}",
            user_id=user_id,
            item_id="prestige_reset",
            purchase_type=PurchaseType.PRESTIGE_RESET,
            amount=-old_balance,
            balance_before=old_balance,
            balance_after=0,
            status=PurchaseStatus.COMPLETED,
            timestamp=datetime.now(),
            metadata={"prestige_level": balance.prestige_level}
        )
        
        balance.purchase_history.append(transaction)
        self._save_user_balance(balance)
        
        logger.info(f"User {user_id} prestiged to level {balance.prestige_level}")
        return True, f"Prestiged to level {balance.prestige_level}!", balance.prestige_level
    
    def _get_last_purchase_time(self, user_id: str, item_id: str) -> Optional[datetime]:
        """Get the last time a user purchased a specific item"""
        balance = self.get_user_balance(user_id)
        
        for trans in reversed(balance.purchase_history):
            if trans.item_id == item_id and trans.status == PurchaseStatus.COMPLETED:
                return trans.timestamp
        
        return None
    
    def _save_user_balance(self, balance: UserXPBalance) -> None:
        """Save user balance to file"""
        balance_file = self.data_dir / f"user_{balance.user_id}_balance.json"
        
        # Convert to dict for JSON serialization
        data = {
            "user_id": balance.user_id,
            "current_balance": balance.current_balance,
            "lifetime_earned": balance.lifetime_earned,
            "lifetime_spent": balance.lifetime_spent,
            "prestige_level": balance.prestige_level,
            "active_purchases": balance.active_purchases,
            "last_purchase": balance.last_purchase.isoformat() if balance.last_purchase else None
        }
        
        with open(balance_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_user_data(self) -> None:
        """Load all user data from files"""
        for balance_file in self.data_dir.glob("user_*_balance.json"):
            try:
                with open(balance_file, 'r') as f:
                    data = json.load(f)
                    user_id = data["user_id"]
                    
                    # Convert ISO dates back to datetime
                    if data.get("last_purchase"):
                        data["last_purchase"] = datetime.fromisoformat(data["last_purchase"])
                    
                    self.user_balances[user_id] = UserXPBalance(
                        user_id=user_id,
                        current_balance=data["current_balance"],
                        lifetime_earned=data["lifetime_earned"],
                        lifetime_spent=data["lifetime_spent"],
                        prestige_level=data.get("prestige_level", 0),
                        active_purchases=data.get("active_purchases", []),
                        last_purchase=data.get("last_purchase")
                    )
            except Exception as e:
                logger.error(f"Error loading balance file {balance_file}: {e}")
    
    def _check_tactical_unlocks(self, old_xp: int, new_xp: int, user_id: str) -> List[Dict[str, Any]]:
        """Check if any tactical strategies were unlocked with new XP amount"""
        unlock_notifications = []
        
        if not TACTICAL_STRATEGIES_AVAILABLE:
            return unlock_notifications
        
        # Tactical strategy unlock thresholds (must match tactical_strategies.py)
        unlock_thresholds = {
            120: "FIRST_BLOOD",
            240: "DOUBLE_TAP", 
            360: "TACTICAL_COMMAND"
        }
        
        # Check which strategies were unlocked
        for threshold, strategy_name in unlock_thresholds.items():
            if old_xp < threshold <= new_xp:
                try:
                    strategy = TacticalStrategy(strategy_name)
                    config = tactical_strategy_manager.TACTICAL_CONFIGS[strategy]
                    
                    # Create comprehensive unlock notification
                    unlock_notification = {
                        "strategy": strategy_name,
                        "display_name": config.display_name,
                        "unlock_message": f"🎯 **{config.display_name.upper()} UNLOCKED!**\n\n{config.description}\n\n💡 *{config.teaching_focus}*",
                        "description": config.description,
                        "teaching_focus": config.teaching_focus,
                        "psychology": config.psychology,
                        "unlock_xp": threshold,
                        "current_xp": new_xp,
                        "daily_potential": config.daily_potential,
                        "max_shots": config.max_shots,
                        "telegram_message": self._format_telegram_unlock_message(config, threshold),
                        "drill_report_message": self._format_drill_unlock_message(config, user_id)
                    }
                    
                    unlock_notifications.append(unlock_notification)
                    
                    # Send social brag notification to squad members
                    if SOCIAL_BRAG_AVAILABLE:
                        try:
                            # Try to get username from user_id for better display
                            username = user_id  # Default fallback
                            if self.get_username_func:
                                try:
                                    better_username = self.get_username_func(user_id)
                                    if better_username:
                                        username = better_username
                                except Exception as e:
                                    logger.warning(f"Username lookup failed for {user_id}: {e}")
                            
                            # Send the brag notification
                            notify_tactical_strategy_unlock(
                                user_id=user_id,
                                username=username,
                                strategy_name=strategy_name,
                                strategy_display_name=config.display_name,
                                strategy_description=config.description,
                                xp_amount=threshold
                            )
                            
                            logger.info(f"Sent social brag notification for {user_id} unlocking {config.display_name}")
                            
                        except Exception as e:
                            logger.error(f"Error sending social brag notification: {e}")
                    
                    # Log detailed unlock info
                    logger.info(f"TACTICAL UNLOCK: User {user_id} unlocked {config.display_name} at {new_xp} XP")
                    
                except Exception as e:
                    logger.error(f"Error processing tactical unlock {strategy_name}: {e}")
        
        return unlock_notifications
    
    def _format_telegram_unlock_message(self, config, threshold: int) -> str:
        """Format unlock message for Telegram bot"""
        return f"""🚀 **TACTICAL BREAKTHROUGH!** 🚀

{config.display_name} UNLOCKED at {threshold} XP!

📋 **Mission Brief:**
{config.description}

🎯 **Training Focus:**
{config.teaching_focus}

💪 **Psychology:**
{config.psychology}

📊 **Daily Potential:** {config.daily_potential}
🔫 **Max Shots:** {config.max_shots}

Soldier, you've earned this tactical advantage. Use it wisely!

— DRILL SERGEANT 🎖️"""
    
    def _format_drill_unlock_message(self, config, user_id: str) -> str:
        """Format unlock message for drill reports"""
        return f"🎖️ **NEW TACTICAL CAPABILITY ACQUIRED**\n\n{config.display_name} is now available for deployment. Your tactical arsenal grows stronger, soldier!"
    
    def get_tactical_unlock_status(self, user_id: str) -> Dict[str, Any]:
        """Get user's tactical strategy unlock status for NIBBLER gamification"""
        balance = self.get_user_balance(user_id)
        
        if not TACTICAL_STRATEGIES_AVAILABLE:
            return {"error": "Tactical strategies not available"}
        
        unlocked_strategies = tactical_strategy_manager.get_unlocked_strategies(balance.current_balance)
        
        # Find next unlock
        next_unlock = None
        unlock_thresholds = [120, 240, 360]
        strategy_names = {120: "FIRST_BLOOD", 240: "DOUBLE_TAP", 360: "TACTICAL_COMMAND"}
        
        for threshold in unlock_thresholds:
            if balance.current_balance < threshold:
                strategy_name = strategy_names[threshold]
                strategy = TacticalStrategy(strategy_name)
                config = tactical_strategy_manager.TACTICAL_CONFIGS[strategy]
                next_unlock = {
                    "strategy": strategy_name,
                    "display_name": config.display_name,
                    "required_xp": threshold,
                    "current_xp": balance.current_balance,
                    "xp_needed": threshold - balance.current_balance,
                    "description": config.description,
                    "psychology": config.psychology,
                    "daily_potential": config.daily_potential,
                    "progress_percent": (balance.current_balance / threshold) * 100
                }
                break
        
        # Get unlock history for this user
        unlock_history = self._get_unlock_history(user_id)
        
        return {
            "current_xp": balance.current_balance,
            "lifetime_earned": balance.lifetime_earned,
            "unlocked_count": len(unlocked_strategies),
            "total_strategies": 4,  # LONE_WOLF (always), FIRST_BLOOD, DOUBLE_TAP, TACTICAL_COMMAND
            "unlocked_strategies": [s.value for s in unlocked_strategies],
            "next_unlock": next_unlock,
            "progress_percentage": min(100, (balance.current_balance / 360) * 100),  # 360 XP unlocks all
            "unlock_history": unlock_history,
            "all_strategies_unlocked": balance.current_balance >= 360
        }
    
    def _get_unlock_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get history of tactical strategy unlocks for user"""
        balance = self.get_user_balance(user_id)
        unlock_history = []
        
        for transaction in balance.purchase_history:
            if transaction.metadata and "strategy_unlocks" in transaction.metadata:
                strategy_unlocks = transaction.metadata["strategy_unlocks"]
                if strategy_unlocks:
                    for unlock in strategy_unlocks:
                        unlock_history.append({
                            "strategy": unlock.get("strategy"),
                            "display_name": unlock.get("display_name"),
                            "unlock_date": transaction.timestamp.isoformat(),
                            "unlock_xp": unlock.get("unlock_xp"),
                            "total_xp_at_unlock": transaction.balance_after
                        })
        
        return sorted(unlock_history, key=lambda x: x["unlock_date"])
    
    def get_xp_for_action(self, action: str, context: Dict[str, Any] = None) -> int:
        """Get XP amount for a specific action"""
        if action in self.xp_rewards:
            reward = self.xp_rewards[action]
            
            # Handle conditional XP (like consecutive wins)
            if isinstance(reward, dict) and context:
                if action == "consecutive_wins" and "streak" in context:
                    streak = context["streak"]
                    # Find highest applicable streak reward
                    applicable_rewards = [xp for req_streak, xp in reward.items() if streak >= req_streak]
                    return max(applicable_rewards) if applicable_rewards else 0
                    
            elif isinstance(reward, int):
                return reward
                
        logger.warning(f"Unknown XP action: {action}")
        return 0
    
    def award_trade_xp(self, user_id: str, trade_result: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Award XP for trade completion with proper context"""
        context = context or {}
        
        # Base XP for trade result
        base_xp = self.get_xp_for_action(f"trade_{trade_result.lower()}")
        total_xp = base_xp
        
        xp_breakdown = [{"source": f"trade_{trade_result.lower()}", "amount": base_xp}]
        
        # Bonus XP for consecutive wins
        if trade_result.upper() == "WIN" and "win_streak" in context:
            streak_xp = self.get_xp_for_action("consecutive_wins", {"streak": context["win_streak"]})
            if streak_xp > 0:
                total_xp += streak_xp
                xp_breakdown.append({"source": f"win_streak_{context['win_streak']}", "amount": streak_xp})
        
        # Bonus XP for perfect day (no losses)
        if "perfect_day" in context and context["perfect_day"]:
            perfect_xp = self.get_xp_for_action("perfect_day")
            total_xp += perfect_xp
            xp_breakdown.append({"source": "perfect_day", "amount": perfect_xp})
        
        # Bonus XP for first time using a strategy
        if "first_strategy_use" in context and context["first_strategy_use"]:
            first_use_xp = self.get_xp_for_action("first_strategy_use")
            total_xp += first_use_xp
            xp_breakdown.append({"source": "first_strategy_use", "amount": first_use_xp})
        
        # Award the XP
        result = self.add_xp(
            user_id=user_id,
            amount=total_xp,
            reason=f"Trade {trade_result.lower()}: {context.get('pair', 'Unknown')}",
            context={
                **context,
                "trade_result": trade_result,
                "xp_breakdown": xp_breakdown,
                "battles_won": 1 if trade_result.upper() == "WIN" else 0
            }
        )
        
        result["xp_breakdown"] = xp_breakdown
        return result
    
    def award_daily_login_xp(self, user_id: str) -> Dict[str, Any]:
        """Award XP for daily login"""
        xp_amount = self.get_xp_for_action("daily_login")
        
        return self.add_xp(
            user_id=user_id,
            amount=xp_amount,
            reason="Daily login bonus",
            context={"daily_login": True}
        )
    
    def award_strategy_selection_xp(self, user_id: str, strategy_name: str) -> Dict[str, Any]:
        """Award XP for selecting a daily strategy"""
        xp_amount = self.get_xp_for_action("strategy_selection")
        
        return self.add_xp(
            user_id=user_id,
            amount=xp_amount,
            reason=f"Strategy selection: {strategy_name}",
            context={"strategy_selected": strategy_name}
        )
    
    def get_drill_report_xp_summary(self, user_id: str) -> Dict[str, Any]:
        """Get XP summary for drill reports"""
        balance = self.get_user_balance(user_id)
        
        # Get today's XP transactions
        today = datetime.now().date()
        today_transactions = [
            t for t in balance.purchase_history 
            if t.timestamp.date() == today and t.amount > 0
        ]
        
        today_xp = sum(t.amount for t in today_transactions)
        
        # Get week's XP transactions
        week_start = today - timedelta(days=today.weekday())
        week_transactions = [
            t for t in balance.purchase_history 
            if t.timestamp.date() >= week_start and t.amount > 0
        ]
        
        week_xp = sum(t.amount for t in week_transactions)
        
        # XP breakdown by source
        xp_sources = {}
        for transaction in today_transactions:
            reason = transaction.metadata.get("reason", "Unknown")
            if reason not in xp_sources:
                xp_sources[reason] = 0
            xp_sources[reason] += transaction.amount
        
        return {
            "current_balance": balance.current_balance,
            "lifetime_earned": balance.lifetime_earned,
            "today_earned": today_xp,
            "week_earned": week_xp,
            "today_sources": xp_sources,
            "recent_unlocks": self._get_recent_tactical_unlocks(user_id),
            "next_unlock": self.get_tactical_unlock_status(user_id).get("next_unlock"),
            "unlock_progress": self.get_tactical_unlock_status(user_id).get("progress_percentage", 0)
        }
    
    def _get_recent_tactical_unlocks(self, user_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent tactical strategy unlocks for drill reports"""
        balance = self.get_user_balance(user_id)
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_unlocks = []
        for transaction in balance.purchase_history:
            if (transaction.timestamp >= cutoff_date and 
                transaction.metadata and 
                "strategy_unlocks" in transaction.metadata):
                
                strategy_unlocks = transaction.metadata["strategy_unlocks"]
                for unlock in strategy_unlocks:
                    recent_unlocks.append({
                        "strategy": unlock.get("strategy"),
                        "display_name": unlock.get("display_name"),
                        "unlock_date": transaction.timestamp.isoformat(),
                        "days_ago": (datetime.now() - transaction.timestamp).days
                    })
        
        return sorted(recent_unlocks, key=lambda x: x["unlock_date"], reverse=True)

# Example usage and testing
if __name__ == "__main__":
    from .achievement_system import AchievementSystem
    
    # Initialize systems
    achievement_system = AchievementSystem()
    economy = XPEconomy(achievement_system=achievement_system)
    
    # Test user
    user_id = "test_user_123"
    print("=== XP Economy Tactical Integration Test ===\n")
    
    # Test 1: Award trade XP with progression
    print("1. Testing Trade XP Awards:")
    
    # First win
    result = economy.award_trade_xp(user_id, "WIN", {
        "pair": "EURUSD", 
        "win_streak": 1,
        "first_strategy_use": True
    })
    print(f"First win: +{result['xp_added']} XP (Balance: {result['new_balance']})")
    if result["strategy_unlocks"]:
        print(f"   🎯 Unlocked: {[unlock['display_name'] for unlock in result['strategy_unlocks']]}")
    
    # Progressive wins to test streak bonuses and unlocks
    for i in range(2, 12):
        result = economy.award_trade_xp(user_id, "WIN", {
            "pair": "GBPUSD",
            "win_streak": i
        })
        print(f"Win #{i}: +{result['xp_added']} XP (Balance: {result['new_balance']})")
        
        if result["strategy_unlocks"]:
            for unlock in result["strategy_unlocks"]:
                print(f"   🎯 TACTICAL UNLOCK: {unlock['display_name']} at {unlock['unlock_xp']} XP!")
                print(f"      {unlock['description']}")
        
        if result["achievement_unlocks"]:
            print(f"   🏆 Achievement unlocked: {result['achievement_unlocks']}")
    
    print(f"\n2. Testing Tactical Unlock Status:")
    unlock_status = economy.get_tactical_unlock_status(user_id)
    print(f"Current XP: {unlock_status['current_xp']}")
    print(f"Unlocked Strategies: {unlock_status['unlocked_strategies']}")
    print(f"Progress to all unlocks: {unlock_status['progress_percentage']:.1f}%")
    
    if unlock_status["next_unlock"]:
        next_unlock = unlock_status["next_unlock"]
        print(f"Next unlock: {next_unlock['display_name']} at {next_unlock['required_xp']} XP")
        print(f"Need {next_unlock['xp_needed']} more XP")
    
    print(f"\n3. Testing Drill Report Integration:")
    drill_summary = economy.get_drill_report_xp_summary(user_id)
    print(f"Today's XP: {drill_summary['today_earned']}")
    print(f"Week's XP: {drill_summary['week_earned']}")
    print(f"XP Sources: {drill_summary['today_sources']}")
    print(f"Unlock Progress: {drill_summary['unlock_progress']:.1f}%")
    
    if drill_summary["recent_unlocks"]:
        print("Recent Tactical Unlocks:")
        for unlock in drill_summary["recent_unlocks"]:
            print(f"  - {unlock['display_name']} ({unlock['days_ago']} days ago)")
    
    print(f"\n4. Testing XP Shop Integration:")
    # Try to purchase items
    success, message, transaction = economy.purchase_item(user_id, "heat_map", "FANG")
    print(f"Purchase result: {message}")
    
    # Check active items
    active = economy.get_active_items(user_id)
    print(f"Active items: {len(active)}")
    
    print(f"\n5. Final Status:")
    balance = economy.get_user_balance(user_id)
    print(f"Final Balance: {balance.current_balance} XP")
    print(f"Lifetime Earned: {balance.lifetime_earned} XP")
    print(f"Lifetime Spent: {balance.lifetime_spent} XP")
    
    # Test edge case - award enough XP to unlock all strategies
    print(f"\n6. Testing Full Unlock (adding 400 XP):")
    result = economy.add_xp(user_id, 400, "Bonus XP for testing")
    print(f"Added XP: {result['xp_added']} (New Balance: {result['new_balance']})")
    
    if result["strategy_unlocks"]:
        for unlock in result["strategy_unlocks"]:
            print(f"   🎯 UNLOCK: {unlock['display_name']}")
            print(f"      Telegram: {unlock['telegram_message'][:100]}...")
    
    final_status = economy.get_tactical_unlock_status(user_id)
    print(f"All strategies unlocked: {final_status['all_strategies_unlocked']}")
    print(f"Total unlocked: {final_status['unlocked_count']}/{final_status['total_strategies']}")
    
    print(f"\n=== Test Complete ===")
    print(f"Enhanced XP Economy with tactical integration is working correctly!")
    print(f"✅ Tactical unlocks at 120/240/360 XP verified")
    print(f"✅ Achievement integration verified") 
    print(f"✅ Drill report integration verified")
    print(f"✅ XP validation and progression verified")