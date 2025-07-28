"""
BITTEN Gear System - Tactical Equipment Management
Handles gear inventory, loadouts, crafting, and trading
"""

import json
import sqlite3
import time
import random
import hashlib
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)

class GearRarity(Enum):
    """Gear rarity tiers with Call of Duty style colors"""
    COMMON = ("Common", "gray", 1.0)  # Gray
    UNCOMMON = ("Uncommon", "green", 1.5)  # Green  
    RARE = ("Rare", "blue", 2.0)  # Blue
    EPIC = ("Epic", "purple", 3.0)  # Purple
    LEGENDARY = ("Legendary", "orange", 5.0)  # Orange
    MYTHIC = ("Mythic", "red", 10.0)  # Red
    
    def __init__(self, display_name: str, color: str, value_multiplier: float):
        self.display_name = display_name
        self.color = color
        self.value_multiplier = value_multiplier
    
    @property
    def drop_weight(self) -> int:
        """Weight for drop calculations (higher = more common)"""
        weights = {
            GearRarity.COMMON: 1000,
            GearRarity.UNCOMMON: 400,
            GearRarity.RARE: 150,
            GearRarity.EPIC: 40,
            GearRarity.LEGENDARY: 9,
            GearRarity.MYTHIC: 1
        }
        return weights.get(self, 0)

class GearType(Enum):
    """Types of tactical gear"""
    INDICATOR = "Indicator"  # Technical analysis tools
    STRATEGY = "Strategy"  # Trading strategies
    BOOST = "Boost"  # Performance enhancers
    CONSUMABLE = "Consumable"  # One-time use items
    ATTACHMENT = "Attachment"  # Gear modifications
    CAMO = "Camo"  # Visual customization

class GearSlot(Enum):
    """Equipment slots in loadout"""
    PRIMARY_INDICATOR = "Primary Indicator"
    SECONDARY_INDICATOR = "Secondary Indicator"
    STRATEGY = "Strategy"
    TACTICAL = "Tactical"
    LETHAL = "Lethal"
    FIELD_UPGRADE = "Field Upgrade"
    PERK_1 = "Perk 1"
    PERK_2 = "Perk 2"
    PERK_3 = "Perk 3"

@dataclass
class GearStats:
    """Statistical bonuses provided by gear"""
    accuracy_bonus: float = 0.0  # Win rate improvement
    range_bonus: float = 0.0  # Analysis depth
    fire_rate_bonus: float = 0.0  # Signal frequency
    damage_bonus: float = 0.0  # Profit multiplier
    mobility_bonus: float = 0.0  # Execution speed
    control_bonus: float = 0.0  # Risk management
    
    # Special stats
    xp_multiplier: float = 1.0
    reward_multiplier: float = 1.0
    cooldown_reduction: float = 0.0
    critical_chance: float = 0.0
    
    def __add__(self, other: 'GearStats') -> 'GearStats':
        """Combine gear stats"""
        return GearStats(
            accuracy_bonus=self.accuracy_bonus + other.accuracy_bonus,
            range_bonus=self.range_bonus + other.range_bonus,
            fire_rate_bonus=self.fire_rate_bonus + other.fire_rate_bonus,
            damage_bonus=self.damage_bonus + other.damage_bonus,
            mobility_bonus=self.mobility_bonus + other.mobility_bonus,
            control_bonus=self.control_bonus + other.control_bonus,
            xp_multiplier=self.xp_multiplier * other.xp_multiplier,
            reward_multiplier=self.reward_multiplier * other.reward_multiplier,
            cooldown_reduction=min(0.75, self.cooldown_reduction + other.cooldown_reduction),
            critical_chance=min(0.5, self.critical_chance + other.critical_chance)
        )

@dataclass
class GearItem:
    """Individual gear item"""
    item_id: str
    name: str
    gear_type: GearType
    rarity: GearRarity
    level: int
    stats: GearStats
    description: str
    icon: str
    slot: Optional[GearSlot] = None
    
    # Crafting and trading
    salvage_value: int = 0
    craft_materials: Dict[str, int] = field(default_factory=dict)
    tradeable: bool = True
    
    # Special properties
    set_name: Optional[str] = None  # Part of a gear set
    special_effects: List[str] = field(default_factory=list)
    unlock_requirement: Optional[str] = None
    
    # Consumable properties
    uses_remaining: Optional[int] = None
    duration_seconds: Optional[int] = None
    
    def __post_init__(self):
        """Calculate derived values"""
        if self.salvage_value == 0:
            base_value = 100 * self.rarity.value_multiplier
            self.salvage_value = int(base_value * (1 + self.level * 0.1))
    
    def get_display_name(self) -> str:
        """Get formatted display name with rarity color"""
        color_codes = {
            "gray": "⬜",
            "green": "🟩",
            "blue": "🟦",
            "purple": "🟪",
            "orange": "🟧",
            "red": "🟥"
        }
        return f"{color_codes.get(self.rarity.color, '')} {self.name}"
    
    def get_power_score(self) -> int:
        """Calculate item power score"""
        stat_sum = (
            self.stats.accuracy_bonus * 100 +
            self.stats.range_bonus * 100 +
            self.stats.fire_rate_bonus * 100 +
            self.stats.damage_bonus * 100 +
            self.stats.mobility_bonus * 100 +
            self.stats.control_bonus * 100
        )
        
        multiplier_bonus = (
            (self.stats.xp_multiplier - 1) * 200 +
            (self.stats.reward_multiplier - 1) * 300
        )
        
        rarity_bonus = self.rarity.value_multiplier * 50
        level_bonus = self.level * 10
        
        return int(stat_sum + multiplier_bonus + rarity_bonus + level_bonus)

