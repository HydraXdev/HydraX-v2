"""
XP Shop Interface for BITTEN
Handles shop display, categorization, and purchase flows
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging

from .xp_economy import XPEconomy, XPItem, PurchaseType

logger = logging.getLogger(__name__)

class ShopCategory(Enum):
    """Shop item categories"""
    TACTICAL_INTEL = "Tactical Intel"
    ELITE_PROTOCOLS = "Elite Protocols"
    AMMUNITION = "Ammunition Upgrades"
    SPECIAL = "Special Items"

@dataclass
class ShopDisplay:
    """Display format for shop items"""
    category: ShopCategory
    items: List[Dict[str, Any]]
    category_icon: str
    category_description: str

class XPShop:
    """XP Shop manager with categorized display"""
    
    # Category mappings
    CATEGORY_MAP = {
        ShopCategory.TACTICAL_INTEL: [
            PurchaseType.HEAT_MAP,
            PurchaseType.SQUAD_RADAR,
            PurchaseType.CONFIDENCE_BOOST
        ],
        ShopCategory.ELITE_PROTOCOLS: [
            PurchaseType.TRAILING_GUARD,
            PurchaseType.SPLIT_COMMAND,
            PurchaseType.STEALTH_ENTRY,
            PurchaseType.FORTRESS_MODE
        ],
        ShopCategory.AMMUNITION: [
            PurchaseType.EXTENDED_MAG,
            PurchaseType.RAPID_RELOAD,
            PurchaseType.SPECIAL_AMMO
        ]
    }
    
    # Category display info
    CATEGORY_INFO = {
        ShopCategory.TACTICAL_INTEL: {
            "icon": "📊",
            "description": "Information advantages and market intelligence"
        },
        ShopCategory.ELITE_PROTOCOLS: {
            "icon": "🎯",
            "description": "Advanced trading strategies and automation"
        },
        ShopCategory.AMMUNITION: {
            "icon": "🔫",
            "description": "Extra shots and enhanced firepower"
        },
        ShopCategory.SPECIAL: {
            "icon": "⭐",
            "description": "Special offers and limited items"
        }
    }
    
    def __init__(self, xp_economy: XPEconomy):
        self.economy = xp_economy
        self.special_offers: Dict[str, Dict[str, Any]] = {}
    
    def get_shop_display(
        self, 
        user_id: str, 
        user_tier: str,
        filter_affordable: bool = False
    ) -> List[ShopDisplay]:
        """Get categorized shop display for user"""
        balance = self.economy.get_user_balance(user_id)
        active_items = {item["item_id"] for item in self.economy.get_active_items(user_id)}
        
        shop_displays = []
        
        for category, purchase_types in self.CATEGORY_MAP.items():
            category_items = []
            
            for purchase_type in purchase_types:
                # Find items of this type
                for item_id, item in self.economy.shop_catalog.items():
                    if item.purchase_type != purchase_type:
                        continue
                    
                    # Skip if filtering and not affordable
                    if filter_affordable and item.cost > balance.current_balance:
                        continue
                    
                    # Check if user can see this item (tier requirement)
                    tier_hierarchy = ["NIBBLER", "FANG", "COMMANDER"]
                    user_tier_index = tier_hierarchy.index(user_tier)
                    item_tier_index = tier_hierarchy.index(item.tier_required)
                    
                    # Prepare item display
                    item_display = {
                        "item_id": item.item_id,
                        "name": item.name,
                        "description": item.description,
                        "cost": item.cost,
                        "tier_required": item.tier_required,
                        "is_locked": user_tier_index < item_tier_index,
                        "is_owned": item_id in active_items,
                        "can_afford": balance.current_balance >= item.cost,
                        "type": self._get_item_type(item),
                        "duration": f"{item.duration_hours}h" if item.duration_hours else None,
                        "uses": item.max_uses,
                        "cooldown": f"{item.cooldown_hours}h" if item.cooldown_hours else None
                    }
                    
                    # Add purchase availability
                    can_buy, reason = self.economy.can_purchase(user_id, item_id, user_tier)
                    item_display["can_purchase"] = can_buy
                    item_display["purchase_reason"] = reason if not can_buy else None
                    
                    # Add unlock progress for locked items
                    if item_display["is_locked"]:
                        item_display["unlock_progress"] = self._get_unlock_progress(
                            user_tier_index, 
                            item_tier_index
                        )
                    
                    category_items.append(item_display)
            
            if category_items:
                info = self.CATEGORY_INFO[category]
                shop_displays.append(ShopDisplay(
                    category=category,
                    items=category_items,
                    category_icon=info["icon"],
                    category_description=info["description"]
                ))
        
        # Add special offers if any
        special_items = self._get_special_offers(user_id, user_tier)
        if special_items:
            shop_displays.append(ShopDisplay(
                category=ShopCategory.SPECIAL,
                items=special_items,
                category_icon=self.CATEGORY_INFO[ShopCategory.SPECIAL]["icon"],
                category_description=self.CATEGORY_INFO[ShopCategory.SPECIAL]["description"]
            ))
        
        return shop_displays
    
    def get_item_details(self, item_id: str, user_id: str, user_tier: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a shop item"""
        if item_id not in self.economy.shop_catalog:
            return None
        
        item = self.economy.shop_catalog[item_id]
        balance = self.economy.get_user_balance(user_id)
        
        # Get purchase history for this item
        purchase_count = sum(
            1 for trans in balance.purchase_history 
            if trans.item_id == item_id and trans.status.value == "completed"
        )
        
        # Get last purchase time
        last_purchase = self.economy._get_last_purchase_time(user_id, item_id)
        
        details = {
            "item": {
                "id": item.item_id,
                "name": item.name,
                "description": item.description,
                "cost": item.cost,
                "tier_required": item.tier_required,
                "type": self._get_item_type(item)
            },
            "user_status": {
                "current_balance": balance.current_balance,
                "can_afford": balance.current_balance >= item.cost,
                "purchase_count": purchase_count,
                "last_purchased": last_purchase.isoformat() if last_purchase else None
            },
            "requirements": self._format_requirements(item.requirements),
            "benefits": self._get_item_benefits(item),
            "warnings": self._get_item_warnings(item)
        }
        
        # Add purchase availability
        can_buy, reason = self.economy.can_purchase(user_id, item_id, user_tier)
        details["purchase"] = {
            "can_purchase": can_buy,
            "reason": reason if not can_buy else "Ready to purchase"
        }
        
        return details
    
    def create_special_offer(
        self,
        offer_id: str,
        item_id: str,
        discount_percent: int,
        valid_hours: int,
        eligible_users: Optional[List[str]] = None,
        min_tier: str = "NIBBLER"
    ) -> None:
        """Create a limited-time special offer"""
        if item_id not in self.economy.shop_catalog:
            raise ValueError(f"Item {item_id} not found in catalog")
        
        item = self.economy.shop_catalog[item_id]
        discounted_price = int(item.cost * (1 - discount_percent / 100))
        
        self.special_offers[offer_id] = {
            "item_id": item_id,
            "original_price": item.cost,
            "discounted_price": discounted_price,
            "discount_percent": discount_percent,
            "expires_at": datetime.now() + timedelta(hours=valid_hours),
            "eligible_users": eligible_users,
            "min_tier": min_tier
        }
        
        logger.info(f"Created special offer {offer_id}: {item.name} at {discount_percent}% off")
    
    def _get_item_type(self, item: XPItem) -> str:
        """Get display type for an item"""
        if item.is_permanent():
            return "Permanent Unlock"
        elif item.duration_hours:
            return "Temporary Boost"
        elif item.max_uses:
            return "Consumable"
        else:
            return "Special"
    
    def _get_unlock_progress(self, current_tier: int, required_tier: int) -> Dict[str, Any]:
        """Get unlock progress information"""
        tiers_needed = required_tier - current_tier
        tier_names = ["NIBBLER", "FANG", "COMMANDER"]
        
        return {
            "tiers_to_unlock": tiers_needed,
            "next_tier": tier_names[current_tier + 1] if current_tier < 3 else None,
            "required_tier": tier_names[required_tier]
        }
    
    def _format_requirements(self, requirements: Dict[str, Any]) -> List[str]:
        """Format requirements for display"""
        formatted = []
        
        if "min_trades" in requirements:
            formatted.append(f"📊 Minimum {requirements['min_trades']} trades")
        
        if "win_rate" in requirements:
            formatted.append(f"🎯 Win rate ≥ {requirements['win_rate']*100:.0f}%")
        
        if "avg_rr" in requirements:
            formatted.append(f"💰 Average R:R ≥ {requirements['avg_rr']:.1f}")
        
        return formatted
    
    def _get_item_benefits(self, item: XPItem) -> List[str]:
        """Get formatted benefits for an item"""
        benefits = []
        
        if item.purchase_type == PurchaseType.TRAILING_GUARD:
            benefits.extend([
                "✅ Automatically protects profits",
                "✅ No manual intervention needed",
                "✅ Works 24/7 on all trades"
            ])
        elif item.purchase_type == PurchaseType.SPLIT_COMMAND:
            benefits.extend([
                "✅ Lock in profits early",
                "✅ Let winners run further",
                "✅ Reduces emotional decisions"
            ])
        elif item.purchase_type == PurchaseType.EXTENDED_MAG:
            benefits.extend([
                "✅ More trading opportunities",
                "✅ Only on high-confidence signals",
                "✅ Maintains safety standards"
            ])
        # Add more benefits for other items...
        
        return benefits
    
    def _get_item_warnings(self, item: XPItem) -> List[str]:
        """Get any warnings for an item"""
        warnings = []
        
        if item.max_uses:
            warnings.append(f"⚠️ Single use only")
        
        if item.duration_hours:
            warnings.append(f"⚠️ Expires after {item.duration_hours} hours")
        
        if item.cooldown_hours:
            warnings.append(f"⚠️ {item.cooldown_hours}h cooldown between purchases")
        
        return warnings
    
    def _get_special_offers(self, user_id: str, user_tier: str) -> List[Dict[str, Any]]:
        """Get active special offers for user"""
        special_items = []
        tier_hierarchy = ["NIBBLER", "FANG", "COMMANDER"]
        user_tier_index = tier_hierarchy.index(user_tier)
        
        for offer_id, offer in self.special_offers.items():
            # Check if expired
            if datetime.now() > offer["expires_at"]:
                continue
            
            # Check tier requirement
            min_tier_index = tier_hierarchy.index(offer["min_tier"])
            if user_tier_index < min_tier_index:
                continue
            
            # Check if user is eligible
            if offer["eligible_users"] and user_id not in offer["eligible_users"]:
                continue
            
            # Get item details
            item = self.economy.shop_catalog[offer["item_id"]]
            
            special_items.append({
                "item_id": offer["item_id"],
                "offer_id": offer_id,
                "name": f"🎁 {item.name} (LIMITED TIME)",
                "description": f"{item.description} - {offer['discount_percent']}% OFF!",
                "cost": offer["discounted_price"],
                "original_cost": offer["original_price"],
                "discount_percent": offer["discount_percent"],
                "expires_in": self._format_time_remaining(offer["expires_at"]),
                "type": "Limited Offer",
                "can_afford": self.economy.get_user_balance(user_id).current_balance >= offer["discounted_price"]
            })
        
        return special_items
    
    def _format_time_remaining(self, expires_at: datetime) -> str:
        """Format time remaining for display"""
        remaining = expires_at - datetime.now()
        hours = int(remaining.total_seconds() / 3600)
        minutes = int((remaining.total_seconds() % 3600) / 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

# Example usage
if __name__ == "__main__":
    from xp_economy import XPEconomy
    
    economy = XPEconomy()
    shop = XPShop(economy)
    
    # Get shop display for a user
    user_id = "test_user"
    economy.add_xp(user_id, 15000, "Initial balance")
    
    display = shop.get_shop_display(user_id, "COMMANDER")
    
    for category_display in display:
        print(f"\n{category_display.category_icon} {category_display.category.value}")
        print(f"  {category_display.category_description}")
        print("  " + "-" * 50)
        
        for item in category_display.items:
            status = "🔒" if item["is_locked"] else ("✅" if item["is_owned"] else "💰")
            print(f"  {status} {item['name']} - {item['cost']} XP")
            print(f"     {item['description']}")
    
    # Create a special offer
    shop.create_special_offer(
        offer_id="weekend_special",
        item_id="heat_map",
        discount_percent=50,
        valid_hours=48
    )