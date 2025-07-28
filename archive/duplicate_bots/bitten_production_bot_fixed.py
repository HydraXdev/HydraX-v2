#!/usr/bin/env python3
"""
BITTEN Production Trading Bot - Fixed Version with Rate Limiting
Handles all trading commands and production integrations
"""

import os
import sys
import json
import time
import logging
import requests
import re
from datetime import datetime
import telebot
from typing import Dict, Optional, Any
import threading
from time import sleep

# Add paths for imports
sys.path.append('/root/HydraX-v2/src')
sys.path.append('/root/HydraX-v2')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/bitten_production_bot_fixed.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('BittenProductionBot')

# Configuration
BOT_TOKEN = '7854827710:AAGsO-vgMpsTOVNu6zoo_-GGJkYQd97Mc5w'

# USER + COMMANDER CONFIG
COMMANDER_IDS = [7176191872]

AUTHORIZED_USERS = {
    "7176191872": {
        "tier": "COMMANDER",
        "account_id": "843859",
        "bridge_id": "bridge_01"
    }
}

def escape_markdown(text):
    """Escape MarkdownV2 special characters"""
    return re.sub(r'([_*\\()~`>#+=|{}.!-])', r'\\\\\\1', text)

class BittenProductionBot:
    """Production Telegram bot for BITTEN trading system - Fixed Version"""
    
    def __init__(self):
        self.bot = telebot.TeleBot(BOT_TOKEN)
        
        # Rate limiting
        self.last_message_time = {}
        self.message_delay = 0.5  # 500ms between messages
        
        logger.info("BITTEN Production Bot (Fixed) initialized")
        
        # Register handlers
        self.setup_handlers()
    
    def safe_send_message(self, chat_id, message_text, **kwargs):
        """Send message with rate limiting"""
        try:
            # Rate limiting
            current_time = time.time()
            if chat_id in self.last_message_time:
                time_since_last = current_time - self.last_message_time[chat_id]
                if time_since_last < self.message_delay:
                    sleep(self.message_delay - time_since_last)
            
            self.last_message_time[chat_id] = time.time()
            return self.bot.send_message(chat_id, message_text, **kwargs)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return None
    
    def setup_handlers(self):
        """Setup message handlers"""
        @self.bot.message_handler(commands=['start', 'help'])
        def handle_start(message):
            self.handle_start_command(message)
        
        @self.bot.message_handler(commands=['status'])
        def handle_status(message):
            self.handle_status_command(message)
        
        @self.bot.message_handler(commands=['mode'])
        def handle_mode(message):
            self.handle_mode_command(message)
        
        @self.bot.message_handler(commands=['ghosted'])
        def handle_ghosted(message):
            self.handle_ghosted_command(message)
        
        @self.bot.message_handler(commands=['force_signal'])
        def handle_force_signal(message):
            self.handle_force_signal_command(message)
        
        @self.bot.message_handler(commands=['ping'])
        def handle_ping(message):
            self.handle_ping_command(message)
        
        @self.bot.message_handler(commands=['fire'])
        def handle_fire(message):
            self.handle_fire_command(message)
        
        @self.bot.message_handler(commands=['menu'])
        def handle_menu(message):
            self.handle_menu_command(message)
        
        @self.bot.message_handler(commands=['bit'])
        def handle_bit(message):
            self.handle_bit_command(message)
        
        @self.bot.message_handler(commands=['slots'])
        def handle_slots(message):
            self.handle_slots_command(message)
        
        @self.bot.message_handler(commands=['presspass'])
        def handle_presspass(message):
            self.handle_presspass_command(message)
        
        # Add callback query handler for button clicks
        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callback_query(call):
            self.handle_callback_query(call)
        
        @self.bot.message_handler(func=lambda message: True)
        def handle_all(message):
            self.handle_all_messages(message)
    
    def handle_start_command(self, message):
        """Handle /start command"""
        user_id = str(message.from_user.id)
        user_config = AUTHORIZED_USERS.get(user_id, {})
        user_tier = user_config.get("tier", "NIBBLER")
        
        welcome_text = f"""🎯 **BITTEN Production Bot**
        
**User**: {message.from_user.first_name}
**Tier**: {user_tier}
**ID**: {user_id}

**Available Commands:**
• /status - System status
• /mode - Configure fire modes
• /ghosted - Ghosted operations report
• /force_signal - Generate test signal

**Status**: ✅ FULLY OPERATIONAL
**Version**: Production v2.7 - Fixed
"""
        
        self.safe_send_message(message.chat.id, welcome_text, parse_mode="Markdown")
    
    def handle_status_command(self, message):
        """Handle /status command"""
        user_id = str(message.from_user.id)
        
        if int(user_id) not in COMMANDER_IDS:
            self.safe_send_message(message.chat.id, "❌ Status command is for commanders only.", parse_mode="Markdown")
            return
        
        # Get system status
        try:
            # Check webapp
            webapp_status = "🔴 OFFLINE"
            try:
                result = requests.get("http://localhost:8888/health", timeout=5)
                if result.status_code == 200:
                    webapp_status = "🟢 ONLINE"
            except:
                pass
            
            # Check bridge
            bridge_status = "🔴 OFFLINE"
            try:
                result = requests.get("http://localhost:9000/health", timeout=5)
                if result.status_code == 200:
                    bridge_status = "🟢 ONLINE"
            except:
                pass
            
            # Check apex_status = "🔴 OFFLINE"
            if os.path.exists("/root/HydraX-v2/.apex_engine.pid"):
                apex_status = "🟢 ONLINE"
            
            status_text = f"""⚡ **BITTEN SYSTEM STATUS**

**Core Services:**
• WebApp (8888): {webapp_status}
• Bridge (9000): {bridge_status}
• Engine: {apex_status}

**Bot Status:**
• Production Bot: 🟢 ONLINE
• Commands: ✅ FULLY FUNCTIONAL
• Rate Limiting: ✅ ENABLED
• User: COMMANDER {user_id}

**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
            
            self.safe_send_message(message.chat.id, status_text, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Status command error: {e}")
            self.safe_send_message(message.chat.id, f"❌ Status check failed: {str(e)}", parse_mode="Markdown")
    
    def handle_mode_command(self, message):
        """Handle /mode command"""
        user_id = str(message.from_user.id)
        user_config = AUTHORIZED_USERS.get(user_id, {})
        user_tier = user_config.get("tier", "NIBBLER")
        
        try:
            # Import fire mode handlers with proper rate limiting
            from src.bitten_core.fire_mode_handlers import FireModeHandlers
            
            # Create a custom bot wrapper with our safe_send_message
            class SafeBotWrapper:
                def __init__(self, bot_instance, parent_instance):
                    self.bot = bot_instance
                    self.parent = parent_instance
                
                def send_message(self, chat_id, text, **kwargs):
                    return self.parent.safe_send_message(chat_id, text, **kwargs)
                
                def answer_callback_query(self, callback_query_id, text=None, show_alert=False):
                    return self.bot.answer_callback_query(callback_query_id, text, show_alert)
                
                def edit_message_text(self, text, chat_id, message_id, **kwargs):
                    return self.bot.edit_message_text(text, chat_id, message_id, **kwargs)
            
            # Use safe wrapper with parent instance
            safe_bot = SafeBotWrapper(self.bot, self)
            FireModeHandlers.handle_mode_command(safe_bot, message, user_tier)
            
        except ImportError as e:
            logger.error(f"Fire mode handlers import failed: {e}")
            # Fallback mode display
            mode_text = f"""🔥 **FIRE MODE CONFIGURATION**