@dataclass
class Loadout:
    """Player's equipped gear loadout"""
    loadout_id: str
    name: str
    slots: Dict[GearSlot, Optional[str]] = field(default_factory=dict)
    created_at: int = field(default_factory=lambda: int(time.time()))
    last_modified: int = field(default_factory=lambda: int(time.time()))
    is_active: bool = False
    
    def get_total_stats(self, gear_items: Dict[str, GearItem]) -> GearStats:
        """Calculate combined stats from all equipped gear"""
        total_stats = GearStats()
        
        for slot, item_id in self.slots.items():
            if item_id and item_id in gear_items:
                total_stats = total_stats + gear_items[item_id].stats
        
        return total_stats
    
    def get_power_score(self, gear_items: Dict[str, GearItem]) -> int:
        """Calculate total loadout power score"""
        total_score = 0
        
        for slot, item_id in self.slots.items():
            if item_id and item_id in gear_items:
                total_score += gear_items[item_id].get_power_score()
        
        return total_score

@dataclass
class CraftingRecipe:
    """Recipe for crafting gear"""
    recipe_id: str
    result_item_id: str
    required_materials: Dict[str, int]  # item_id -> quantity
    required_level: int
    crafting_time: int  # seconds
    success_rate: float = 1.0
    
    def can_craft(self, inventory: Dict[str, int], user_level: int) -> Tuple[bool, str]:
        """Check if user can craft this item"""
        if user_level < self.required_level:
            return False, f"Requires level {self.required_level}"
        
        for material_id, required_qty in self.required_materials.items():
            if inventory.get(material_id, 0) < required_qty:
                return False, f"Insufficient materials"
        
        return True, "Ready to craft"

@dataclass
class TradeOffer:
    """Gear trading offer between players"""
    trade_id: str
    sender_id: int
    receiver_id: int
    offered_items: List[str]  # item_ids
    requested_items: List[str]  # item_ids
    offered_xp: int = 0
    requested_xp: int = 0
    status: str = "pending"  # pending, accepted, rejected, expired
    created_at: int = field(default_factory=lambda: int(time.time()))
    expires_at: int = field(default_factory=lambda: int(time.time()) + 86400)  # 24 hours
    
    def is_expired(self) -> bool:
        """Check if trade offer has expired"""
        return time.time() > self.expires_at

