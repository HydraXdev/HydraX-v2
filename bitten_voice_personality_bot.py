#!/usr/bin/env python3
"""
🎭 BITTEN VOICE & PERSONALITY BOT
Dedicated bot for Drill Sergeant, NEXUS, DOC, OBSERVER personalities
Separate from trading signals - handles all voice and character interactions
(ATHENA moved to dedicated athena_mission_bot.py)

TOKEN: 8103700393:AAEK3RjTGHHYyy_X1Uc9FUuUoRcLuzYZe4k
"""

import os
import sys
import json
import time
import logging
import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import telebot
from telebot import types

# Add paths for imports
sys.path.append('/root/HydraX-v2/src')
sys.path.append('/root/HydraX-v2')

# Import configuration loader
from config_loader import get_voice_bot_token

# Import personality systems
try:
    from src.bitten_core.voice.unified_personality_orchestrator import unified_orchestrator
    # from src.bitten_core.voice.athena_personality import AthenaPersonality  # REMOVED - Moved to dedicated bot
    from src.bitten_core.voice.nexus_personality import NexusPersonality  
    from src.bitten_core.voice.doc_personality import DocPersonality
    from src.bitten_core.intel_bot_personalities import IntelBotPersonalities, BotPersonality
    from src.bitten_core.daily_drill_report import DailyDrillReportSystem
    PERSONALITY_SYSTEMS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Personality systems not available: {e}")
    PERSONALITY_SYSTEMS_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/bitten_voice_personality_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('BittenVoiceBot')

# VOICE/PERSONALITY BOT TOKEN (separate from trading bot) - Load from environment
VOICE_BOT_TOKEN = get_voice_bot_token()

