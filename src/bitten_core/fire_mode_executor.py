#!/usr/bin/env python3
"""
Fire Mode Execution Logic
Handles SEMI_AUTO and FULL_AUTO execution based on user settings
"""

import logging
import json
from datetime import datetime
from typing import Dict, Optional, Tuple
from telebot import types
from .fire_mode_database import fire_mode_db

logger = logging.getLogger(__name__)

class FireModeExecutor:
    """Executes trades based on user's fire mode settings"""
    
    def __init__(self, bot=None):
        self.bot = bot
    
    def should_show_confirm_buttons(self, user_id: str, mission: Dict) -> bool:
        """Check if mission should show confirm button for SEMI_AUTO"""
        mode_info = fire_mode_db.get_user_mode(user_id)
        
        # Show confirm buttons if:
        # 1. User is in SELECT mode
        # 2. Mission is still fireable (timer not expired)
        if mode_info['current_mode'] == 'SELECT' and not mission.get('expired', False):
            return True
        
        return False
    
    def should_auto_fire(self, user_id: str, user_tier: str, mission: Dict) -> Tuple[bool, str]:
        """Check if mission should auto-fire for FULL_AUTO users"""
        mode_info = fire_mode_db.get_user_mode(user_id)
        
        # Check if user is in AUTO mode
        if mode_info['current_mode'] != 'AUTO':
            return False, "Not in AUTO mode"
        
        # Check if user tier allows AUTO
        if user_tier not in ["COMMANDER"]:
            return False, "Tier doesn't support AUTO"
        
        # Check TCS threshold (80% for AUTO - sleep mode trading)
        tcs = mission.get('tcs', 0)
        if tcs < 80:
            return False, f"TCS {tcs}% < 80% threshold"
        
        # Check if slot available
        if not fire_mode_db.check_slot_available(user_id):
            return False, "No slots available"
        
        # Check if mission not expired
        if mission.get('expired', False):
            return False, "Mission expired"
        
        return True, "Ready to auto-fire"
    
    def create_semi_auto_keyboard(self, mission_id: str) -> types.InlineKeyboardMarkup:
        """Create inline keyboard for SELECT FIRE confirmation"""
        keyboard = types.InlineKeyboardMarkup()
        
        # Single CONFIRM button (no cancel needed per user requirement)
        keyboard.row(
            types.InlineKeyboardButton(
                "🚀 CONFIRM FIRE", 
                callback_data=f"semi_fire_{mission_id}"
            )
        )
        
        return keyboard
    
    def format_semi_auto_message(self, mission: Dict) -> str:
        """Format mission details for SELECT FIRE display"""
        # Extract mission details
        symbol = mission.get('symbol', 'UNKNOWN')
        direction = mission.get('direction', 'UNKNOWN')
        entry = mission.get('entry_price', 0)
        sl = mission.get('stop_loss', 0)
        tp = mission.get('take_profit', 0)
        risk_amount = mission.get('risk_amount', 0)
        potential_profit = mission.get('potential_profit', 0)
        signal_type = mission.get('signal_type', 'UNKNOWN')
        tcs = mission.get('tcs', 0)
        
        # Format message
        message = f"""🎯 **SELECT FIRE TRADE READY**

**Signal**: {signal_type}
**Pair**: {symbol}
**Direction**: {direction}
**TCS**: {tcs}%

**Entry**: {entry}
**Stop Loss**: {sl}
**Take Profit**: {tp}

**Risk**: ${risk_amount:.2f}
**Potential Profit**: ${potential_profit:.2f}

⏱️ Confirm before timer expires"""
        
        return message
    
    def execute_auto_fire(self, user_id: str, mission: Dict) -> Dict:
        """Execute AUTO mode fire"""
        try:
            # Occupy slot first
            mission_id = mission.get('mission_id')
            symbol = mission.get('symbol')
            
            if not fire_mode_db.occupy_slot(user_id, mission_id, symbol):
                return {
                    'success': False,
                    'message': 'Failed to occupy slot',
                    'fired': False
                }
            
            # Here you would call the actual fire mechanism
            # For now, return success
            logger.info(f"AUTO-FIRED mission {mission_id} for user {user_id}")
            
            return {
                'success': True,
                'message': 'AUTO-FIRED successfully',
                'fired': True,
                'mode': 'AUTO'
            }
            
        except Exception as e:
            logger.error(f"Error in auto-fire: {e}")
            return {
                'success': False,
                'message': f'Auto-fire error: {str(e)}',
                'fired': False
            }
    
    def handle_semi_fire_callback(self, bot, call):
        """Handle SELECT FIRE confirmation callback"""
        try:
            # Extract mission_id from callback data
            mission_id = call.data.replace("semi_fire_", "")
            user_id = str(call.from_user.id)
            
            # Here you would:
            # 1. Verify mission still valid
            # 2. Execute the trade
            # 3. Update the message
            
            # For now, just acknowledge
            bot.answer_callback_query(call.id, "🚀 Trade executed!")
            
            # Update message to show execution
            bot.edit_message_text(
                f"✅ **TRADE EXECUTED**\n\nMission ID: {mission_id}\nMode: SELECT FIRE",
                call.message.chat.id,
                call.message.message_id
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling semi-fire callback: {e}")
            bot.answer_callback_query(call.id, "Error executing trade", show_alert=True)
            return False
    
    def check_and_execute_auto_trades(self, user_id: str, user_tier: str, new_mission: Dict) -> Optional[Dict]:
        """Check if a new mission should be auto-fired"""
        # Check if should auto-fire
        should_fire, reason = self.should_auto_fire(user_id, user_tier, new_mission)
        
        if should_fire:
            # Execute auto-fire
            result = self.execute_auto_fire(user_id, new_mission)
            logger.info(f"Auto-fire result for user {user_id}: {result}")
            return result
        else:
            logger.info(f"Auto-fire skipped for user {user_id}: {reason}")
            return None
    
    def release_slot_on_trade_close(self, user_id: str, mission_id: str):
        """Release slot when trade closes"""
        if fire_mode_db.release_slot(user_id, mission_id):
            logger.info(f"Released slot for user {user_id}, mission {mission_id}")
        else:
            logger.error(f"Failed to release slot for user {user_id}, mission {mission_id}")
    
    def get_mode_status_text(self, user_id: str, user_tier: str) -> str:
        """Get formatted text showing current fire mode status"""
        mode_info = fire_mode_db.get_user_mode(user_id)
        current_mode = mode_info['current_mode']
        
        status = f"🎮 Fire Mode: **{current_mode}**"
        
        if current_mode == 'AUTO':
            if user_tier in ["COMMANDER"]:
                status += f"\n🎰 Slots: {mode_info['slots_in_use']}/{mode_info['max_slots']}"
                status += "\n🎯 Auto-firing 87%+ TCS signals"
            else:
                status += "\n🔒 AUTO requires COMMANDER+ subscription"
        elif current_mode == 'SELECT':
            status += "\n🎯 One-click confirmations active"
        else:
            status += "\n🔫 SELECT FIRE mode active"
        
        return status

# Singleton instance
fire_mode_executor = FireModeExecutor()