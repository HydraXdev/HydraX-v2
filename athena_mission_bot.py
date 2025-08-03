#!/usr/bin/env python3
"""
🏛️ ATHENA MISSION BOT
Dedicated Telegram bot for ATHENA's tactical mission dispatching
Strategic Commander AI for BITTEN trading signals

Token: 8322305650:AAGtBpEMm759_7gI4m9sg0OJwFhBVjR4pEI
"""

import os
import sys
import json
import time
import logging
import requests
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import telebot
from telebot import types

# Add paths for imports
sys.path.append('/root/HydraX-v2/src')
sys.path.append('/root/HydraX-v2')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/athena_mission_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AthenaMissionBot')

# ATHENA Mission Bot Token
ATHENA_BOT_TOKEN = "8322305650:AAGtBpEMm759_7gI4m9sg0OJwFhBVjR4pEI"

class AthenaMissionBot:
    """
    🏛️ ATHENA - Advanced Tactical Handler for Embedded Neural Analysis
    Dedicated mission dispatch bot with strategic command authority
    """
    
    def __init__(self):
        self.bot = telebot.TeleBot(ATHENA_BOT_TOKEN)
        
        # Import ATHENA personality system
        try:
            from src.bitten_core.personality.athena_personality import AthenaPersonality
            self.athena = AthenaPersonality()
            self.athena_available = True
            logger.info("✅ ATHENA personality system loaded")
        except ImportError as e:
            logger.error(f"❌ Failed to load ATHENA personality: {e}")
            self.athena_available = False
        
        # Mission dispatch settings
        self.authorized_dispatchers = ["7176191872"]  # Commander user
        self.authorized_users = ["7176191872"]  # For backward compatibility
        self.mission_counter = 0
        self.active_missions = {}
        
        # Setup command handlers
        self.setup_handlers()
        
        logger.info("🏛️ ATHENA Mission Bot initialized")
        logger.info(f"⚔️ Strategic Command Authority: ACTIVE")
        logger.info(f"📡 Ready for mission dispatch operations")
    
    def setup_handlers(self):
        """Setup ATHENA mission bot command handlers"""
        
        @self.bot.message_handler(commands=['start'])
        def handle_start(message):
            """ATHENA introduction and status"""
            user_id = str(message.from_user.id)
            
            welcome_msg = """🏛️ **ATHENA COMMAND ACTIVATED**

*Advanced Tactical Handler for Embedded Neural Analysis*

**STATUS**: OPERATIONAL
**AUTHORITY**: Strategic Mission Command
**CLASSIFICATION**: BITTEN Tactical Network

I am ATHENA, your strategic mission commander. I coordinate all tactical operations and provide mission briefings for BITTEN trading signals.

**Available Commands:**
• `/status` - Tactical system status
• `/brief` - Generate sample mission briefing
• `/help` - Command reference

**Mission Authority**: All signal dispatches flow through ATHENA Command.

*Strategic intelligence online. Ready for operations.*"""

            self.bot.send_message(
                message.chat.id, 
                welcome_msg, 
                parse_mode="Markdown"
            )
        
        @self.bot.message_handler(commands=['status'])
        def handle_status(message):
            """ATHENA tactical system status"""
            user_id = str(message.from_user.id)
            
            status_msg = f"""🏛️ **ATHENA TACTICAL STATUS**

**System State**: OPERATIONAL ✅
**Command Authority**: {self.athena.traits['command_authority'] * 100:.0f}%
**Strategic Intelligence**: {self.athena.traits['strategic_intelligence'] * 100:.0f}%
**Mission Counter**: {self.mission_counter}
**Active Missions**: {len(self.active_missions)}

**Personality System**: {'✅ ACTIVE' if self.athena_available else '❌ OFFLINE'}
**Dispatch Authority**: {'✅ AUTHORIZED' if user_id in self.authorized_dispatchers else '⚠️ LIMITED'}

**Last Boot**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

*All tactical systems nominal. Standing by for mission parameters.*"""

            self.bot.send_message(
                message.chat.id,
                status_msg,
                parse_mode="Markdown"
            )
        
        @self.bot.message_handler(commands=['brief'])
        def handle_brief(message):
            """Generate sample mission briefing"""
            user_id = str(message.from_user.id)
            
            if not self.athena_available:
                self.bot.send_message(
                    message.chat.id,
                    "❌ ATHENA personality system offline. Cannot generate briefings."
                )
                return
            
            # Generate sample mission data
            sample_signal = {
                'symbol': 'EURUSD',
                'direction': 'BUY',
                'entry_price': 1.0875,
                'take_profit': 1.0925,
                'stop_loss': 1.0825,
                'tcs_score': 89.5,
                'pattern': 'Institutional Breakout',
                'timeframe': 'M15',
                'signal_id': f'ATHENA_DEMO_{int(time.time())}'
            }
            
            # Get user tier (default to COMMANDER for demo)
            user_tier = "COMMANDER"
            mission_id = f"DEMO_{int(time.time())}"
            
            # Generate ATHENA mission briefing
            briefing = self.athena.get_mission_briefing(sample_signal, user_tier, mission_id)
            
            # Add tactical enhancements for high TCS
            if sample_signal['tcs_score'] > 85:
                tactical_confidence = f"\n\n🎯 **TACTICAL ASSESSMENT**\nIntel confirms {sample_signal['tcs_score']:.1f}% likelihood of mission success.\nStrategic conditions: OPTIMAL"
                briefing += tactical_confidence
            
            self.bot.send_message(
                message.chat.id,
                briefing,
                parse_mode="Markdown"
            )
        
        @self.bot.message_handler(commands=['help'])
        def handle_help(message):
            """ATHENA command reference"""
            help_msg = """🏛️ **ATHENA COMMAND REFERENCE**

**Core Commands:**
• `/start` - Initialize ATHENA interface
• `/status` - System status and authority level
• `/brief` - Generate demo mission briefing
• `/help` - This command reference

**Mission Dispatch:**
• Automatic signal processing from VENOM engine
• Real-time tactical briefings for all signals
• Strategic command authority for COMMANDER tier

**Authority Levels:**
• **COMMANDER**: Full tactical access
• **STANDARD**: Limited briefing access

**Mission Classifications:**
• 🎯 **PRECISION_STRIKE** (1:3 R:R) - High-reward targeting
• ⚡ **RAPID_ASSAULT** (1:2 R:R) - Quick tactical strikes

*ATHENA Command - Strategic Operations Division*"""

            self.bot.send_message(
                message.chat.id,
                help_msg,
                parse_mode="Markdown"
            )
        
        # Add global message handler for mission dispatch integration
        @self.bot.message_handler(func=lambda message: True)
        def handle_all_messages(message):
            """Handle all other messages with ATHENA personality"""
            if not message.text.startswith('/'):
                # ATHENA tactical response to general queries
                response = "🏛️ ATHENA operational. Use `/help` for command reference or await mission parameters."
                self.bot.send_message(message.chat.id, response)
    
    def dispatch_mission_signal(self, signal_data: Dict, user_data: Dict) -> bool:
        """
        Primary method for dispatching mission signals via ATHENA
        This will be called by the signal generation system
        """
        if not self.athena_available:
            logger.error("❌ Cannot dispatch mission: ATHENA personality offline")
            return False
        
        try:
            # Extract signal information
            symbol = signal_data.get('symbol', 'UNKNOWN')
            direction = signal_data.get('direction', 'UNKNOWN')
            tcs_score = signal_data.get('tcs_score', 0)
            signal_id = signal_data.get('signal_id', f'ATHENA_{int(time.time())}')
            
            # Extract user information
            user_id = user_data.get('user_id', 'UNKNOWN')
            user_tier = user_data.get('tier', 'NIBBLER')
            chat_id = user_data.get('chat_id', user_id)
            
            # Generate mission ID
            self.mission_counter += 1
            mission_id = f"ATHENA_{symbol}_{self.mission_counter:04d}"
            
            # Generate ATHENA mission briefing
            briefing = self.athena.get_mission_briefing(signal_data, user_tier, mission_id)
            
            # Add tactical confidence for high TCS signals
            if tcs_score > 85:
                tactical_line = f"\n\n🎯 **INTEL CONFIRMATION**\nTactical analysis confirms {tcs_score:.1f}% mission success probability.\nStrategic advantage: CONFIRMED"
                briefing += tactical_line
            
            # Add signal ID for tracking
            briefing += f"\n\n📋 **MISSION CODE**: `{signal_id}`"
            
            # Create fire button for authorized users
            keyboard = types.InlineKeyboardMarkup()
            if user_tier in ["COMMANDER", "FANG"]:
                fire_button = types.InlineKeyboardButton(
                    "🔥 EXECUTE MISSION", 
                    callback_data=f"fire_{signal_id}"
                )
                keyboard.add(fire_button)
            
            # Dispatch mission via ATHENA bot
            if keyboard.keyboard:  # Has buttons
                self.bot.send_message(
                    chat_id=chat_id,
                    text=briefing,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
            else:
                self.bot.send_message(
                    chat_id=chat_id,
                    text=briefing,
                    parse_mode="Markdown"
                )
            
            # Track active mission
            self.active_missions[signal_id] = {
                'mission_id': mission_id,
                'user_id': user_id,
                'symbol': symbol,
                'direction': direction,
                'tcs_score': tcs_score,
                'dispatched_at': datetime.now(),
                'status': 'DISPATCHED'
            }
            
            logger.info(f"🏛️ Mission dispatched: {mission_id} for {user_id} ({symbol} {direction})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Mission dispatch failed: {e}")
            return False
    
    def send_execution_result(self, signal_id: str, execution_result: Dict, user_data: Dict) -> bool:
        """Send execution results via ATHENA tactical voice"""
        if not self.athena_available:
            return False
        
        try:
            chat_id = user_data.get('chat_id')
            signal_data = self.active_missions.get(signal_id, {})
            
            if execution_result.get('success'):
                response = self.athena.get_execution_success(signal_data, execution_result)
            else:
                response = self.athena.get_execution_failure(signal_data, execution_result)
            
            self.bot.send_message(
                chat_id=chat_id,
                text=f"🏛️ **MISSION UPDATE**\n\n{response}",
                parse_mode="Markdown"
            )
            
            # Update mission status
            if signal_id in self.active_missions:
                self.active_missions[signal_id]['status'] = 'EXECUTED' if execution_result.get('success') else 'FAILED'
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Execution result dispatch failed: {e}")
            return False
    
    def run(self):
        """Start ATHENA mission bot"""
        logger.info("🏛️ ATHENA Mission Bot starting...")
        logger.info("⚔️ Strategic Command Authority: ACTIVE")
        logger.info("📡 Awaiting mission parameters...")
        
        try:
            self.bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            logger.error(f"❌ ATHENA Bot error: {e}")
            time.sleep(5)
            self.run()  # Auto-restart

def main():
    """Launch ATHENA Mission Bot"""
    athena_bot = AthenaMissionBot()
    athena_bot.run()

if __name__ == "__main__":
    main()