class BittenVoicePersonalityBot:
    """
    🎭 Dedicated Voice & Personality Bot
    Handles all character interactions separate from trading signals
    """
    
    def __init__(self):
        self.bot = telebot.TeleBot(VOICE_BOT_TOKEN)
        self.setup_personality_systems()
        self.setup_handlers()
        
        # User session tracking
        self.user_sessions = {}
        self.active_personalities = {}
        
        logger.info("🎭 BITTEN Voice & Personality Bot initialized")
        logger.info(f"🤖 Token: {VOICE_BOT_TOKEN[:20]}...")
    
    def setup_personality_systems(self):
        """Initialize all personality systems"""
        try:
            if PERSONALITY_SYSTEMS_AVAILABLE:
                # Core personalities (ATHENA moved to dedicated mission bot)
                # self.athena = AthenaPersonality()  # REMOVED - Now in athena_mission_bot.py
                self.nexus = NexusPersonality()
                self.doc = DocPersonality()
                
                # Intel bot personalities
                self.intel_bots = IntelBotPersonalities()
                
                # Drill report system
                self.drill_system = DailyDrillReportSystem()
                
                # Unified orchestrator
                self.orchestrator = unified_orchestrator
                
                logger.info("✅ All personality systems loaded")
            else:
                self.setup_fallback_personalities()
                logger.info("⚠️ Using fallback personality system")
                
        except Exception as e:
            logger.error(f"Error setting up personality systems: {e}")
            self.setup_fallback_personalities()
    
    def setup_fallback_personalities(self):
        """Fallback personality responses"""
        self.fallback_responses = {
            # 'ATHENA': "🏛️ ATHENA: Strategic analysis in progress...",  # REMOVED - Dedicated bot
            'DRILL': "🪖 DRILL SERGEANT: Stay focused, recruit!",
            'NEXUS': "📡 NEXUS: Monitoring all frequencies...",
            'DOC': "🩺 DOC: Protecting your capital...",
            'OBSERVER': "👁️ OBSERVER: Watching market patterns..."
        }
    
    def setup_handlers(self):
        """Setup bot command handlers"""
        
        # ATHENA REMOVED - Now handled by dedicated athena_mission_bot.py
        # ATHENA strategic commander handlers moved to dedicated bot
        
        @self.bot.message_handler(commands=['drill'])
        def handle_drill(message):
            """Drill Sergeant personality"""
            user_id = str(message.from_user.id)
            self.active_personalities[user_id] = 'DRILL'
            
            if PERSONALITY_SYSTEMS_AVAILABLE and hasattr(self, 'drill_system'):
                report = self.drill_system.generate_drill_report(user_id)
                if hasattr(report, 'message'):
                    response = report.message
                else:
                    response = str(report) if report else "🪖 DRILL SERGEANT: No report available!"
            else:
                response = self.fallback_responses['DRILL']
                
            self.bot.reply_to(message, f"🪖 **DRILL SERGEANT ACTIVATED**\n\n{response}")
        
        @self.bot.message_handler(commands=['nexus'])
        def handle_nexus(message):
            """NEXUS recruiter personality"""
            user_id = str(message.from_user.id)
            self.active_personalities[user_id] = 'NEXUS'
            
            if PERSONALITY_SYSTEMS_AVAILABLE and hasattr(self, 'nexus'):
                response = self.nexus.get_celebration_response(
                    'execution_success',
                    {'symbol': 'EURUSD', 'profit_pips': 25}
                )
            else:
                response = self.fallback_responses['NEXUS']
                
            self.bot.reply_to(message, f"📡 **NEXUS ACTIVATED**\n\n{response}")
        
        @self.bot.message_handler(commands=['doc'])
        def handle_doc(message):
            """DOC medic personality"""
            user_id = str(message.from_user.id)
            self.active_personalities[user_id] = 'DOC'
            
            if PERSONALITY_SYSTEMS_AVAILABLE and hasattr(self, 'doc'):
                response = self.doc.get_risk_warning({
                    'risk_level': 'moderate',
                    'account_balance': 10000,
                    'current_risk': 200
                })
            else:
                response = self.fallback_responses['DOC']
                
            self.bot.reply_to(message, f"🩺 **DOC ACTIVATED**\n\n{response}")
        
        @self.bot.message_handler(commands=['observer'])
        def handle_observer(message):
            """OBSERVER market watcher"""
            user_id = str(message.from_user.id)
            self.active_personalities[user_id] = 'OBSERVER'
            
            response = "👁️ **OBSERVER**: Monitoring market patterns and user behavior. All tactical movements logged."
            self.bot.reply_to(message, response)
        
        @self.bot.message_handler(commands=['personalities'])
        def handle_personalities_menu(message):
            """Show all available personalities"""
            keyboard = types.InlineKeyboardMarkup()
            
            keyboard.add(
                # types.InlineKeyboardButton("🏛️ ATHENA", callback_data="personality_athena"),  # REMOVED - Dedicated bot
                types.InlineKeyboardButton("🪖 DRILL", callback_data="personality_drill")
            )
            keyboard.add(
                types.InlineKeyboardButton("📡 NEXUS", callback_data="personality_nexus"),
                types.InlineKeyboardButton("🩺 DOC", callback_data="personality_doc")
            )
            keyboard.add(
                types.InlineKeyboardButton("👁️ OBSERVER", callback_data="personality_observer")
            )
            
            self.bot.reply_to(
                message,
                "🎭 **BITTEN PERSONALITY SELECTION**\n\n"
                "Choose your AI companion:\n"
                "🪖 **DRILL** - Motivational Sergeant\n"
                "📡 **NEXUS** - Recruiter Protocol\n"
                "🩺 **DOC** - Risk Manager\n"
                "👁️ **OBSERVER** - Market Watcher\n\n"
                "📢 **ATHENA** - Strategic Commander now operates via dedicated Mission Bot\n"
                "ATHENA - Strategic Commander now operates via dedicated Mission Bot",
                reply_markup=keyboard
            )
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('personality_'))
        def handle_personality_callback(call):
            """Handle personality selection callbacks"""
            personality = call.data.replace('personality_', '').upper()
            user_id = str(call.from_user.id)
            
            self.active_personalities[user_id] = personality
            
            responses = {
                # 'ATHENA': "🏛️ ATHENA Strategic Commander activated. Ready for tactical analysis.",  # REMOVED - Dedicated bot
                'DRILL': "🪖 DRILL SERGEANT activated. Time to get motivated, recruit!",
                'NEXUS': "📡 NEXUS Recruiter Protocol activated. Ready to celebrate your victories!",
                'DOC': "🩺 DOC Risk Manager activated. Your capital protection is my priority.",
                'OBSERVER': "👁️ OBSERVER activated. All market patterns under surveillance."
            }
            
            self.bot.answer_callback_query(call.id, f"{personality} activated!")
            self.bot.send_message(call.message.chat.id, responses.get(personality, "Personality activated!"))
        
        @self.bot.message_handler(commands=['voice_status'])
        def handle_voice_status(message):
            """Check voice system status"""
            user_id = str(message.from_user.id)
            active = self.active_personalities.get(user_id, 'None')
            
            status = f"🎭 **VOICE SYSTEM STATUS**\n\n"
            status += f"**Active Personality**: {active}\n"
            status += f"**Systems Available**: {'✅' if PERSONALITY_SYSTEMS_AVAILABLE else '❌'}\n"
            status += f"**Available Personalities**: DRILL, NEXUS, DOC, OBSERVER (ATHENA = Dedicated Mission Bot)\n\n"
            status += "Use /personalities to select a different character."
            
            self.bot.reply_to(message, status)
        
        @self.bot.message_handler(func=lambda message: True)
        def handle_personality_chat(message):
            """Handle general chat with active personality"""
            user_id = str(message.from_user.id)
            active_personality = self.active_personalities.get(user_id, 'DRILL')  # Changed default from ATHENA
            
            # Route to appropriate personality
            if active_personality == 'ATHENA':
                response = "🏛️ ATHENA now operates via dedicated Mission Bot. Use /personalities to select an available personality."
            elif active_personality == 'DRILL':
                responses = [
                    "🪖 DRILL SERGEANT: Keep pushing forward, recruit!",
                    "🪖 DRILL SERGEANT: No excuses! Execute the mission!",
                    "🪖 DRILL SERGEANT: Outstanding performance! Keep it up!"
                ]
                response = random.choice(responses)
            elif active_personality == 'NEXUS':
                response = "📡 NEXUS: Message received and processed. Ready for next deployment!"
            elif active_personality == 'DOC':
                response = "🩺 DOC: Your message analyzed for risk factors. Recommend maintaining discipline."
            elif active_personality == 'OBSERVER':
                response = "👁️ OBSERVER: Message logged. Pattern analysis in progress."
            else:
                response = "🎭 No personality active. Use /personalities to select one."
            
            self.bot.reply_to(message, response)
    
    def start_polling(self):
        """Start the bot polling"""
        logger.info("🚀 Starting BITTEN Voice & Personality Bot...")
        logger.info("🎭 Personalities: DRILL, NEXUS, DOC, OBSERVER (ATHENA = Dedicated Mission Bot)")
        logger.info("📱 Commands: /personalities, /drill, /nexus, /doc, /observer")
        
        try:
            self.bot.infinity_polling(timeout=30, long_polling_timeout=30)
        except Exception as e:
            logger.error(f"❌ Bot polling error: {e}")
            time.sleep(5)
            self.start_polling()  # Restart on error

def main():
    """Main entry point"""
    print("🎭 BITTEN VOICE & PERSONALITY BOT")
    print("=" * 50)
    print("🪖 DRILL SERGEANT - Motivational Force")
    print("📡 NEXUS - Recruiter Protocol")
    print("🩺 DOC - Risk Manager")
    print("👁️ OBSERVER - Market Watcher")
    print("📢 ATHENA - Strategic Commander (Dedicated Mission Bot)")
    print("=" * 50)
    
    bot = BittenVoicePersonalityBot()
    bot.start_polling()

if __name__ == "__main__":
    main()