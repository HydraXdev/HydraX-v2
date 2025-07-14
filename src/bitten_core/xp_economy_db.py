"""
XP Economy System with Database Integration for BITTEN
Handles XP spending, validation, and transaction logging with PostgreSQL
"""

import asyncio
from typing import Dict, Optional, Tuple, List, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.xp_database import XPDatabase, XPBalance, XPTransaction

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
class UserXPBalanceDB:
    """User's XP balance wrapper for database integration"""
    user_id: str
    current_balance: int
    lifetime_earned: int
    lifetime_spent: int
    prestige_level: int = 0
    active_purchases: List[str] = field(default_factory=list)
    last_purchase: Optional[datetime] = None
    
    @classmethod
    def from_db_balance(cls, balance: XPBalance, user_id_str: str) -> 'UserXPBalanceDB':
        """Create from database balance object"""
        return cls(
            user_id=user_id_str,
            current_balance=balance.current_balance,
            lifetime_earned=balance.lifetime_earned,
            lifetime_spent=balance.lifetime_spent,
            prestige_level=balance.prestige_level,
            active_purchases=[],  # Loaded separately
            last_purchase=balance.last_updated
        )


class XPEconomyDB:
    """Main XP economy manager with database integration"""
    
    def __init__(self):
        """Initialize the XP economy with database backend"""
        self.xp_db: Optional[XPDatabase] = None
        self.items: Dict[str, XPItem] = {}
        self.users: Dict[str, UserXPBalanceDB] = {}  # Cache for compatibility
        self._init_task = None
        
        # Initialize shop items
        self._initialize_shop_items()
    
    async def initialize(self):
        """Initialize database connection"""
        try:
            self.xp_db = XPDatabase()
            await self.xp_db.initialize()
            await self.xp_db.initialize_tables()
            logger.info("XP Economy database initialized")
        except Exception as e:
            logger.error(f"Failed to initialize XP Economy database: {e}")
            raise
    
    async def _ensure_initialized(self):
        """Ensure database is initialized"""
        if not self.xp_db:
            await self.initialize()
    
    def _initialize_shop_items(self):
        """Initialize available shop items"""
        # Tactical Intel (30-min boosts)
        self.items["heat_map"] = XPItem(
            item_id="heat_map",
            name="Heat Map Intel",
            description="See where the action is for 30 minutes",
            cost=500,
            purchase_type=PurchaseType.HEAT_MAP,
            tier_required="NIBBLER",
            duration_hours=0.5
        )
        
        self.items["squad_radar"] = XPItem(
            item_id="squad_radar",
            name="Squad Radar",
            description="Track your squad's performance for 30 minutes",
            cost=750,
            purchase_type=PurchaseType.SQUAD_RADAR,
            tier_required="NIBBLER",
            duration_hours=0.5
        )
        
        self.items["confidence_boost"] = XPItem(
            item_id="confidence_boost",
            name="Confidence Boost",
            description="1.5x XP multiplier for 30 minutes",
            cost=1000,
            purchase_type=PurchaseType.CONFIDENCE_BOOST,
            tier_required="FANG",
            duration_hours=0.5
        )
        
        # Elite Protocols (permanent unlocks)
        self.items["trailing_guard"] = XPItem(
            item_id="trailing_guard",
            name="Trailing Guard Protocol",
            description="Automatic stop-loss trailing on all trades",
            cost=5000,
            purchase_type=PurchaseType.TRAILING_GUARD,
            tier_required="FANG"
        )
        
        self.items["split_command"] = XPItem(
            item_id="split_command",
            name="Split Command Protocol",
            description="Execute multi-position strategies",
            cost=7500,
            purchase_type=PurchaseType.SPLIT_COMMAND,
            tier_required="COMMANDER"
        )
        
        self.items["stealth_entry"] = XPItem(
            item_id="stealth_entry",
            name="Stealth Entry Protocol",
            description="Hidden order execution",
            cost=10000,
            purchase_type=PurchaseType.STEALTH_ENTRY,
            tier_required="COMMANDER"
        )
        
        self.items["fortress_mode"] = XPItem(
            item_id="fortress_mode",
            name="Fortress Mode Protocol",
            description="Ultimate risk management suite",
            cost=15000,
            purchase_type=PurchaseType.FORTRESS_MODE,
            tier_required="APEX"
        )
        
        # Ammunition (consumables)
        self.items["extended_mag"] = XPItem(
            item_id="extended_mag",
            name="Extended Magazine",
            description="5 extra signal slots for 24 hours",
            cost=2000,
            purchase_type=PurchaseType.EXTENDED_MAG,
            tier_required="NIBBLER",
            duration_hours=24
        )
        
        self.items["rapid_reload"] = XPItem(
            item_id="rapid_reload",
            name="Rapid Reload",
            description="Instant position reset (3 uses)",
            cost=3000,
            purchase_type=PurchaseType.RAPID_RELOAD,
            tier_required="FANG",
            max_uses=3
        )
        
        self.items["special_ammo"] = XPItem(
            item_id="special_ammo",
            name="Special Ammunition",
            description="Enhanced signal accuracy for 1 hour",
            cost=1500,
            purchase_type=PurchaseType.SPECIAL_AMMO,
            tier_required="FANG",
            duration_hours=1
        )
    
    async def get_user_balance(self, user_id: str) -> UserXPBalanceDB:
        """Get user's XP balance from database"""
        await self._ensure_initialized()
        
        try:
            user_id_int = int(user_id)
            balance = await self.xp_db.get_user_balance(user_id_int)
            
            if not balance:
                # Create new balance
                balance = await self.xp_db.create_user_balance(user_id_int, 0)
            
            # Convert to UserXPBalanceDB and cache
            user_balance = UserXPBalanceDB.from_db_balance(balance, user_id)
            self.users[user_id] = user_balance
            
            return user_balance
            
        except Exception as e:
            logger.error(f"Failed to get user balance: {e}")
            # Return cached version if available
            if user_id in self.users:
                return self.users[user_id]
            # Return empty balance
            return UserXPBalanceDB(
                user_id=user_id,
                current_balance=0,
                lifetime_earned=0,
                lifetime_spent=0
            )
    
    async def add_xp(self, user_id: str, amount: int, source: str = "unknown",
                     metadata: Optional[Dict[str, Any]] = None) -> UserXPBalanceDB:
        """Add XP to user balance"""
        await self._ensure_initialized()
        
        try:
            user_id_int = int(user_id)
            balance, transaction = await self.xp_db.add_xp(
                user_id_int, amount, f"XP earned from {source}", metadata
            )
            
            # Update cache
            user_balance = UserXPBalanceDB.from_db_balance(balance, user_id)
            self.users[user_id] = user_balance
            
            logger.info(f"Added {amount} XP to user {user_id} from {source}")
            return user_balance
            
        except Exception as e:
            logger.error(f"Failed to add XP: {e}")
            raise
    
    async def spend_xp(self, user_id: str, amount: int, item_name: str,
                       metadata: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
        """Spend XP from user balance"""
        await self._ensure_initialized()
        
        try:
            user_id_int = int(user_id)
            balance, transaction = await self.xp_db.spend_xp(
                user_id_int, amount, f"Purchased: {item_name}", metadata
            )
            
            # Update cache
            user_balance = UserXPBalanceDB.from_db_balance(balance, user_id)
            self.users[user_id] = user_balance
            
            logger.info(f"User {user_id} spent {amount} XP on {item_name}")
            return True, "Purchase successful"
            
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            logger.error(f"Failed to spend XP: {e}")
            return False, "Transaction failed"
    
    async def purchase_item(self, user_id: str, item_id: str,
                           user_tier: str = "NIBBLER") -> Tuple[bool, str]:
        """Purchase an item from the shop"""
        if item_id not in self.items:
            return False, "Item not found"
        
        item = self.items[item_id]
        
        # Check tier requirement
        tier_levels = ["NIBBLER", "FANG", "COMMANDER", "APEX"]
        if tier_levels.index(user_tier) < tier_levels.index(item.tier_required):
            return False, f"Requires {item.tier_required} tier or higher"
        
        # Check balance and make purchase
        user_balance = await self.get_user_balance(user_id)
        
        if user_balance.current_balance < item.cost:
            return False, f"Insufficient XP. Need {item.cost}, have {user_balance.current_balance}"
        
        # Process the purchase
        success, message = await self.spend_xp(
            user_id,
            item.cost,
            item.name,
            {
                "item_id": item_id,
                "purchase_type": item.purchase_type.value,
                "tier": user_tier
            }
        )
        
        if success:
            # Track active purchase (would need separate table for this)
            user_balance.active_purchases.append(item_id)
            user_balance.last_purchase = datetime.now()
            
            return True, f"Successfully purchased {item.name}!"
        
        return False, message
    
    def get_shop_items(self, user_tier: str = "NIBBLER") -> List[Dict[str, Any]]:
        """Get available shop items for user's tier"""
        tier_levels = ["NIBBLER", "FANG", "COMMANDER", "APEX"]
        user_tier_level = tier_levels.index(user_tier)
        
        available_items = []
        for item in self.items.values():
            required_level = tier_levels.index(item.tier_required)
            
            item_data = {
                "id": item.item_id,
                "name": item.name,
                "description": item.description,
                "cost": item.cost,
                "type": item.purchase_type.value,
                "available": user_tier_level >= required_level,
                "tier_required": item.tier_required,
                "is_permanent": item.is_permanent()
            }
            
            if item.duration_hours:
                item_data["duration"] = f"{item.duration_hours} hours"
            if item.max_uses:
                item_data["uses"] = item.max_uses
                
            available_items.append(item_data)
        
        return sorted(available_items, key=lambda x: (not x["available"], x["cost"]))
    
    def get_active_items(self, user_id: str) -> List[str]:
        """Get user's active purchased items"""
        if user_id in self.users:
            return self.users[user_id].active_purchases
        return []
    
    # Compatibility methods for file-based system
    
    def _save_user_data(self, user_id: str):
        """Compatibility method - data is already saved in database"""
        pass
    
    async def migrate_from_file_system(self, old_economy):
        """Migrate data from file-based XPEconomy to database"""
        await self._ensure_initialized()
        
        migrated_count = 0
        for user_id, old_balance in old_economy.users.items():
            try:
                user_id_int = int(user_id)
                
                # Create balance in database
                balance = await self.xp_db.create_user_balance(
                    user_id_int,
                    old_balance.current_balance
                )
                
                # Add transaction for migration
                await self.xp_db.add_xp(
                    user_id_int,
                    0,  # No actual XP added, just recording
                    "Migrated from file system",
                    {
                        "lifetime_earned": old_balance.lifetime_earned,
                        "lifetime_spent": old_balance.lifetime_spent,
                        "migration_date": datetime.now().isoformat()
                    }
                )
                
                migrated_count += 1
                logger.info(f"Migrated user {user_id} with {old_balance.current_balance} XP")
                
            except Exception as e:
                logger.error(f"Failed to migrate user {user_id}: {e}")
        
        logger.info(f"Migration complete. Migrated {migrated_count} users")
    
    async def cleanup(self):
        """Clean up database connections"""
        if self.xp_db:
            await self.xp_db.close()


# Helper functions for backward compatibility

async def create_xp_economy_db() -> XPEconomyDB:
    """Create and initialize XP economy with database"""
    economy = XPEconomyDB()
    await economy.initialize()
    return economy


if __name__ == "__main__":
    async def test_xp_economy():
        """Test XP economy functionality"""
        print("Testing XP Economy with database...")
        
        economy = await create_xp_economy_db()
        
        try:
            # Test user ID
            test_user = "12345"
            
            # Add some XP
            print(f"\nAdding 5000 XP to user {test_user}...")
            balance = await economy.add_xp(test_user, 5000, "test_bonus")
            print(f"✓ Balance: {balance.current_balance} XP")
            
            # Get shop items
            print("\nAvailable shop items:")
            items = economy.get_shop_items("FANG")
            for item in items[:3]:
                print(f"  - {item['name']}: {item['cost']} XP")
            
            # Make a purchase
            print(f"\nPurchasing Heat Map Intel...")
            success, message = await economy.purchase_item(test_user, "heat_map", "FANG")
            print(f"✓ {message}")
            
            # Check new balance
            balance = await economy.get_user_balance(test_user)
            print(f"✓ New balance: {balance.current_balance} XP")
            
            print("\n✅ XP Economy database test complete!")
            
        finally:
            await economy.cleanup()
    
    # Run the test
    asyncio.run(test_xp_economy())