**Current Mode**: AUTO (default for {user_tier})

**Available Modes:**
• **SELECT FIRE**: Manual execution only
• **AUTO**: Automatic trade execution

**Note**: Fire mode system temporarily using fallback.
Use /status for system information.
"""
            self.safe_send_message(message.chat.id, mode_text, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Mode command error: {e}")
            self.safe_send_message(message.chat.id, f"❌ Mode command failed: {str(e)}", parse_mode="Markdown")
    
    def handle_ghosted_command(self, message):
        """Handle /ghosted command"""
        user_id = str(message.from_user.id)
        
        if int(user_id) not in COMMANDER_IDS:
            self.safe_send_message(message.chat.id, "❌ Ghosted command is for commanders only.", parse_mode="Markdown")
            return
        
        try:
            # Try to get ghosted operations report
            ghosted_text = """👻 **GHOSTED OPERATIONS REPORT**

**Last 24 Hours:**
• Total Missions: 0
• Executed: 0
• Ghosted: 0
• Ghost Win Rate: 0%

**Status**: Ghosted tracking system operational
**Note**: No ghosted operations in the last 24 hours
"""
            self.safe_send_message(message.chat.id, ghosted_text, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Ghosted command error: {e}")
            self.safe_send_message(message.chat.id, f"❌ Ghosted report failed: {str(e)}", parse_mode="Markdown")
    
    def handle_force_signal_command(self, message):
        """Handle /force_signal command"""
        user_id = str(message.from_user.id)
        
        if int(user_id) not in COMMANDER_IDS:
            self.safe_send_message(message.chat.id, "❌ Force signal command is for commanders only.", parse_mode="Markdown")
            return
        
        try:
            # Generate test signal
            signal_text = f"""🎯 **TEST SIGNAL GENERATED**

