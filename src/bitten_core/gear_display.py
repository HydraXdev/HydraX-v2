"""
Gear Display Components
Visual formatting and display utilities for gear inventory
"""

from typing import Dict, List, Optional, Tuple, Any
from PIL import Image, ImageDraw, ImageFont
import io
import base64
from dataclasses import dataclass

from .gear_system import GearItem, GearRarity, GearType, GearStats, Loadout

class GearVisualizer:
    """Creates visual representations of gear and inventory"""
    
    # Color schemes for rarities
    RARITY_COLORS = {
        GearRarity.COMMON: (128, 128, 128),  # Gray
        GearRarity.UNCOMMON: (0, 255, 0),  # Green
        GearRarity.RARE: (0, 112, 255),  # Blue
        GearRarity.EPIC: (163, 53, 238),  # Purple
        GearRarity.LEGENDARY: (255, 128, 0),  # Orange
        GearRarity.MYTHIC: (255, 0, 0),  # Red
    }
    
    # Stat icons
    STAT_ICONS = {
        'accuracy': '🎯',
        'damage': '💥',
        'fire_rate': '⚡',
        'range': '📡',
        'mobility': '🏃',
        'control': '🛡️',
        'xp': '⭐',
        'reward': '💰',
        'cooldown': '⏱️',
        'critical': '🎲'
    }
    
    @staticmethod
    def format_gear_card(item: GearItem) -> str:
        """Format a single gear item as a text card"""
        # Header with rarity color
        rarity_emoji = {
            GearRarity.COMMON: "⬜",
            GearRarity.UNCOMMON: "🟩",
            GearRarity.RARE: "🟦",
            GearRarity.EPIC: "🟪",
            GearRarity.LEGENDARY: "🟧",
            GearRarity.MYTHIC: "🟥"
        }
        
        card = f"{rarity_emoji.get(item.rarity, '⬜')} **{item.name}**\n"
        card += f"*{item.rarity.display_name} {item.gear_type.value}*\n"
        card += f"Level {item.level} | Power: {item.get_power_score()}\n"
        card += "─" * 25 + "\n"
        
        # Description
        card += f"_{item.description}_\n\n"
        
        # Stats
        if any([
            item.stats.accuracy_bonus,
            item.stats.damage_bonus,
            item.stats.fire_rate_bonus,
            item.stats.range_bonus,
            item.stats.mobility_bonus,
            item.stats.control_bonus
        ]):
            card += "**Stats:**\n"
            
            if item.stats.accuracy_bonus > 0:
                card += f"🎯 Accuracy: +{item.stats.accuracy_bonus*100:.1f}%\n"
            if item.stats.damage_bonus > 0:
                card += f"💥 Damage: +{item.stats.damage_bonus*100:.1f}%\n"
            if item.stats.fire_rate_bonus > 0:
                card += f"⚡ Fire Rate: +{item.stats.fire_rate_bonus*100:.1f}%\n"
            if item.stats.range_bonus > 0:
                card += f"📡 Range: +{item.stats.range_bonus*100:.1f}%\n"
            if item.stats.mobility_bonus > 0:
                card += f"🏃 Mobility: +{item.stats.mobility_bonus*100:.1f}%\n"
            if item.stats.control_bonus > 0:
                card += f"🛡️ Control: +{item.stats.control_bonus*100:.1f}%\n"
            
            card += "\n"
        
        # Special stats
        if item.stats.xp_multiplier > 1.0:
            card += f"⭐ XP Multiplier: {item.stats.xp_multiplier:.1f}x\n"
        if item.stats.reward_multiplier > 1.0:
            card += f"💰 Reward Multiplier: {item.stats.reward_multiplier:.1f}x\n"
        if item.stats.cooldown_reduction > 0:
            card += f"⏱️ Cooldown Reduction: -{item.stats.cooldown_reduction*100:.0f}%\n"
        if item.stats.critical_chance > 0:
            card += f"🎲 Critical Chance: +{item.stats.critical_chance*100:.0f}%\n"
        
        # Special effects
        if item.special_effects:
            card += "\n**Special Effects:**\n"
            for effect in item.special_effects:
                card += f"✨ {effect}\n"
        
        # Set info
        if item.set_name:
            card += f"\n🔗 Part of _{item.set_name}_ set\n"
        
        # Trade/salvage info
        card += "\n" + "─" * 25 + "\n"
        if not item.tradeable:
            card += "🔒 Soulbound (Cannot Trade)\n"
        card += f"♻️ Salvage Value: {item.salvage_value} materials\n"
        
        return card
    
    @staticmethod
    def format_loadout_display(
        loadout: Loadout, 
        gear_items: Dict[str, GearItem],
        set_bonus: Optional[GearStats] = None
    ) -> str:
        """Format loadout display with equipped items"""
        display = f"⚔️ **{loadout.name}**\n"
        display += f"Power Score: {loadout.get_power_score(gear_items):}\n"
        display += "━" * 30 + "\n\n"
        
        # Show equipped items by slot
        for slot in GearSlot:
            item_id = loadout.slots.get(slot)
            if item_id and item_id in gear_items:
                item = gear_items[item_id]
                display += f"**{slot.value}:**\n"
                display += f"  {item.get_display_name()} (PWR: {item.get_power_score()})\n"
            else:
                display += f"**{slot.value}:** _Empty_\n"
        
        # Total stats
        display += "\n**Combined Stats:**\n"
        total_stats = loadout.get_total_stats(gear_items)
        
        stat_lines = []
        if total_stats.accuracy_bonus > 0:
            stat_lines.append(f"🎯 +{total_stats.accuracy_bonus*100:.1f}% Accuracy")
        if total_stats.damage_bonus > 0:
            stat_lines.append(f"💥 +{total_stats.damage_bonus*100:.1f}% Damage")
        if total_stats.fire_rate_bonus > 0:
            stat_lines.append(f"⚡ +{total_stats.fire_rate_bonus*100:.1f}% Fire Rate")
        if total_stats.xp_multiplier > 1.0:
            stat_lines.append(f"⭐ {total_stats.xp_multiplier:.1f}x XP")
        
        for line in stat_lines:
            display += f"  {line}\n"
        
        # Set bonus
        if set_bonus:
            display += "\n🔥 **SET BONUS ACTIVE** 🔥\n"
            if set_bonus.accuracy_bonus > 0:
                display += f"  +{set_bonus.accuracy_bonus*100:.0f}% Accuracy\n"
            if set_bonus.damage_bonus > 0:
                display += f"  +{set_bonus.damage_bonus*100:.0f}% Damage\n"
            if set_bonus.critical_chance > 0:
                display += f"  +{set_bonus.critical_chance*100:.0f}% Crit Chance\n"
        
        return display
    
    @staticmethod
    def format_inventory_grid(
        inventory: Dict[str, GearItem],
        max_items: int = 20
    ) -> str:
        """Format inventory as a compact grid"""
        if not inventory:
            return "_Your inventory is empty_"
        
        # Group by type and rarity
        grouped = {}
        for item_id, item in inventory.items():
            key = (item.gear_type, item.rarity)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(item)
        
        # Sort groups
        sorted_groups = sorted(
            grouped.items(),
            key=lambda x: (-x[0][1].value_multiplier, x[0][0].value)
        )
        
        grid = "**📦 INVENTORY GRID 📦**\n"
        grid += "```\n"
        
        items_shown = 0
        for (gear_type, rarity), items in sorted_groups:
            if items_shown >= max_items:
                remaining = sum(len(group_items) for _, group_items in sorted_groups) - items_shown
                grid += f"\n... and {remaining} more items\n"
                break
            
            # Type header
            grid += f"\n{gear_type.value.upper()} ({rarity.display_name}):\n"
            
            # Items in this group
            for item in items[:5]:  # Max 5 per group
                if items_shown >= max_items:
                    break
                
                # Compact display
                power_str = f"[{item.get_power_score():>4}]"
                level_str = f"Lv{item.level:>2}"
                name = item.name[:20].ljust(20)
                
                grid += f"  {power_str} {level_str} {name}\n"
                items_shown += 1
            
            if len(items) > 5:
                grid += f"  ... +{len(items)-5} more {gear_type.value}\n"
        
        grid += "```"
        
        return grid
    
    @staticmethod
    def format_drop_notification(item: GearItem, source: str = "Unknown") -> str:
        """Format gear drop notification"""
        rarity_effects = {
            GearRarity.COMMON: "",
            GearRarity.UNCOMMON: "✨",
            GearRarity.RARE: "✨✨",
            GearRarity.EPIC: "✨✨✨",
            GearRarity.LEGENDARY: "🌟🌟🌟🌟",
            GearRarity.MYTHIC: "🌟🌟🌟🌟🌟"
        }
        
        effects = rarity_effects.get(item.rarity, "")
        
        notification = f"{effects} **GEAR DROP!** {effects}\n\n"
        notification += f"You received: {item.get_display_name()}\n"
        notification += f"Type: {item.gear_type.value}\n"
        notification += f"Power: {item.get_power_score()}\n"
        notification += f"Source: {source}\n"
        
        # Add flavor text based on rarity
        if item.rarity == GearRarity.MYTHIC:
            notification += "\n_🎊 MYTHIC ITEM! This is extraordinarily rare! 🎊_"
        elif item.rarity == GearRarity.LEGENDARY:
            notification += "\n_⚡ Legendary gear acquired! Outstanding! ⚡_"
        elif item.rarity == GearRarity.EPIC:
            notification += "\n_💜 Epic find! This will serve you well! 💜_"
        
        return notification
    
    @staticmethod
    def format_comparison(item1: GearItem, item2: GearItem) -> str:
        """Compare two gear items side by side"""
        comparison = "**📊 GEAR COMPARISON 📊**\n\n"
        
        # Headers
        comparison += f"**Current:** {item1.get_display_name()}\n"
        comparison += f"**vs**\n"
        comparison += f"**New:** {item2.get_display_name()}\n"
        comparison += "─" * 30 + "\n\n"
        
        # Power comparison
        power_diff = item2.get_power_score() - item1.get_power_score()
        power_symbol = "🔺" if power_diff > 0 else "🔻" if power_diff < 0 else "➖"
        comparison += f"**Power:** {item1.get_power_score()} → {item2.get_power_score()} "
        comparison += f"{power_symbol} ({power_diff:+d})\n\n"
        
        # Stat comparison
        stats_to_compare = [
            ('accuracy_bonus', '🎯 Accuracy', 100),
            ('damage_bonus', '💥 Damage', 100),
            ('fire_rate_bonus', '⚡ Fire Rate', 100),
            ('xp_multiplier', '⭐ XP Multi', 1),
            ('reward_multiplier', '💰 Reward Multi', 1)
        ]
        
        for stat_name, display_name, multiplier in stats_to_compare:
            val1 = getattr(item1.stats, stat_name)
            val2 = getattr(item2.stats, stat_name)
            
            if val1 != 0 or val2 != 0:
                diff = (val2 - val1) * multiplier
                symbol = "🔺" if diff > 0 else "🔻" if diff < 0 else "➖"
                
                if multiplier == 100:  # Percentage stats
                    comparison += f"{display_name}: {val1*100:.1f}% → {val2*100:.1f}% "
                else:  # Multiplier stats
                    comparison += f"{display_name}: {val1:.1f}x → {val2:.1f}x "
                
                comparison += f"{symbol} ({diff:+.1f})\n"
        
        # Special effects comparison
        if item1.special_effects or item2.special_effects:
            comparison += "\n**Special Effects:**\n"
            
            effects1 = set(item1.special_effects)
            effects2 = set(item2.special_effects)
            
            # Lost effects
            for effect in effects1 - effects2:
                comparison += f"❌ -{effect}\n"
            
            # Gained effects
            for effect in effects2 - effects1:
                comparison += f"✅ +{effect}\n"
            
            # Kept effects
            for effect in effects1 & effects2:
                comparison += f"➖ {effect}\n"
        
        return comparison
    
    @staticmethod
    def create_inventory_image(
        inventory: Dict[str, GearItem],
        title: str = "TACTICAL INVENTORY"
    ) -> bytes:
        """Create a visual inventory image (returns PNG bytes)"""
        # Image dimensions
        width = 800
        height = 600
        cell_size = 80
        padding = 10
        
        # Create image
        img = Image.new('RGB', (width, height), color=(20, 20, 20))
        draw = ImageDraw.Draw(img)
        
        # Try to load font (fallback to default if not available)
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            item_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except:
            title_font = ImageFont.load_default()
            item_font = ImageFont.load_default()
        
        # Draw title
        draw.text((width//2, 20), title, fill=(255, 255, 255), 
                 font=title_font, anchor="mt")
        
        # Sort inventory by rarity and power
        sorted_items = sorted(
            inventory.values(),
            key=lambda x: (x.rarity.value_multiplier, x.get_power_score()),
            reverse=True
        )
        
        # Draw grid
        start_x = padding
        start_y = 60
        cols = (width - 2 * padding) // (cell_size + padding)
        
        for idx, item in enumerate(sorted_items[:35]):  # Max 35 items shown
            row = idx // cols
            col = idx % cols
            
            x = start_x + col * (cell_size + padding)
            y = start_y + row * (cell_size + padding)
            
            # Get rarity color
            color = GearVisualizer.RARITY_COLORS.get(item.rarity, (128, 128, 128))
            
            # Draw cell border
            draw.rectangle(
                [x, y, x + cell_size, y + cell_size],
                outline=color,
                width=3
            )
            
            # Draw item icon (simplified)
            icon_map = {
                GearType.INDICATOR: "📊",
                GearType.STRATEGY: "🎯",
                GearType.BOOST: "⚡",
                GearType.CONSUMABLE: "💊",
                GearType.ATTACHMENT: "🔧",
                GearType.CAMO: "🎨"
            }
            
            # Draw type icon in center
            icon_text = icon_map.get(item.gear_type, "📦")
            draw.text(
                (x + cell_size//2, y + cell_size//2 - 10),
                icon_text,
                fill=(255, 255, 255),
                font=title_font,
                anchor="mm"
            )
            
            # Draw level
            draw.text(
                (x + 5, y + cell_size - 20),
                f"Lv{item.level}",
                fill=(200, 200, 200),
                font=item_font
            )
            
            # Draw power score
            power_text = str(item.get_power_score())
            draw.text(
                (x + cell_size - 5, y + cell_size - 20),
                power_text,
                fill=(255, 255, 0),
                font=item_font,
                anchor="ra"
            )
        
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        return img_byte_arr.getvalue()
    
    @staticmethod
    def format_crafting_progress(
        recipe_id: str,
        start_time: int,
        completion_time: int,
        current_time: int
    ) -> str:
        """Format crafting progress bar"""
        total_time = completion_time - start_time
        elapsed_time = current_time - start_time
        progress = min(elapsed_time / total_time, 1.0)
        
        # Progress bar
        bar_length = 20
        filled = int(bar_length * progress)
        empty = bar_length - filled
        
        bar = "█" * filled + "░" * empty
        
        # Time remaining
        time_left = max(0, completion_time - current_time)
        minutes_left = time_left // 60
        seconds_left = time_left % 60
        
        display = f"**Crafting Progress:**\n"
        display += f"[{bar}] {progress*100:.0f}%\n"
        
        if time_left > 0:
            display += f"⏱️ Time remaining: {minutes_left}m {seconds_left}s"
        else:
            display += "✅ **COMPLETE!** Collect your item!"
        
        return display

class GearStatsFormatter:
    """Formats gear statistics for display"""
    
    @staticmethod
    def format_enhanced_stats(
        base_stats: Dict[str, float],
        gear_stats: Dict[str, float]
    ) -> str:
        """Format stats showing base + gear enhancement"""
        display = "**📊 ENHANCED COMBAT STATS 📊**\n\n"
        
        stat_displays = [
            ('accuracy', '🎯 Accuracy', True),
            ('damage', '💥 Damage', False),
            ('fire_rate', '⚡ Fire Rate', False),
            ('xp_rate', '⭐ XP Rate', False),
            ('reward_rate', '💰 Reward Rate', False),
            ('critical_chance', '🎲 Crit Chance', True)
        ]
        
        for stat_key, display_name, is_percentage in stat_displays:
            base = base_stats.get(stat_key, 0)
            enhanced = gear_stats.get(stat_key, base)
            
            if enhanced != base:
                improvement = ((enhanced / base) - 1) * 100 if base > 0 else 0
                
                if is_percentage:
                    display += f"{display_name}: {base*100:.0f}% → "
                    display += f"**{enhanced*100:.0f}%** "
                else:
                    display += f"{display_name}: {base:.1f}x → "
                    display += f"**{enhanced:.1f}x** "
                
                display += f"_(+{improvement:.0f}% from gear)_\n"
            else:
                if is_percentage:
                    display += f"{display_name}: {base*100:.0f}%\n"
                else:
                    display += f"{display_name}: {base:.1f}x\n"
        
        # Special stats
        if 'cooldown_reduction' in gear_stats and gear_stats['cooldown_reduction'] > 0:
            display += f"\n⏱️ Cooldown Reduction: -{gear_stats['cooldown_reduction']*100:.0f}%"
        
        return display
    
    @staticmethod
    def format_gear_summary(inventory_display: Dict[str, Any]) -> str:
        """Format gear collection summary"""
        summary = "**🎖️ GEAR COLLECTION SUMMARY 🎖️**\n\n"
        
        # Total stats
        summary += f"**Total Gear:** {inventory_display['total_items']} items\n"
        summary += f"**Total Power:** {inventory_display['total_power']:}\n"
        summary += f"**Storage Used:** {inventory_display['inventory_space']['used']}"
        summary += f"/{inventory_display['inventory_space']['max']}\n\n"
        
        # Rarity breakdown with visual bar
        summary += "**Rarity Distribution:**\n"
        
        total_items = inventory_display['total_items']
        for rarity in GearRarity:
            count = inventory_display['rarity_breakdown'].get(rarity, 0)
            if count > 0:
                percentage = (count / total_items) * 100
                bar_length = int(percentage / 5)  # 20 char max bar
                bar = "█" * bar_length + "░" * (20 - bar_length)
                
                emoji = {
                    GearRarity.COMMON: "⬜",
                    GearRarity.UNCOMMON: "🟩",
                    GearRarity.RARE: "🟦",
                    GearRarity.EPIC: "🟪",
                    GearRarity.LEGENDARY: "🟧",
                    GearRarity.MYTHIC: "🟥"
                }.get(rarity, "⬜")
                
                summary += f"{emoji} {rarity.display_name:10} [{bar}] {count:3} ({percentage:.0f}%)\n"
        
        # Best items showcase
        if inventory_display['items_by_type']:
            summary += "\n**🏆 TOP GEAR BY TYPE 🏆**\n"
            
            for gear_type, rarity_dict in inventory_display['items_by_type'].items():
                all_items = []
                for items in rarity_dict.values():
                    all_items.extend(items)
                
                if all_items:
                    best_item = max(all_items, key=lambda x: x.get_power_score())
                    summary += f"{gear_type.value}: {best_item.get_display_name()} "
                    summary += f"(PWR: {best_item.get_power_score()})\n"
        
        # Active loadout preview
        if inventory_display['active_loadout']:
            loadout = inventory_display['active_loadout']
            summary += f"\n**⚔️ ACTIVE LOADOUT: {loadout.name} ⚔️**\n"
            
            if inventory_display['loadout_stats']:
                stats = inventory_display['loadout_stats']
                key_stats = []
                
                if stats.accuracy_bonus > 0:
                    key_stats.append(f"+{stats.accuracy_bonus*100:.0f}% ACC")
                if stats.damage_bonus > 0:
                    key_stats.append(f"+{stats.damage_bonus*100:.0f}% DMG")
                if stats.xp_multiplier > 1:
                    key_stats.append(f"{stats.xp_multiplier:.1f}x XP")
                
                if key_stats:
                    summary += " | ".join(key_stats)
                
                if inventory_display['set_bonus']:
                    summary += "\n🔥 _Set Bonus Active!_"
        
        return summary