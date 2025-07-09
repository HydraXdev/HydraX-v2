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
    tier_required: str  # NIBBLER, FANG, COMMANDER, APEX
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
    
    def __init__(self, data_dir: str = "data/xp_economy"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Define shop catalog
        self.shop_catalog = self._initialize_shop_catalog()
        
        # User balances cache
        self.user_balances: Dict[str, UserXPBalance] = {}
        
        # Load existing data
        self._load_user_data()
    
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
            tier_required="APEX"
        )
        
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
    
    def add_xp(self, user_id: str, amount: int, reason: str = "") -> UserXPBalance:
        """Add XP to user's balance"""
        balance = self.get_user_balance(user_id)
        
        balance.current_balance += amount
        balance.lifetime_earned += amount
        
        # Log transaction
        transaction = XPTransaction(
            transaction_id=f"{user_id}_{datetime.now().timestamp()}",
            user_id=user_id,
            item_id="xp_earned",
            purchase_type=PurchaseType.HEAT_MAP,  # Placeholder
            amount=amount,
            balance_before=balance.current_balance - amount,
            balance_after=balance.current_balance,
            status=PurchaseStatus.COMPLETED,
            timestamp=datetime.now(),
            metadata={"reason": reason}
        )
        
        balance.purchase_history.append(transaction)
        self._save_user_balance(balance)
        
        logger.info(f"Added {amount} XP to user {user_id}. New balance: {balance.current_balance}")
        return balance
    
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
        tier_hierarchy = ["NIBBLER", "FANG", "COMMANDER", "APEX"]
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


# Example usage
if __name__ == "__main__":
    economy = XPEconomy()
    
    # Add XP to user
    user_id = "test_user_123"
    economy.add_xp(user_id, 10000, "Trade wins")
    
    # Try to purchase
    success, message, transaction = economy.purchase_item(user_id, "heat_map", "FANG")
    print(f"Purchase result: {message}")
    
    # Check active items
    active = economy.get_active_items(user_id)
    print(f"Active items: {active}")
    
    # Check balance
    balance = economy.get_user_balance(user_id)
    print(f"Current balance: {balance.current_balance} XP")