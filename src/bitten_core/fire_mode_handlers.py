#!/usr/bin/env python3
"""
Fire Mode Bot Command Handlers
Handles mode switching and slot management commands
"""

import logging
from typing import Dict, Optional
from telebot import types
from .fire_mode_database import fire_mode_db

logger = logging.getLogger(__name__)

class FireModeHandlers:
    """Handles fire mode related bot commands"""
    
    @staticmethod
    def validate_fire_mode_access(user_tier: str, requested_mode: str) -> tuple[bool, str]:
        """Validate if user can use requested fire mode"""
        # All modes visible to all users (for FOMO)
        # AUTO only available for COMMANDER (premium tier)
        
        if requested_mode == "AUTO":
            if user_tier != "COMMANDER":
                return False, "🔒 AUTO mode requires COMMANDER subscription"
        
        return True, ""
    
    @staticmethod
    def get_mode_keyboard(user_tier: str, current_mode: str) -> types.InlineKeyboardMarkup:
        """Create inline keyboard for mode selection"""
        keyboard = types.InlineKeyboardMarkup()
        
        # Create buttons for each mode
        modes = [
            ("🎯 SELECT FIRE", "SELECT", "mode_SELECT"),
            ("🚀 FULL AUTO", "AUTO", "mode_AUTO")
        ]
        
        buttons = []
        for display_name, mode_name, callback_data in modes:
            # Add checkmark to current mode
            if mode_name == current_mode:
                display_name = f"✅ {display_name}"
            
            # Add lock icon for AUTO if not COMMANDER
            if mode_name == "AUTO" and user_tier != "COMMANDER":
                display_name = f"{display_name} 🔒"
            
            buttons.append(types.InlineKeyboardButton(display_name, callback_data=callback_data))
        
        # Add buttons in a column
        for button in buttons:
            keyboard.row(button)
        
        # Add slots configuration for COMMANDER users
        if user_tier == "COMMANDER":
            keyboard.row(types.InlineKeyboardButton("⚙️ Configure Slots", callback_data="mode_slots"))
        
        return keyboard
    
    @staticmethod
    def handle_mode_command(bot, message, user_tier: str):
        """Handle /mode command"""
        user_id = str(message.from_user.id)
        
        try:
            # Get current mode with error handling
            logger.info(f"Processing /mode command for user {user_id} (tier: {user_tier})")
            mode_info = fire_mode_db.get_user_mode(user_id)
            current_mode = mode_info['current_mode']
            logger.info(f"Current mode for user {user_id}: {current_mode}")
        except Exception as e:
            logger.error(f"Failed to get user mode for {user_id}: {e}")
            bot.send_message(message.chat.id, "❌ Error accessing fire mode settings. Please try again.")
            return
        
        # Check if mode specified in command
        parts = message.text.split()
        if len(parts) > 1:
            requested_mode = parts[1].upper()
            # Map old names to new names for compatibility
            mode_map = {"MANUAL": "SELECT", "SEMI": "SELECT", "SEMI-AUTO": "SELECT"}
            requested_mode = mode_map.get(requested_mode, requested_mode)
            
            if requested_mode in ["SELECT", "AUTO"]:
                try:
                    # Validate access
                    valid, error_msg = FireModeHandlers.validate_fire_mode_access(user_tier, requested_mode)
                    if not valid:
                        logger.warning(f"User {user_id} denied access to {requested_mode}: {error_msg}")
                        bot.send_message(message.chat.id, error_msg)
                        return
                    
                    # Set new mode
                    logger.info(f"Setting fire mode for user {user_id} to {requested_mode}")
                    if fire_mode_db.set_user_mode(user_id, requested_mode, "User command"):
                        success_msg = f"✅ Fire mode changed to {requested_mode}\n"
                        if requested_mode == 'AUTO':
                            success_msg += "🎯 87%+ TCS signals will auto-fire when slots available"
                        
                        bot.send_message(message.chat.id, success_msg)
                        logger.info(f"Successfully changed fire mode for user {user_id} to {requested_mode}")
                    else:
                        logger.error(f"Failed to set fire mode for user {user_id} to {requested_mode}")
                        bot.send_message(message.chat.id, "❌ Error changing fire mode. Please try again.")
                    return
                except Exception as e:
                    logger.error(f"Error processing mode change for user {user_id}: {e}")
                    bot.send_message(message.chat.id, "❌ Error processing mode change. Please try again.")
                    return
        
        # Show mode selection menu
        try:
            mode_text = f"""🎮 **Fire Mode Configuration**

Current Mode: **{current_mode}**
Your Tier: **{user_tier}**

🎯 **SELECT FIRE** - One-click confirmations
🚀 **FULL AUTO** - Auto-fire 87%+ TCS signals

{f"Slots in use: {mode_info['slots_in_use']}/{mode_info['max_slots']}" if current_mode == "AUTO" else ""}

Select your fire mode:"""
            
            keyboard = FireModeHandlers.get_mode_keyboard(user_tier, current_mode)
            bot.send_message(message.chat.id, mode_text, reply_markup=keyboard, parse_mode="Markdown")
            logger.info(f"Successfully displayed mode menu for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error displaying mode menu for user {user_id}: {e}")
            # Send fallback message without keyboard
            fallback_text = f"🎮 Current Fire Mode: {current_mode}\nTier: {user_tier}\n\nUse /mode SELECT or /mode AUTO to change modes."
            bot.send_message(message.chat.id, fallback_text)
    
    @staticmethod
    def handle_mode_callback(bot, call, user_tier: str):
        """Handle fire mode selection callbacks"""
        user_id = str(call.from_user.id)
        
        try:
            logger.info(f"Processing mode callback for user {user_id}: {call.data}")
            
            if call.data == "mode_slots":
                # Show slot configuration
                FireModeHandlers.show_slot_config(bot, call, user_tier)
                return
            
            # Extract requested mode
            requested_mode = call.data.replace("mode_", "")
            logger.info(f"User {user_id} requesting mode change to: {requested_mode}")
            
            # Validate access
            valid, error_msg = FireModeHandlers.validate_fire_mode_access(user_tier, requested_mode)
            if not valid:
                logger.warning(f"Mode access denied for user {user_id} to {requested_mode}: {error_msg}")
                bot.answer_callback_query(call.id, error_msg, show_alert=True)
                return
            
            # Set new mode
            if fire_mode_db.set_user_mode(user_id, requested_mode, "Inline selection"):
                bot.answer_callback_query(call.id, f"Fire mode changed to {requested_mode}")
                logger.info(f"Successfully changed fire mode for user {user_id} to {requested_mode}")
                
                # Update message with new keyboard
                mode_info = fire_mode_db.get_user_mode(user_id)
                keyboard = FireModeHandlers.get_mode_keyboard(user_tier, requested_mode)
                
                updated_text = f"""🎮 **Fire Mode Configuration**

Current Mode: **{requested_mode}** ✅
Your Tier: **{user_tier}**

{"🎯 87%+ TCS signals will auto-fire when slots available" if requested_mode == "AUTO" else ""}
{f"Slots: {mode_info['slots_in_use']}/{mode_info['max_slots']}" if requested_mode == "AUTO" else ""}"""
                
                try:
                    bot.edit_message_text(
                        updated_text,
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Failed to update message for user {user_id}: {e}")
                    # Send new message if editing fails
                    bot.send_message(call.message.chat.id, updated_text, reply_markup=keyboard, parse_mode="Markdown")
            else:
                logger.error(f"Failed to set fire mode for user {user_id} to {requested_mode}")
                bot.answer_callback_query(call.id, "Error changing fire mode", show_alert=True)
                
        except Exception as e:
            logger.error(f"Critical error in mode callback for user {user_id}: {e}")
            bot.answer_callback_query(call.id, "System error. Please try /mode command instead.", show_alert=True)
    
    @staticmethod
    def show_slot_config(bot, call, user_tier: str):
        """Show slot configuration menu"""
        user_id = str(call.from_user.id)
        mode_info = fire_mode_db.get_user_mode(user_id)
        
        keyboard = types.InlineKeyboardMarkup()
        
        # Slot options
        for slots in [1, 2, 3]:
            check = "✅ " if mode_info['max_slots'] == slots else ""
            keyboard.row(
                types.InlineKeyboardButton(
                    f"{check}{slots} Slot{'s' if slots > 1 else ''}", 
                    callback_data=f"slots_{slots}"
                )
            )
        
        keyboard.row(types.InlineKeyboardButton("⬅️ Back", callback_data="mode_back"))
        
        text = f"""⚙️ **Slot Configuration**

Maximum concurrent positions for AUTO mode
Current: **{mode_info['max_slots']} slot{'s' if mode_info['max_slots'] > 1 else ''}**
In use: **{mode_info['slots_in_use']}**

Select maximum slots:"""
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    @staticmethod
    def handle_slots_callback(bot, call, user_tier: str):
        """Handle slot selection callbacks"""
        user_id = str(call.from_user.id)
        
        if call.data == "mode_back":
            # Go back to mode selection
            FireModeHandlers.handle_mode_command(bot, call.message, user_tier)
            return
        
        # Extract slot count
        slots = int(call.data.replace("slots_", ""))
        
        if fire_mode_db.set_max_slots(user_id, slots):
            bot.answer_callback_query(call.id, f"Max slots set to {slots}")
            # Show updated menu
            FireModeHandlers.show_slot_config(bot, call, user_tier)
        else:
            bot.answer_callback_query(call.id, "Error setting slots", show_alert=True)
    
    @staticmethod
    def handle_slots_command(bot, message, user_tier: str):
        """Handle /slots command"""
        user_id = str(message.from_user.id)
        
        # Check if COMMANDER
        if user_tier != "COMMANDER":
            bot.send_message(message.chat.id, "🔒 Slot configuration requires COMMANDER subscription")
            return
        
        # Check if slots specified
        parts = message.text.split()
        if len(parts) > 1:
            try:
                slots = int(parts[1])
                if 1 <= slots <= 3:
                    if fire_mode_db.set_max_slots(user_id, slots):
                        bot.send_message(message.chat.id, f"✅ Max slots set to {slots}")
                    else:
                        bot.send_message(message.chat.id, "❌ Error setting slots")
                else:
                    bot.send_message(message.chat.id, "❌ Slots must be between 1 and 3")
            except ValueError:
                bot.send_message(message.chat.id, "❌ Invalid slot number")
            return
        
        # Show current slots
        mode_info = fire_mode_db.get_user_mode(user_id)
        active_slots = fire_mode_db.get_active_slots(user_id)
        
        slots_text = f"""🎰 **Slot Status**

Max Slots: **{mode_info['max_slots']}**
In Use: **{mode_info['slots_in_use']}**
Available: **{mode_info['max_slots'] - mode_info['slots_in_use']}**

Active Positions:"""
        
        if active_slots:
            for i, slot in enumerate(active_slots, 1):
                slots_text += f"\n{i}. {slot['symbol']} (Mission: {slot['mission_id'][:8]}...)"
        else:
            slots_text += "\nNo active positions"
        
        slots_text += "\n\nUse `/slots [1-3]` to set max slots"
        
        bot.send_message(message.chat.id, slots_text, parse_mode="Markdown")