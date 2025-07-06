"""
Gear System Commands for BITTEN
Telegram command handlers for gear inventory management
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler
from datetime import datetime
import json

from .gear_system import (
    GearSystem, GearItem, GearRarity, GearType, 
    GearSlot, Loadout, GearStats
)

logger = logging.getLogger(__name__)

# Conversation states
GEAR_MENU, INVENTORY_VIEW, LOADOUT_VIEW, EQUIP_ITEM, CRAFT_MENU, TRADE_MENU = range(6)


class GearCommands:
    """Handles all gear-related telegram commands"""
    
    def __init__(self, gear_system: GearSystem):
        self.gear_system = gear_system
        
    async def gear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Main /gear command handler"""
        user_id = update.effective_user.id
        
        # Main gear menu
        keyboard = [
            [
                InlineKeyboardButton("🎒 Inventory", callback_data="gear_inventory"),
                InlineKeyboardButton("⚔️ Loadouts", callback_data="gear_loadouts")
            ],
            [
                InlineKeyboardButton("🔨 Crafting", callback_data="gear_crafting"),
                InlineKeyboardButton("💱 Trading", callback_data="gear_trading")
            ],
            [
                InlineKeyboardButton("📊 Stats", callback_data="gear_stats"),
                InlineKeyboardButton("🏪 Shop", callback_data="gear_shop")
            ],
            [InlineKeyboardButton("❌ Close", callback_data="gear_close")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Get user stats
        display = self.gear_system.get_inventory_display(user_id)
        
        message = (
            "🎮 **TACTICAL GEAR MENU** 🎮\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"**Operative:** {update.effective_user.first_name}\n"
            f"**Total Gear:** {display['total_items']} items\n"
            f"**Power Score:** {display['total_power']:,}\n\n"
            "**Rarity Breakdown:**\n"
        )
        
        # Add rarity counts with colors
        rarity_emojis = {
            GearRarity.COMMON: "⬜",
            GearRarity.UNCOMMON: "🟩",
            GearRarity.RARE: "🟦",
            GearRarity.EPIC: "🟪",
            GearRarity.LEGENDARY: "🟧",
            GearRarity.MYTHIC: "🟥"
        }
        
        for rarity, count in display['rarity_breakdown'].items():
            if count > 0:
                emoji = rarity_emojis.get(rarity, "⬜")
                message += f"{emoji} {rarity.display_name}: {count}\n"
        
        message += "\n*Select an option to manage your tactical gear:*"
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        return GEAR_MENU
    
    async def gear_menu_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle gear menu selections"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "gear_close":
            await query.edit_message_text("*Gear menu closed.*", parse_mode='Markdown')
            return ConversationHandler.END
        
        elif query.data == "gear_inventory":
            return await self.show_inventory(update, context)
        
        elif query.data == "gear_loadouts":
            return await self.show_loadouts(update, context)
        
        elif query.data == "gear_crafting":
            return await self.show_crafting(update, context)
        
        elif query.data == "gear_trading":
            return await self.show_trading(update, context)
        
        elif query.data == "gear_stats":
            return await self.show_gear_stats(update, context)
        
        elif query.data == "gear_shop":
            await query.edit_message_text(
                "*🏪 Gear Shop*\n\n"
                "The gear shop is integrated with the XP Shop.\n"
                "Use `/shop` to browse and purchase gear with XP.",
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        
        return GEAR_MENU
    
    async def show_inventory(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Display user's gear inventory"""
        query = update.callback_query
        user_id = update.effective_user.id
        
        inventory = self.gear_system.get_user_inventory(user_id)
        
        if not inventory:
            await query.edit_message_text(
                "*🎒 Your Inventory is Empty*\n\n"
                "Complete missions and achievements to earn gear drops!",
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        
        # Group by type
        grouped = {}
        for item_id, item in inventory.items():
            if item.gear_type not in grouped:
                grouped[item.gear_type] = []
            grouped[item.gear_type].append(item)
        
        message = "🎒 **YOUR TACTICAL INVENTORY** 🎒\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Show items by type
        for gear_type, items in grouped.items():
            message += f"**{gear_type.value}s:**\n"
            
            # Sort by rarity and power
            items.sort(key=lambda x: (x.rarity.value_multiplier, x.get_power_score()), reverse=True)
            
            for item in items[:5]:  # Show top 5 per category
                message += f"{item.get_display_name()} "
                message += f"(Lvl {item.level} | Power: {item.get_power_score()})\n"
            
            if len(items) > 5:
                message += f"*...and {len(items) - 5} more*\n"
            
            message += "\n"
        
        # Add action buttons
        keyboard = [
            [
                InlineKeyboardButton("🔧 Equip Gear", callback_data="inventory_equip"),
                InlineKeyboardButton("♻️ Salvage", callback_data="inventory_salvage")
            ],
            [
                InlineKeyboardButton("📋 View Details", callback_data="inventory_details"),
                InlineKeyboardButton("🔙 Back", callback_data="gear_back_to_menu")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        return INVENTORY_VIEW
    
    async def show_loadouts(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Display user's loadouts"""
        query = update.callback_query
        user_id = update.effective_user.id
        
        loadouts = self.gear_system.get_user_loadouts(user_id)
        active_loadout = self.gear_system.get_active_loadout(user_id)
        inventory = self.gear_system.get_user_inventory(user_id)
        
        message = "⚔️ **LOADOUT MANAGEMENT** ⚔️\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        if not loadouts:
            message += "*No loadouts created yet.*\n\n"
        else:
            for loadout in loadouts[:3]:  # Show up to 3 loadouts
                is_active = active_loadout and loadout.loadout_id == active_loadout.loadout_id
                
                message += f"**{loadout.name}** {'✅ ACTIVE' if is_active else ''}\n"
                message += f"Power: {loadout.get_power_score(inventory):,}\n"
                
                # Show equipped items
                equipped_count = sum(1 for item_id in loadout.slots.values() if item_id)
                message += f"Equipped: {equipped_count}/{len(GearSlot)} slots\n\n"
        
        # Show active loadout stats
        if active_loadout:
            stats = active_loadout.get_total_stats(inventory)
            set_bonus = self.gear_system.get_gear_set_bonus(user_id, active_loadout)
            
            message += "**Active Loadout Stats:**\n"
            message += f"• Accuracy: +{stats.accuracy_bonus*100:.1f}%\n"
            message += f"• Damage: +{stats.damage_bonus*100:.1f}%\n"
            message += f"• Fire Rate: +{stats.fire_rate_bonus*100:.1f}%\n"
            message += f"• XP Multiplier: {stats.xp_multiplier:.1f}x\n"
            
            if set_bonus:
                message += "\n**🔥 Set Bonus Active! 🔥**\n"
        
        keyboard = [
            [
                InlineKeyboardButton("📝 Create Loadout", callback_data="loadout_create"),
                InlineKeyboardButton("✏️ Edit Loadout", callback_data="loadout_edit")
            ],
            [
                InlineKeyboardButton("🔄 Switch Active", callback_data="loadout_switch"),
                InlineKeyboardButton("🔙 Back", callback_data="gear_back_to_menu")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        return LOADOUT_VIEW
    
    async def show_crafting(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Display crafting menu"""
        query = update.callback_query
        user_id = update.effective_user.id
        
        # Check active crafts
        completed = self.gear_system.check_crafting_completion(user_id)
        
        message = "🔨 **WEAPON CRAFTING** 🔨\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        if completed:
            message += "**✅ Crafting Complete:**\n"
            for craft in completed:
                if craft['success']:
                    message += f"• Successfully crafted {craft['item_id']}!\n"
                else:
                    message += f"• Failed to craft {craft['item_id']} (materials lost)\n"
            message += "\n"
        
        # Show available recipes
        message += "**Available Blueprints:**\n\n"
        
        inventory = self.gear_system.get_user_inventory(user_id)
        inventory_counts = {}
        for item_id in inventory:
            inventory_counts[item_id] = inventory_counts.get(item_id, 0) + 1
        
        recipes_available = False
        for recipe_id, recipe in self.gear_system.CRAFTING_RECIPES.items():
            can_craft, reason = recipe.can_craft(inventory_counts, 50)  # Placeholder level
            
            result_item = self.gear_system.GEAR_CATALOG.get(recipe.result_item_id)
            if result_item:
                message += f"**{result_item.get_display_name()}**\n"
                message += f"Time: {recipe.crafting_time//60} minutes\n"
                
                if can_craft:
                    message += "✅ Ready to craft\n"
                    recipes_available = True
                else:
                    message += f"❌ {reason}\n"
                
                message += "\n"
        
        keyboard = []
        if recipes_available:
            keyboard.append([
                InlineKeyboardButton("🔨 Start Crafting", callback_data="craft_start")
            ])
        
        keyboard.append([
            InlineKeyboardButton("📦 Materials", callback_data="craft_materials"),
            InlineKeyboardButton("🔙 Back", callback_data="gear_back_to_menu")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        return CRAFT_MENU
    
    async def show_trading(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Display trading menu"""
        query = update.callback_query
        user_id = update.effective_user.id
        
        message = "💱 **GEAR TRADING POST** 💱\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        message += "**Trading Rules:**\n"
        message += "• Only tradeable items can be exchanged\n"
        message += "• Trades expire after 24 hours\n"
        message += "• Both parties must have the items\n"
        message += "• No trade backs - trades are final\n\n"
        
        message += "*Trading system coming soon!*\n\n"
        message += "Join the squad to find trading partners:\n"
        message += "Use `/squad` to see who's online"
        
        keyboard = [
            [
                InlineKeyboardButton("📤 Create Offer", callback_data="trade_create"),
                InlineKeyboardButton("📥 View Offers", callback_data="trade_view")
            ],
            [
                InlineKeyboardButton("📜 Trade History", callback_data="trade_history"),
                InlineKeyboardButton("🔙 Back", callback_data="gear_back_to_menu")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        return TRADE_MENU
    
    async def show_gear_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show comprehensive gear statistics"""
        query = update.callback_query
        user_id = update.effective_user.id
        
        display = self.gear_system.get_inventory_display(user_id)
        
        message = "📊 **GEAR STATISTICS** 📊\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Inventory summary
        message += f"**Total Items:** {display['total_items']}\n"
        message += f"**Total Power:** {display['total_power']:,}\n"
        message += f"**Storage:** {display['inventory_space']['used']}/{display['inventory_space']['max']}\n\n"
        
        # Best items by type
        message += "**Top Gear by Type:**\n"
        for gear_type, rarity_dict in display['items_by_type'].items():
            all_items = []
            for items in rarity_dict.values():
                all_items.extend(items)
            
            if all_items:
                best_item = max(all_items, key=lambda x: x.get_power_score())
                message += f"• {gear_type.value}: {best_item.get_display_name()} (Power: {best_item.get_power_score()})\n"
        
        message += "\n**Collection Progress:**\n"
        
        # Calculate collection stats
        total_possible = len(self.gear_system.GEAR_CATALOG)
        collected = len([item for item in display['items_by_type']])
        
        message += f"• Catalog Items: {collected}/{total_possible}\n"
        message += f"• Legendary Items: {display['rarity_breakdown'].get(GearRarity.LEGENDARY, 0)}\n"
        message += f"• Mythic Items: {display['rarity_breakdown'].get(GearRarity.MYTHIC, 0)}\n"
        
        # Add loadout power if active
        if display['active_loadout']:
            loadout_power = display['active_loadout'].get_power_score(
                self.gear_system.get_user_inventory(user_id)
            )
            message += f"\n**Active Loadout Power:** {loadout_power:,}"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="gear_back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        return GEAR_MENU
    
    async def handle_back_to_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle back to main gear menu"""
        query = update.callback_query
        await query.answer()
        
        # Recreate main menu
        keyboard = [
            [
                InlineKeyboardButton("🎒 Inventory", callback_data="gear_inventory"),
                InlineKeyboardButton("⚔️ Loadouts", callback_data="gear_loadouts")
            ],
            [
                InlineKeyboardButton("🔨 Crafting", callback_data="gear_crafting"),
                InlineKeyboardButton("💱 Trading", callback_data="gear_trading")
            ],
            [
                InlineKeyboardButton("📊 Stats", callback_data="gear_stats"),
                InlineKeyboardButton("🏪 Shop", callback_data="gear_shop")
            ],
            [InlineKeyboardButton("❌ Close", callback_data="gear_close")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        user_id = update.effective_user.id
        display = self.gear_system.get_inventory_display(user_id)
        
        message = (
            "🎮 **TACTICAL GEAR MENU** 🎮\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"**Operative:** {update.effective_user.first_name}\n"
            f"**Total Gear:** {display['total_items']} items\n"
            f"**Power Score:** {display['total_power']:,}\n\n"
            "*Select an option to manage your tactical gear:*"
        )
        
        await query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        return GEAR_MENU
    
    async def handle_inventory_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle inventory actions"""
        query = update.callback_query
        await query.answer()
        
        action = query.data
        
        if action == "inventory_equip":
            await query.edit_message_text(
                "*🔧 Equip Gear*\n\n"
                "To equip gear, use:\n"
                "`/equip <item_name>`\n\n"
                "Example: `/equip MACD Elite`",
                parse_mode='Markdown'
            )
        
        elif action == "inventory_salvage":
            await query.edit_message_text(
                "*♻️ Salvage Gear*\n\n"
                "To salvage gear for materials, use:\n"
                "`/salvage <item_name>`\n\n"
                "⚠️ Warning: Salvaging destroys the item!",
                parse_mode='Markdown'
            )
        
        elif action == "inventory_details":
            await query.edit_message_text(
                "*📋 Item Details*\n\n"
                "To view detailed stats, use:\n"
                "`/gear info <item_name>`\n\n"
                "This shows all stats, effects, and requirements.",
                parse_mode='Markdown'
            )
        
        return ConversationHandler.END
    
    async def handle_loadout_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle loadout actions"""
        query = update.callback_query
        await query.answer()
        
        action = query.data
        user_id = update.effective_user.id
        
        if action == "loadout_create":
            # Create new loadout
            loadout_name = f"Loadout {len(self.gear_system.get_user_loadouts(user_id)) + 1}"
            new_loadout = self.gear_system.create_loadout(user_id, loadout_name)
            
            if new_loadout:
                await query.edit_message_text(
                    f"*✅ Created new loadout: {loadout_name}*\n\n"
                    "Use `/equip <item>` to add gear to this loadout.",
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text(
                    "*❌ Failed to create loadout*",
                    parse_mode='Markdown'
                )
        
        elif action == "loadout_edit":
            await query.edit_message_text(
                "*✏️ Edit Loadout*\n\n"
                "To rename a loadout:\n"
                "`/loadout rename <old_name> <new_name>`\n\n"
                "To delete a loadout:\n"
                "`/loadout delete <name>`",
                parse_mode='Markdown'
            )
        
        elif action == "loadout_switch":
            loadouts = self.gear_system.get_user_loadouts(user_id)
            
            if len(loadouts) <= 1:
                await query.edit_message_text(
                    "*You need at least 2 loadouts to switch between them.*",
                    parse_mode='Markdown'
                )
            else:
                keyboard = []
                for loadout in loadouts:
                    keyboard.append([
                        InlineKeyboardButton(
                            f"{loadout.name} {'✅' if loadout.is_active else ''}",
                            callback_data=f"activate_loadout_{loadout.loadout_id}"
                        )
                    ])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "*Select loadout to activate:*",
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
        
        return ConversationHandler.END
    
    async def handle_craft_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle crafting actions"""
        query = update.callback_query
        await query.answer()
        
        action = query.data
        user_id = update.effective_user.id
        
        if action == "craft_start":
            # Show craftable recipes
            keyboard = []
            for recipe_id, recipe in self.gear_system.CRAFTING_RECIPES.items():
                result_item = self.gear_system.GEAR_CATALOG.get(recipe.result_item_id)
                if result_item:
                    keyboard.append([
                        InlineKeyboardButton(
                            result_item.get_display_name(),
                            callback_data=f"craft_item_{recipe_id}"
                        )
                    ])
            
            keyboard.append([InlineKeyboardButton("Cancel", callback_data="gear_back_to_menu")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "*Select item to craft:*",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        
        elif action.startswith("craft_item_"):
            recipe_id = action.replace("craft_item_", "")
            success, message, craft_id = self.gear_system.craft_item(user_id, recipe_id)
            
            if success:
                await query.edit_message_text(
                    f"*🔨 Crafting Started!*\n\n{message}\n\n"
                    f"Craft ID: `{craft_id}`\n"
                    "Check back later to collect your item.",
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text(
                    f"*❌ Crafting Failed*\n\n{message}",
                    parse_mode='Markdown'
                )
        
        elif action == "craft_materials":
            inventory = self.gear_system.get_user_inventory(user_id)
            materials = [item for item in inventory.values() 
                        if "craft_material" in item.item_id]
            
            message = "*📦 Crafting Materials*\n\n"
            if materials:
                material_counts = {}
                for mat in materials:
                    material_counts[mat.name] = material_counts.get(mat.name, 0) + 1
                
                for name, count in material_counts.items():
                    message += f"• {name}: {count}\n"
            else:
                message += "No crafting materials in inventory.\n"
                message += "Salvage unwanted gear to get materials!"
            
            await query.edit_message_text(message, parse_mode='Markdown')
        
        return ConversationHandler.END
    
    async def handle_trade_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle trading actions"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            "*💱 Trading System*\n\n"
            "The trading system is currently under development.\n"
            "Check back soon for peer-to-peer gear trading!",
            parse_mode='Markdown'
        )
        
        return ConversationHandler.END
    
    def get_conversation_handler(self) -> ConversationHandler:
        """Get the conversation handler for gear commands"""
        return ConversationHandler(
            entry_points=[CommandHandler('gear', self.gear_command)],
            states={
                GEAR_MENU: [
                    CallbackQueryHandler(self.gear_menu_handler, pattern='^gear_'),
                ],
                INVENTORY_VIEW: [
                    CallbackQueryHandler(self.handle_inventory_action, pattern='^inventory_'),
                    CallbackQueryHandler(self.handle_back_to_menu, pattern='^gear_back_to_menu$'),
                ],
                LOADOUT_VIEW: [
                    CallbackQueryHandler(self.handle_loadout_action, pattern='^loadout_'),
                    CallbackQueryHandler(self.handle_back_to_menu, pattern='^gear_back_to_menu$'),
                ],
                CRAFT_MENU: [
                    CallbackQueryHandler(self.handle_craft_action, pattern='^craft_'),
                    CallbackQueryHandler(self.handle_back_to_menu, pattern='^gear_back_to_menu$'),
                ],
                TRADE_MENU: [
                    CallbackQueryHandler(self.handle_trade_action, pattern='^trade_'),
                    CallbackQueryHandler(self.handle_back_to_menu, pattern='^gear_back_to_menu$'),
                ],
            },
            fallbacks=[
                CallbackQueryHandler(self.gear_menu_handler, pattern='^gear_close$'),
                CommandHandler('gear', self.gear_command)
            ],
        )


# Quick action commands
async def equip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick equip command"""
    if not context.args:
        await update.message.reply_text(
            "*Usage:* `/equip <item_name>`\n\n"
            "Example: `/equip MACD Elite`",
            parse_mode='Markdown'
        )
        return
    
    user_id = update.effective_user.id
    item_name = ' '.join(context.args)
    
    # Find item in inventory
    gear_system = context.bot_data.get('gear_system')
    if not gear_system:
        await update.message.reply_text("*Gear system not initialized*", parse_mode='Markdown')
        return
    
    inventory = gear_system.get_user_inventory(user_id)
    
    # Find item by name (case insensitive)
    found_item = None
    for item_id, item in inventory.items():
        if item_name.lower() in item.name.lower():
            found_item = item
            break
    
    if not found_item:
        await update.message.reply_text(
            f"*Item '{item_name}' not found in inventory*",
            parse_mode='Markdown'
        )
        return
    
    # Equip item
    success, message = gear_system.equip_item(user_id, found_item.item_id)
    
    if success:
        await update.message.reply_text(
            f"*✅ {message}*\n\n"
            f"Power Score: {found_item.get_power_score()}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"*❌ {message}*",
            parse_mode='Markdown'
        )


async def salvage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick salvage command"""
    if not context.args:
        await update.message.reply_text(
            "*Usage:* `/salvage <item_name>`\n\n"
            "⚠️ *Warning: This will destroy the item!*",
            parse_mode='Markdown'
        )
        return
    
    user_id = update.effective_user.id
    item_name = ' '.join(context.args)
    
    # Find item in inventory
    gear_system = context.bot_data.get('gear_system')
    if not gear_system:
        await update.message.reply_text("*Gear system not initialized*", parse_mode='Markdown')
        return
    
    inventory = gear_system.get_user_inventory(user_id)
    
    # Find item by name
    found_item = None
    for item_id, item in inventory.items():
        if item_name.lower() in item.name.lower():
            found_item = item
            break
    
    if not found_item:
        await update.message.reply_text(
            f"*Item '{item_name}' not found in inventory*",
            parse_mode='Markdown'
        )
        return
    
    # Confirm salvage
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm Salvage", 
                               callback_data=f"confirm_salvage_{found_item.item_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_salvage")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"*Salvage {found_item.get_display_name()}?*\n\n"
        f"Rarity: {found_item.rarity.display_name}\n"
        f"Power: {found_item.get_power_score()}\n"
        f"Salvage Value: {found_item.salvage_value} materials\n\n"
        f"⚠️ *This action cannot be undone!*",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def handle_salvage_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle salvage confirmation"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_salvage":
        await query.edit_message_text("*Salvage cancelled.*", parse_mode='Markdown')
        return
    
    if query.data.startswith("confirm_salvage_"):
        item_id = query.data.replace("confirm_salvage_", "")
        user_id = update.effective_user.id
        
        gear_system = context.bot_data.get('gear_system')
        success, message, value = gear_system.salvage_item(user_id, item_id)
        
        if success:
            await query.edit_message_text(
                f"*✅ {message}*\n\n"
                "Materials have been added to your inventory.",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                f"*❌ {message}*",
                parse_mode='Markdown'
            )


# Drop simulation command (for testing)
async def gear_drop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Simulate a gear drop (admin only)"""
    user_id = update.effective_user.id
    
    # Check if user is admin (you'd implement proper admin check)
    if user_id not in [123456789]:  # Replace with actual admin IDs
        await update.message.reply_text("*Admin only command*", parse_mode='Markdown')
        return
    
    gear_system = context.bot_data.get('gear_system')
    if not gear_system:
        await update.message.reply_text("*Gear system not initialized*", parse_mode='Markdown')
        return
    
    # Generate random drop
    item = gear_system.generate_random_drop(
        user_level=50,  # Would get actual level
        luck_multiplier=1.5
    )
    
    # Add to inventory
    gear_system.add_item_to_inventory(user_id, item, source="admin_drop")
    
    await update.message.reply_text(
        f"*🎁 GEAR DROP! 🎁*\n\n"
        f"You received: {item.get_display_name()}\n"
        f"Type: {item.gear_type.value}\n"
        f"Rarity: {item.rarity.display_name}\n"
        f"Power: {item.get_power_score()}\n\n"
        f"*{item.description}*",
        parse_mode='Markdown'
    )