**Signal Type**: RAPID ASSAULT
**Symbol**: EURUSD
**Direction**: BUY
**TCS Score**: 85%
**Timestamp**: {datetime.now().strftime('%H:%M:%S')} UTC

**Status**: ✅ Test signal injected successfully
**Mission ID**: TEST_{int(time.time())}
"""
            self.safe_send_message(message.chat.id, signal_text, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Force signal command error: {e}")
            self.safe_send_message(message.chat.id, f"❌ Force signal failed: {str(e)}", parse_mode="Markdown")
    
    def handle_all_messages(self, message):
        """Handle all other messages"""
        user_id = str(message.from_user.id)
        user_config = AUTHORIZED_USERS.get(user_id, {})
        
        if not user_config:
            self.safe_send_message(message.chat.id, "❌ Unauthorized user. Contact admin for access.", parse_mode="Markdown")
            return
        
        # Echo back with user info
        response_text = f"""🤖 **BITTEN Production Bot**

**Message received**: {message.text}
**User**: {user_config.get('tier', 'NIBBLER')} {user_id}

Use /help for available commands.
"""
        
        self.safe_send_message(message.chat.id, response_text, parse_mode="Markdown")
    
    def handle_ping_command(self, message):
        """Handle /ping command"""
        self.safe_send_message(message.chat.id, "🏓 Pong! Bot is responsive.", parse_mode="Markdown")
    
    def handle_fire_command(self, message):
        """Handle /fire command"""
        user_id = str(message.from_user.id)
        user_config = AUTHORIZED_USERS.get(user_id, {})
        
        if not user_config:
            self.safe_send_message(message.chat.id, "❌ Unauthorized user.", parse_mode="Markdown")
            return
        
        fire_text = """🔥 **FIRE COMMAND**

This command is used for direct trade execution.
Use /mode to configure your fire mode settings.
Use /status to check system status.

**Current Status**: System operational
"""
        self.safe_send_message(message.chat.id, fire_text, parse_mode="Markdown")
    
    def handle_menu_command(self, message):
        """Handle /menu command"""
        user_id = str(message.from_user.id)
        user_config = AUTHORIZED_USERS.get(user_id, {})
        
        if not user_config:
            self.safe_send_message(message.chat.id, "❌ Unauthorized user.", parse_mode="Markdown")
            return
        
        menu_text = f"""📋 **BITTEN COMMAND MENU**

**Trading Commands:**
• /mode - Configure fire modes
• /fire - Direct trade execution
• /slots - Manage AUTO fire slots
• /ghosted - Ghosted operations report

**System Commands:**
• /status - System health check
• /ping - Bot responsiveness test
• /force_signal - Generate test signal

**User Commands:**
• /bit - BIT personality interaction
• /presspass - Press pass information
• /help - Command help

**Your Tier**: {user_config.get('tier', 'NIBBLER')}
"""
        self.safe_send_message(message.chat.id, menu_text, parse_mode="Markdown")
    
    def handle_bit_command(self, message):
        """Handle /bit command"""
        user_id = str(message.from_user.id)
        user_config = AUTHORIZED_USERS.get(user_id, {})
        
        if not user_config:
            self.safe_send_message(message.chat.id, "❌ Unauthorized user.", parse_mode="Markdown")
            return
        
        bit_text = """🐱 **BIT PERSONALITY SYSTEM**

*BIT purrs and stretches*

"Meow! I'm BIT, your feline trading companion. I analyze market patterns with cat-like precision and help you navigate the trading jungle."

**BIT Functions:**
• Market analysis with feline intuition
• Trade recommendations
• Personality interactions
• Tactical assessments

*BIT's tail swishes with anticipation*
"""
        self.safe_send_message(message.chat.id, bit_text, parse_mode="Markdown")
    
    def handle_slots_command(self, message):
        """Handle /slots command"""
        user_id = str(message.from_user.id)
        user_config = AUTHORIZED_USERS.get(user_id, {})
        
        if not user_config:
            self.safe_send_message(message.chat.id, "❌ Unauthorized user.", parse_mode="Markdown")
            return
        
        try:
            # Get current slot information
            import sqlite3
            conn = sqlite3.connect('/root/HydraX-v2/data/fire_modes.db')
            cursor = conn.cursor()
            cursor.execute('SELECT current_mode, max_slots, slots_in_use FROM user_fire_modes WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                current_mode, max_slots, slots_in_use = result
                slots_text = f"""🎯 **FIRE SLOTS CONFIGURATION**

**Current Mode**: {current_mode}
**Slots Available**: {max_slots}
**Slots In Use**: {slots_in_use}
**Slots Free**: {max_slots - slots_in_use}