class GearSystem:
    """Main gear system manager"""
    
    # Gear catalog - predefined items
    GEAR_CATALOG = {
        # Indicators
        "rsi_scanner_basic": GearItem(
            item_id="rsi_scanner_basic",
            name="RSI Scanner",
            gear_type=GearType.INDICATOR,
            rarity=GearRarity.COMMON,
            level=1,
            stats=GearStats(accuracy_bonus=0.05, range_bonus=0.10),
            description="Basic RSI oversold/overbought scanner",
            icon="📊",
            slot=GearSlot.PRIMARY_INDICATOR
        ),
        "macd_elite": GearItem(
            item_id="macd_elite",
            name="MACD Elite",
            gear_type=GearType.INDICATOR,
            rarity=GearRarity.RARE,
            level=10,
            stats=GearStats(accuracy_bonus=0.15, fire_rate_bonus=0.20),
            description="Advanced MACD crossover detection system",
            icon="📈",
            slot=GearSlot.PRIMARY_INDICATOR
        ),
        "volume_analyzer_pro": GearItem(
            item_id="volume_analyzer_pro",
            name="Volume Analyzer Pro",
            gear_type=GearType.INDICATOR,
            rarity=GearRarity.EPIC,
            level=20,
            stats=GearStats(range_bonus=0.25, control_bonus=0.20),
            description="Professional volume profile analysis",
            icon="📊",
            slot=GearSlot.SECONDARY_INDICATOR
        ),
        
        # Strategies
        "scalper_basic": GearItem(
            item_id="scalper_basic",
            name="Scalper's Toolkit",
            gear_type=GearType.STRATEGY,
            rarity=GearRarity.UNCOMMON,
            level=5,
            stats=GearStats(fire_rate_bonus=0.30, mobility_bonus=0.25),
            description="Quick in-and-out trading strategy",
            icon="⚡",
            slot=GearSlot.STRATEGY
        ),
        "swing_master": GearItem(
            item_id="swing_master",
            name="Swing Master Protocol",
            gear_type=GearType.STRATEGY,
            rarity=GearRarity.LEGENDARY,
            level=30,
            stats=GearStats(damage_bonus=0.40, accuracy_bonus=0.30),
            description="Elite swing trading system with AI predictions",
            icon="🎯",
            slot=GearSlot.STRATEGY
        ),
        
        # Boosts
        "xp_boost_2x": GearItem(
            item_id="xp_boost_2x",
            name="Double XP Token",
            gear_type=GearType.BOOST,
            rarity=GearRarity.RARE,
            level=1,
            stats=GearStats(xp_multiplier=2.0),
            description="Double XP gains for 1 hour",
            icon="⭐",
            slot=GearSlot.TACTICAL,
            duration_seconds=3600
        ),
        "profit_shield": GearItem(
            item_id="profit_shield",
            name="Profit Shield",
            gear_type=GearType.BOOST,
            rarity=GearRarity.EPIC,
            level=15,
            stats=GearStats(control_bonus=0.50),
            description="Reduces losses by 50% for next 5 trades",
            icon="🛡️",
            slot=GearSlot.TACTICAL,
            uses_remaining=5
        ),
        
        # Consumables
        "emergency_stop": GearItem(
            item_id="emergency_stop",
            name="Emergency Stop",
            gear_type=GearType.CONSUMABLE,
            rarity=GearRarity.UNCOMMON,
            level=1,
            stats=GearStats(),
            description="Instantly close all positions",
            icon="🚨",
            uses_remaining=1,
            tradeable=False
        ),
        "instant_analysis": GearItem(
            item_id="instant_analysis",
            name="Instant Analysis",
            gear_type=GearType.CONSUMABLE,
            rarity=GearRarity.RARE,
            level=10,
            stats=GearStats(),
            description="Get AI analysis of current market conditions",
            icon="🤖",
            uses_remaining=1
        ),
        
        # Legendary/Mythic items
        "quantum_predictor": GearItem(
            item_id="quantum_predictor",
            name="Quantum Market Predictor",
            gear_type=GearType.INDICATOR,
            rarity=GearRarity.MYTHIC,
            level=50,
            stats=GearStats(
                accuracy_bonus=0.50,
                range_bonus=0.40,
                critical_chance=0.25,
                xp_multiplier=1.5
            ),
            description="Mythic-tier quantum computing market predictor",
            icon="🌟",
            slot=GearSlot.PRIMARY_INDICATOR,
            special_effects=["Quantum Entanglement: 25% chance to predict exact price"],
            unlock_requirement="prestige_5"
        )
    }
    
    # Crafting recipes
    CRAFTING_RECIPES = {
        "craft_macd_elite": CraftingRecipe(
            recipe_id="craft_macd_elite",
            result_item_id="macd_elite",
            required_materials={
                "rsi_scanner_basic": 3,
                "craft_material_rare": 5
            },
            required_level=10,
            crafting_time=300  # 5 minutes
        )
    }
    
    # Gear sets with bonuses
    GEAR_SETS = {
        "sniper_elite": {
            "name": "Elite Sniper Set",
            "items": ["macd_elite", "volume_analyzer_pro", "swing_master"],
            "bonuses": {
                2: GearStats(accuracy_bonus=0.10, critical_chance=0.05),
                3: GearStats(accuracy_bonus=0.20, critical_chance=0.15, damage_bonus=0.25)
            }
        }
    }
    
    def __init__(self, db_path: str = "bitten_gear.db"):
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self):
        """Initialize gear database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # User inventory table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_inventory (
                user_id INTEGER,
                item_id TEXT,
                item_data TEXT,
                quantity INTEGER DEFAULT 1,
                acquired_at INTEGER,
                PRIMARY KEY (user_id, item_id)
            )
        ''')
        
        # User loadouts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_loadouts (
                user_id INTEGER,
                loadout_id TEXT,
                loadout_data TEXT,
                PRIMARY KEY (user_id, loadout_id)
            )
        ''')
        
        # Crafting queue table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crafting_queue (
                craft_id TEXT PRIMARY KEY,
                user_id INTEGER,
                recipe_id TEXT,
                start_time INTEGER,
                completion_time INTEGER,
                status TEXT DEFAULT 'crafting'
            )
        ''')
        
        # Trade offers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trade_offers (
                trade_id TEXT PRIMARY KEY,
                trade_data TEXT,
                created_at INTEGER,
                status TEXT DEFAULT 'pending'
            )
        ''')
        
        # Gear drop history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drop_history (
                drop_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item_id TEXT,
                rarity TEXT,
                source TEXT,
                dropped_at INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_user_inventory(self, user_id: int) -> Dict[str, GearItem]:
        """Get user's gear inventory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT item_id, item_data, quantity 
            FROM user_inventory 
            WHERE user_id = ?
        ''', (user_id,))
        
        inventory = {}
        for row in cursor.fetchall():
            item_id, item_data, quantity = row
            
            # Try to load from catalog first
            if item_id in self.GEAR_CATALOG:
                item = self.GEAR_CATALOG[item_id]
            else:
                # Load custom item from JSON
                item_dict = json.loads(item_data)
                item = self._dict_to_gear_item(item_dict)
            
            inventory[item_id] = item
        
        conn.close()
        return inventory
    
    def add_item_to_inventory(
        self, 
        user_id: int, 
        item: Union[str, GearItem], 
        quantity: int = 1,
        source: str = "unknown"
    ) -> bool:
        """Add item to user's inventory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Handle item reference
        if isinstance(item, str):
            if item not in self.GEAR_CATALOG:
                return False
            gear_item = self.GEAR_CATALOG[item]
            item_id = item
        else:
            gear_item = item
            item_id = item.item_id
        
        # Serialize item data
        item_data = json.dumps(self._gear_item_to_dict(gear_item))
        
        # Add to inventory
        cursor.execute('''
            INSERT INTO user_inventory (user_id, item_id, item_data, quantity, acquired_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, item_id) DO UPDATE SET
                quantity = quantity + ?,
                item_data = ?
        ''', (user_id, item_id, item_data, quantity, int(time.time()), 
              quantity, item_data))
        
        # Log drop history
        cursor.execute('''
            INSERT INTO drop_history (user_id, item_id, rarity, source, dropped_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, item_id, gear_item.rarity.name, source, int(time.time())))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Added {quantity}x {item_id} to user {user_id}'s inventory")
        return True
    
    def create_loadout(
        self, 
        user_id: int, 
        name: str, 
        set_active: bool = False
    ) -> Optional[Loadout]:
        """Create a new loadout for user"""
        loadout_id = hashlib.md5(f"{user_id}_{name}_{time.time()}".encode()).hexdigest()[:12]
        
        loadout = Loadout(
            loadout_id=loadout_id,
            name=name,
            is_active=set_active
        )
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Deactivate other loadouts if setting active
        if set_active:
            cursor.execute('''
                UPDATE user_loadouts 
                SET loadout_data = json_set(loadout_data, '$.is_active', 0)
                WHERE user_id = ?
            ''', (user_id,))
        
        # Save new loadout
        cursor.execute('''
            INSERT INTO user_loadouts (user_id, loadout_id, loadout_data)
            VALUES (?, ?, ?)
        ''', (user_id, loadout_id, json.dumps(asdict(loadout))))
        
        conn.commit()
        conn.close()
        
        return loadout
    
    def equip_item(
        self, 
        user_id: int, 
        item_id: str, 
        loadout_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Equip item to loadout slot"""
        # Get user inventory
        inventory = self.get_user_inventory(user_id)
        if item_id not in inventory:
            return False, "Item not in inventory"
        
        item = inventory[item_id]
        if not item.slot:
            return False, "Item cannot be equipped"
        
        # Get active loadout if not specified
        if not loadout_id:
            loadout = self.get_active_loadout(user_id)
            if not loadout:
                # Create default loadout
                loadout = self.create_loadout(user_id, "Default", set_active=True)
            loadout_id = loadout.loadout_id
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update loadout
        cursor.execute('''
            UPDATE user_loadouts 
            SET loadout_data = json_set(loadout_data, '$.slots."' || ? || '"', ?)
            WHERE user_id = ? AND loadout_id = ?
        ''', (item.slot.value, item_id, user_id, loadout_id))
        
        conn.commit()
        conn.close()
        
        return True, f"Equipped {item.get_display_name()} to {item.slot.value}"
    
    def get_active_loadout(self, user_id: int) -> Optional[Loadout]:
        """Get user's active loadout"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT loadout_data 
            FROM user_loadouts 
            WHERE user_id = ? AND json_extract(loadout_data, '$.is_active') = 1
        ''', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            data = json.loads(row[0])
            return Loadout(**data)
        
        return None
    
    def get_user_loadouts(self, user_id: int) -> List[Loadout]:
        """Get all user loadouts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT loadout_data 
            FROM user_loadouts 
            WHERE user_id = ?
            ORDER BY json_extract(loadout_data, '$.created_at') DESC
        ''', (user_id,))
        
        loadouts = []
        for row in cursor.fetchall():
            data = json.loads(row[0])
            loadouts.append(Loadout(**data))
        
        conn.close()
        return loadouts
    
    def generate_random_drop(
        self, 
        user_level: int, 
        luck_multiplier: float = 1.0,
        guaranteed_rarity: Optional[GearRarity] = None
    ) -> GearItem:
        """Generate random gear drop based on level and luck"""
        # Calculate rarity weights
        weights = []
        rarities = []
        
        for rarity in GearRarity:
            # Higher level increases chance of better drops
            level_bonus = user_level * 0.5 if rarity.value_multiplier > 2 else 0
            
            # Apply luck multiplier to rare+ items
            luck_bonus = luck_multiplier if rarity.value_multiplier > 2 else 1.0
            
            weight = rarity.drop_weight + level_bonus
            weight *= luck_bonus
            
            weights.append(weight)
            rarities.append(rarity)
        
        # Select rarity
        if guaranteed_rarity:
            selected_rarity = guaranteed_rarity
        else:
            selected_rarity = random.choices(rarities, weights=weights)[0]
        
        # Select item type
        item_type = random.choice(list(GearType))
        
        # Generate item
        item_id = f"drop_{int(time.time())}_{random.randint(1000, 9999)}"
        
        # Generate stats based on rarity and level
        stat_multiplier = selected_rarity.value_multiplier * (1 + user_level * 0.02)
        
        stats = GearStats(
            accuracy_bonus=random.uniform(0, 0.1) * stat_multiplier if random.random() > 0.5 else 0,
            range_bonus=random.uniform(0, 0.1) * stat_multiplier if random.random() > 0.5 else 0,
            fire_rate_bonus=random.uniform(0, 0.1) * stat_multiplier if random.random() > 0.5 else 0,
            damage_bonus=random.uniform(0, 0.1) * stat_multiplier if random.random() > 0.5 else 0,
            mobility_bonus=random.uniform(0, 0.1) * stat_multiplier if random.random() > 0.5 else 0,
            control_bonus=random.uniform(0, 0.1) * stat_multiplier if random.random() > 0.5 else 0,
            xp_multiplier=1.0 + (random.uniform(0, 0.2) * stat_multiplier if selected_rarity.value_multiplier > 3 else 0),
            reward_multiplier=1.0 + (random.uniform(0, 0.2) * stat_multiplier if selected_rarity.value_multiplier > 3 else 0),
            cooldown_reduction=random.uniform(0, 0.1) * stat_multiplier if selected_rarity.value_multiplier > 2 else 0,
            critical_chance=random.uniform(0, 0.05) * stat_multiplier if selected_rarity.value_multiplier > 2 else 0
        )
        
        # Generate name
        prefixes = {
            GearRarity.COMMON: ["Basic", "Standard", "Regular"],
            GearRarity.UNCOMMON: ["Enhanced", "Improved", "Advanced"],
            GearRarity.RARE: ["Superior", "Elite", "Precision"],
            GearRarity.EPIC: ["Master", "Legendary", "Ultimate"],
            GearRarity.LEGENDARY: ["Apex", "Divine", "Mythical"],
            GearRarity.MYTHIC: ["Quantum", "Cosmic", "Transcendent"]
        }
        
        suffixes = {
            GearType.INDICATOR: ["Scanner", "Analyzer", "Detector"],
            GearType.STRATEGY: ["Protocol", "System", "Method"],
            GearType.BOOST: ["Enhancer", "Amplifier", "Accelerator"],
            GearType.CONSUMABLE: ["Kit", "Pack", "Module"],
            GearType.ATTACHMENT: ["Mod", "Upgrade", "Enhancement"],
            GearType.CAMO: ["Pattern", "Skin", "Coating"]
        }
        
        prefix = random.choice(prefixes.get(selected_rarity, ["Unknown"]))
        suffix = random.choice(suffixes.get(item_type, ["Item"]))
        name = f"{prefix} {suffix}"
        
        # Assign slot based on type
        slot_mappings = {
            GearType.INDICATOR: [GearSlot.PRIMARY_INDICATOR, GearSlot.SECONDARY_INDICATOR],
            GearType.STRATEGY: [GearSlot.STRATEGY],
            GearType.BOOST: [GearSlot.TACTICAL, GearSlot.FIELD_UPGRADE],
            GearType.CONSUMABLE: [GearSlot.LETHAL, GearSlot.TACTICAL],
            GearType.ATTACHMENT: None,
            GearType.CAMO: None
        }
        
        available_slots = slot_mappings.get(item_type, [])
        slot = random.choice(available_slots) if available_slots else None
        
        # Create item
        item = GearItem(
            item_id=item_id,
            name=name,
            gear_type=item_type,
            rarity=selected_rarity,
            level=max(1, min(user_level + random.randint(-5, 10), 100)),
            stats=stats,
            description=f"A {selected_rarity.display_name.lower()} {item_type.value.lower()} dropped from combat",
            icon=self._get_item_icon(item_type),
            slot=slot
        )
        
        return item
    
    def craft_item(
        self, 
        user_id: int, 
        recipe_id: str
    ) -> Tuple[bool, str, Optional[str]]:
        """Start crafting an item"""
        if recipe_id not in self.CRAFTING_RECIPES:
            return False, "Unknown recipe", None
        
        recipe = self.CRAFTING_RECIPES[recipe_id]
        
        # Check requirements
        inventory = self.get_user_inventory(user_id)
        inventory_counts = defaultdict(int)
        for item_id in inventory:
            inventory_counts[item_id] += 1
        
        # Simplified level check (would need user profile integration)
        user_level = 50  # Placeholder
        
        can_craft, reason = recipe.can_craft(inventory_counts, user_level)
        if not can_craft:
            return False, reason, None
        
        # Start crafting
        craft_id = hashlib.md5(f"{user_id}_{recipe_id}_{time.time()}".encode()).hexdigest()[:12]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Remove materials from inventory
        for material_id, qty in recipe.required_materials.items():
            cursor.execute('''
                UPDATE user_inventory 
                SET quantity = quantity - ?
                WHERE user_id = ? AND item_id = ?
            ''', (qty, user_id, material_id))
            
            # Remove if quantity is 0
            cursor.execute('''
                DELETE FROM user_inventory 
                WHERE user_id = ? AND item_id = ? AND quantity <= 0
            ''', (user_id, material_id))
        
        # Add to crafting queue
        cursor.execute('''
            INSERT INTO crafting_queue (craft_id, user_id, recipe_id, start_time, completion_time)
            VALUES (?, ?, ?, ?, ?)
        ''', (craft_id, user_id, recipe_id, int(time.time()), 
              int(time.time()) + recipe.crafting_time))
        
        conn.commit()
        conn.close()
        
        return True, f"Started crafting {recipe.result_item_id}", craft_id
    
    def check_crafting_completion(self, user_id: int) -> List[Dict[str, Any]]:
        """Check and complete any finished crafting"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        current_time = int(time.time())
        
        # Find completed crafts
        cursor.execute('''
            SELECT craft_id, recipe_id 
            FROM crafting_queue 
            WHERE user_id = ? AND completion_time <= ? AND status = 'crafting'
        ''', (user_id, current_time))
        
        completed = []
        for craft_id, recipe_id in cursor.fetchall():
            recipe = self.CRAFTING_RECIPES[recipe_id]
            
            # Check success
            if random.random() <= recipe.success_rate:
                # Add crafted item
                self.add_item_to_inventory(
                    user_id, 
                    recipe.result_item_id, 
                    source="crafting"
                )
                
                completed.append({
                    'craft_id': craft_id,
                    'success': True,
                    'item_id': recipe.result_item_id
                })
            else:
                completed.append({
                    'craft_id': craft_id,
                    'success': False,
                    'item_id': recipe.result_item_id
                })
            
            # Update status
            cursor.execute('''
                UPDATE crafting_queue 
                SET status = ? 
                WHERE craft_id = ?
            ''', ('completed' if completed[-1]['success'] else 'failed', craft_id))
        
        conn.commit()
        conn.close()
        
        return completed
    
    def create_trade_offer(
        self,
        sender_id: int,
        receiver_id: int,
        offered_items: List[str],
        requested_items: List[str],
        offered_xp: int = 0,
        requested_xp: int = 0
    ) -> Tuple[bool, str, Optional[TradeOffer]]:
        """Create a trade offer between players"""
        # Validate sender has offered items
        sender_inventory = self.get_user_inventory(sender_id)
        for item_id in offered_items:
            if item_id not in sender_inventory:
                return False, f"You don't have {item_id}", None
            if not sender_inventory[item_id].tradeable:
                return False, f"{item_id} is not tradeable", None
        
        # Create trade offer
        trade_id = hashlib.md5(
            f"{sender_id}_{receiver_id}_{time.time()}".encode()
        ).hexdigest()[:12]
        
        trade = TradeOffer(
            trade_id=trade_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            offered_items=offered_items,
            requested_items=requested_items,
            offered_xp=offered_xp,
            requested_xp=requested_xp
        )
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO trade_offers (trade_id, trade_data, created_at, status)
            VALUES (?, ?, ?, ?)
        ''', (trade_id, json.dumps(asdict(trade)), trade.created_at, trade.status))
        
        conn.commit()
        conn.close()
        
        return True, "Trade offer created", trade
    
    def accept_trade(self, trade_id: str, user_id: int) -> Tuple[bool, str]:
        """Accept a trade offer"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get trade offer
        cursor.execute('''
            SELECT trade_data 
            FROM trade_offers 
            WHERE trade_id = ? AND status = 'pending'
        ''', (trade_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, "Trade not found or already processed"
        
        trade_data = json.loads(row[0])
        trade = TradeOffer(**trade_data)
        
        # Verify user is receiver
        if trade.receiver_id != user_id:
            conn.close()
            return False, "You cannot accept this trade"
        
        # Check if expired
        if trade.is_expired():
            cursor.execute('''
                UPDATE trade_offers 
                SET status = 'expired' 
                WHERE trade_id = ?
            ''', (trade_id,))
            conn.commit()
            conn.close()
            return False, "Trade has expired"
        
        # Validate both parties have required items
        sender_inv = self.get_user_inventory(trade.sender_id)
        receiver_inv = self.get_user_inventory(trade.receiver_id)
        
        # Check sender items
        for item_id in trade.offered_items:
            if item_id not in sender_inv:
                conn.close()
                return False, "Sender no longer has offered items"
        
        # Check receiver items
        for item_id in trade.requested_items:
            if item_id not in receiver_inv:
                conn.close()
                return False, "You don't have requested items"
        
        # Execute trade
        # Transfer items from sender to receiver
        for item_id in trade.offered_items:
            cursor.execute('''
                DELETE FROM user_inventory 
                WHERE user_id = ? AND item_id = ?
            ''', (trade.sender_id, item_id))
            
            self.add_item_to_inventory(trade.receiver_id, sender_inv[item_id], source="trade")
        
        # Transfer items from receiver to sender
        for item_id in trade.requested_items:
            cursor.execute('''
                DELETE FROM user_inventory 
                WHERE user_id = ? AND item_id = ?
            ''', (trade.receiver_id, item_id))
            
            self.add_item_to_inventory(trade.sender_id, receiver_inv[item_id], source="trade")
        
        # Update trade status
        cursor.execute('''
            UPDATE trade_offers 
            SET status = 'accepted' 
            WHERE trade_id = ?
        ''', (trade_id,))
        
        conn.commit()
        conn.close()
        
        return True, "Trade completed successfully"
    
    def salvage_item(self, user_id: int, item_id: str) -> Tuple[bool, str, int]:
        """Salvage item for materials"""
        inventory = self.get_user_inventory(user_id)
        
        if item_id not in inventory:
            return False, "Item not in inventory", 0
        
        item = inventory[item_id]
        salvage_value = item.salvage_value
        
        # Remove item from inventory
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM user_inventory 
            WHERE user_id = ? AND item_id = ?
        ''', (user_id, item_id))
        
        # Add crafting materials based on rarity
        material_rewards = {
            GearRarity.COMMON: [("craft_material_common", 1)],
            GearRarity.UNCOMMON: [("craft_material_common", 2), ("craft_material_uncommon", 1)],
            GearRarity.RARE: [("craft_material_uncommon", 2), ("craft_material_rare", 1)],
            GearRarity.EPIC: [("craft_material_rare", 2), ("craft_material_epic", 1)],
            GearRarity.LEGENDARY: [("craft_material_epic", 2), ("craft_material_legendary", 1)],
            GearRarity.MYTHIC: [("craft_material_legendary", 2), ("craft_material_mythic", 1)]
        }
        
        materials = material_rewards.get(item.rarity, [])
        for material_id, quantity in materials:
            # Create material item if needed
            material = GearItem(
                item_id=material_id,
                name=material_id.replace("_", " ").title(),
                gear_type=GearType.CONSUMABLE,
                rarity=GearRarity.COMMON,
                level=1,
                stats=GearStats(),
                description="Crafting material",
                icon="🔧"
            )
            self.add_item_to_inventory(user_id, material, quantity, source="salvage")
        
        conn.commit()
        conn.close()
        
        return True, f"Salvaged {item.get_display_name()} for {salvage_value} materials", salvage_value
    
    def get_gear_set_bonus(self, user_id: int, loadout: Loadout) -> Optional[GearStats]:
        """Calculate gear set bonuses for equipped items"""
        inventory = self.get_user_inventory(user_id)
        equipped_items = []
        
        # Get all equipped items
        for slot, item_id in loadout.slots.items():
            if item_id and item_id in inventory:
                equipped_items.append(item_id)
        
        # Check each gear set
        total_bonus = GearStats()
        
        for set_id, set_info in self.GEAR_SETS.items():
            set_items = set_info["items"]
            equipped_count = sum(1 for item in set_items if item in equipped_items)
            
            # Apply set bonuses
            for required_count, bonus_stats in set_info["bonuses"].items():
                if equipped_count >= required_count:
                    total_bonus = total_bonus + bonus_stats
        
        return total_bonus if total_bonus.accuracy_bonus > 0 else None
    
    def get_inventory_display(self, user_id: int) -> Dict[str, Any]:
        """Get formatted inventory display for user"""
        inventory = self.get_user_inventory(user_id)
        loadouts = self.get_user_loadouts(user_id)
        active_loadout = self.get_active_loadout(user_id)
        
        # Organize by type and rarity
        organized = defaultdict(lambda: defaultdict(list))
        
        for item_id, item in inventory.items():
            organized[item.gear_type][item.rarity].append(item)
        
        # Calculate inventory stats
        total_power = sum(item.get_power_score() for item in inventory.values())
        rarity_counts = defaultdict(int)
        for item in inventory.values():
            rarity_counts[item.rarity] += 1
        
        # Get loadout stats
        loadout_stats = None
        set_bonus = None
        if active_loadout:
            loadout_stats = active_loadout.get_total_stats(inventory)
            set_bonus = self.get_gear_set_bonus(user_id, active_loadout)
        
        return {
            'total_items': len(inventory),
            'total_power': total_power,
            'rarity_breakdown': dict(rarity_counts),
            'items_by_type': dict(organized),
            'loadouts': loadouts,
            'active_loadout': active_loadout,
            'loadout_stats': loadout_stats,
            'set_bonus': set_bonus,
            'inventory_space': {
                'used': len(inventory),
                'max': 500  # Could be upgraded
            }
        }
    
    def _get_item_icon(self, gear_type: GearType) -> str:
        """Get icon for gear type"""
        icons = {
            GearType.INDICATOR: "📊",
            GearType.STRATEGY: "🎯",
            GearType.BOOST: "⚡",
            GearType.CONSUMABLE: "💊",
            GearType.ATTACHMENT: "🔧",
            GearType.CAMO: "🎨"
        }
        return icons.get(gear_type, "📦")
    
    def _gear_item_to_dict(self, item: GearItem) -> Dict[str, Any]:
        """Convert GearItem to dictionary for storage"""
        return {
            'item_id': item.item_id,
            'name': item.name,
            'gear_type': item.gear_type.value,
            'rarity': item.rarity.name,
            'level': item.level,
            'stats': asdict(item.stats),
            'description': item.description,
            'icon': item.icon,
            'slot': item.slot.value if item.slot else None,
            'salvage_value': item.salvage_value,
            'craft_materials': item.craft_materials,
            'tradeable': item.tradeable,
            'set_name': item.set_name,
            'special_effects': item.special_effects,
            'unlock_requirement': item.unlock_requirement,
            'uses_remaining': item.uses_remaining,
            'duration_seconds': item.duration_seconds
        }
    
    def _dict_to_gear_item(self, data: Dict[str, Any]) -> GearItem:
        """Convert dictionary to GearItem"""
        return GearItem(
            item_id=data['item_id'],
            name=data['name'],
            gear_type=GearType(data['gear_type']),
            rarity=GearRarity[data['rarity']],
            level=data['level'],
            stats=GearStats(**data['stats']),
            description=data['description'],
            icon=data['icon'],
            slot=GearSlot(data['slot']) if data.get('slot') else None,
            salvage_value=data.get('salvage_value', 0),
            craft_materials=data.get('craft_materials', {}),
            tradeable=data.get('tradeable', True),
            set_name=data.get('set_name'),
            special_effects=data.get('special_effects', []),
            unlock_requirement=data.get('unlock_requirement'),
            uses_remaining=data.get('uses_remaining'),
            duration_seconds=data.get('duration_seconds')
        )

# Achievement integration hooks
def award_gear_for_achievement(
    gear_system: GearSystem,
    user_id: int,
    achievement_id: str,
    achievement_tier: str
) -> Optional[GearItem]:
    """Award gear when achievement is unlocked"""
    # Map achievement tiers to gear rarities
    tier_to_rarity = {
        "bronze": GearRarity.UNCOMMON,
        "silver": GearRarity.RARE,
        "gold": GearRarity.EPIC,
        "platinum": GearRarity.LEGENDARY,
        "diamond": GearRarity.LEGENDARY,
        "master": GearRarity.MYTHIC
    }
    
    guaranteed_rarity = tier_to_rarity.get(achievement_tier.lower())
    
    # Generate special achievement drop
    item = gear_system.generate_random_drop(
        user_level=1,  # Would need actual level
        luck_multiplier=2.0,  # Achievement drops are luckier
        guaranteed_rarity=guaranteed_rarity
    )
    
    # Add achievement tag
    item.description = f"Awarded for unlocking {achievement_id}"
    
    # Add to inventory
    gear_system.add_item_to_inventory(
        user_id,
        item,
        source=f"achievement_{achievement_id}"
    )
    
    return item

# Milestone integration
def award_gear_for_milestone(
    gear_system: GearSystem,
    user_id: int,
    milestone_type: str,
    milestone_value: int
) -> Optional[GearItem]:
    """Award gear for reaching milestones"""
    # Special milestone rewards
    milestone_rewards = {
        "total_trades_100": "scalper_basic",
        "total_trades_1000": "swing_master",
        "profit_10000": "profit_shield",
        "xp_50000": "xp_boost_2x"
    }
    
    milestone_key = f"{milestone_type}_{milestone_value}"
    
    if milestone_key in milestone_rewards:
        item_id = milestone_rewards[milestone_key]
        gear_system.add_item_to_inventory(
            user_id,
            item_id,
            source=f"milestone_{milestone_key}"
        )
        return gear_system.GEAR_CATALOG.get(item_id)
    
    # Generate random reward for other milestones
    return award_gear_for_achievement(
        gear_system,
        user_id,
        f"milestone_{milestone_type}",
        "gold"  # Milestones give good rewards
    )