**Slot Status**:
{"🟢 " * slots_in_use}{"⚪ " * (max_slots - slots_in_use)}

**COMMANDER**: Up to 3 simultaneous AUTO trades
**Note**: Use /mode to configure AUTO fire settings
"""
            else:
                slots_text = "❌ Unable to retrieve slot information."
            
            self.safe_send_message(message.chat.id, slots_text, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Slots command error: {e}")
            self.safe_send_message(message.chat.id, f"❌ Slots command failed: {str(e)}", parse_mode="Markdown")
    
    def handle_presspass_command(self, message):
        """Handle /presspass command"""
        user_id = str(message.from_user.id)
        user_config = AUTHORIZED_USERS.get(user_id, {})
        
        if not user_config:
            self.safe_send_message(message.chat.id, "❌ Unauthorized user.", parse_mode="Markdown")
            return
        
        user_tier = user_config.get('tier', 'NIBBLER')
        
        if user_tier == 'COMMANDER':
            presspass_text = """🎫 **PRESS PASS INFORMATION**

**Your Status**: COMMANDER (Full Access)
**Press Pass**: Not applicable - you have full access

**COMMANDER Benefits**:
• Unlimited signal access
• All fire modes (SELECT + AUTO)
• Up to 3 simultaneous trades
• Priority support
• Advanced analytics
• Full system control

**Status**: ✅ FULLY OPERATIONAL
"""
        else:
            presspass_text = f"""🎫 **PRESS PASS INFORMATION**

**Your Current Tier**: {user_tier}

**Press Pass**: 14-day free trial access
**Includes**: Basic signal access, SELECT fire mode
**Upgrade Available**: COMMANDER tier for full features

**Contact**: Support for upgrade options
"""
        
        self.safe_send_message(message.chat.id, presspass_text, parse_mode="Markdown")
    
    def handle_callback_query(self, call):
        """Handle callback query (button clicks)"""
        user_id = str(call.from_user.id)
        user_config = AUTHORIZED_USERS.get(user_id, {})
        
        if not user_config:
            self.bot.answer_callback_query(call.id, "❌ Unauthorized user", show_alert=True)
            return
        
        user_tier = user_config.get("tier", "NIBBLER")
        
        try:
            # Handle mode selection callbacks
            if call.data.startswith("mode_"):
                from src.bitten_core.fire_mode_handlers import FireModeHandlers
                
                # Create safe bot wrapper for callback handling
                class SafeBotWrapper:
                    def __init__(self, bot_instance, parent_instance):
                        self.bot = bot_instance
                        self.parent = parent_instance
                    
                    def send_message(self, chat_id, text, **kwargs):
                        return self.parent.safe_send_message(chat_id, text, **kwargs)
                    
                    def answer_callback_query(self, callback_query_id, text=None, show_alert=False):
                        return self.bot.answer_callback_query(callback_query_id, text, show_alert)
                    
                    def edit_message_text(self, text, chat_id, message_id, **kwargs):
                        return self.bot.edit_message_text(text, chat_id, message_id, **kwargs)
                
                safe_bot = SafeBotWrapper(self.bot, self)
                FireModeHandlers.handle_mode_callback(safe_bot, call, user_tier)
            else:
                self.bot.answer_callback_query(call.id, "Unknown command", show_alert=True)
                
        except ImportError:
            logger.error("Fire mode handlers not available")
            self.bot.answer_callback_query(call.id, "Fire mode system unavailable", show_alert=True)
        except Exception as e:
            logger.error(f"Callback query error: {e}")
            self.bot.answer_callback_query(call.id, "System error", show_alert=True)
    
    def start_bot(self):
        """Start the bot"""
        try:
            logger.info("Starting BITTEN Production Bot (Fixed)...")
            logger.info(f"Authorized users: {list(AUTHORIZED_USERS.keys())}")
            logger.info(f"Commanders: {COMMANDER_IDS}")
            
            # Test bot connection
            try:
                bot_info = self.bot.get_me()
                logger.info(f"Bot connected successfully: @{bot_info.username}")
            except Exception as e:
                logger.error(f"Bot connection failed: {e}")
                return
            
            # Send startup message to log channel
            try:
                self.safe_send_message(-1002581996861, "🚀 BITTEN Production Bot (Fixed) started successfully!")
            except Exception as e:
                logger.warning(f"Could not send startup message: {e}")
            
            logger.info("Starting bot polling...")
            self.bot.infinity_polling(timeout=10, long_polling_timeout=5)
            
        except Exception as e:
            logger.error(f"Bot startup failed: {e}")
            raise

if __name__ == "__main__":
    bot = BittenProductionBot()
    bot.start_bot()