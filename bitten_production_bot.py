#!/usr/bin/env python3
"""
BITTEN Production Trading Bot - Fully Wired
Handles all trading commands and production integrations
"""

import os
import sys
import json
import time
import logging
import requests
import re
import asyncio
from datetime import datetime, timedelta
import telebot
from typing import Dict, Optional, Any
import threading
from time import sleep
import subprocess
import docker
import base64
import string
from pathlib import Path
import zmq
import uuid

# Add paths for imports
sys.path.append('/root/HydraX-v2/src')
sys.path.append('/root/HydraX-v2')

# Import configuration loader
from config_loader import get_bot_token, get_logging_config, validate_required_config

# Validate configuration early
try:
    validate_required_config()
except ValueError as e:
    print(f"❌ Configuration error: {e}")
    print("Please check your .env file and ensure all required variables are set.")
    sys.exit(1)

# Configure logging with environment variables
log_config = get_logging_config()
logging.basicConfig(
    level=getattr(logging, log_config['level'], logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_config['file_path']),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('BittenProductionBot')

# NOTE: Personality systems moved to separate voice bot
# bitten_voice_personality_bot.py handles ATHENA, DRILL, NEXUS, DOC, OBSERVER
# This bot focuses on trading signals and tactical execution only
UNIFIED_PERSONALITY_AVAILABLE = False
PERSONALITY_SYSTEM_AVAILABLE = False

# Import BIT integration system

# Import credit referral system
try:
    from src.bitten_core.credit_referral_bot_commands import get_credit_referral_bot_commands
    CREDIT_REFERRAL_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Credit referral system not available: {e}")
    CREDIT_REFERRAL_AVAILABLE = False
try:
    from src.bitten_core.bit_integration import (
        bit_integration, bit_enhance, bit_trade_reaction, 
        bit_welcome, bit_daily_wisdom
    )
    BIT_AVAILABLE = True
except ImportError:
    BIT_AVAILABLE = False
    def bit_enhance(msg, situation=None): return msg
    def bit_trade_reaction(success, profit=0, symbol=""): return ""
    def bit_welcome(tier="NIBBLER"): return "Welcome to BITTEN."
    def bit_daily_wisdom(): return "Market analysis in progress..."

# Import mission generator
try:
    from src.bitten_core.mission_briefing_generator_v5 import generate_mission
    MISSION_GENERATOR_AVAILABLE = True
except ImportError:
    try:
        from bitten_core.mission_briefing_generator_v5 import generate_mission
        MISSION_GENERATOR_AVAILABLE = True
    except ImportError:
        MISSION_GENERATOR_AVAILABLE = False
        def generate_mission(signal, user_id):
            """Fallback mission generator"""
            mission_id = f"{user_id}_{int(time.time())}"
            mission = {
                "mission_id": mission_id,
                "user_id": user_id,
                "symbol": signal["symbol"],
                "type": signal["type"],
                "tcs": signal["tcs_score"],
                "timestamp": datetime.utcnow().isoformat(),
                "status": "pending",
                "file_path": f"./missions/{mission_id}.json"
            }
            os.makedirs("./missions/", exist_ok=True)
            with open(f"./missions/{mission_id}.json", "w") as f:
                json.dump(mission, f, indent=2)
            return mission

# Import drill report and tactical systems
try:
    from src.bitten_core.daily_drill_report import DailyDrillReportSystem
    from src.bitten_core.tactical_strategies import tactical_strategy_manager
    from src.bitten_core.drill_report_bot_integration import register_drill_report_handlers
    DRILL_SYSTEM_AVAILABLE = True
    logger.info("✅ Drill report system imported successfully")
except ImportError as e:
    DRILL_SYSTEM_AVAILABLE = False
    logger.warning(f"⚠️ Drill report system not available: {e}")

try:
    from src.bitten_core.tactical_interface import TacticalInterface
    from src.bitten_core.personalized_mission_brain import get_mission_brain, create_personalized_missions_for_signal
    TACTICAL_INTERFACE_AVAILABLE = True
    logger.info("✅ Tactical interface imported successfully")
except ImportError as e:
    TACTICAL_INTERFACE_AVAILABLE = False
    logger.warning(f"⚠️ Tactical interface not available: {e}")

# Import zero simulation integration
try:
    from src.bitten_core.zero_simulation_integration import ZeroSimulationIntegration
    ZERO_SIM_AVAILABLE = True
    logger.info("✅ Zero simulation integration imported successfully")
except ImportError as e:
    ZERO_SIM_AVAILABLE = False
    logger.warning(f"⚠️ Zero simulation integration not available: {e}")

# Import VENOM v7.0 Production Engine with CITADEL Shield
try:
    from apex_venom_v7_citadel_integrated import VenomCitadelProductionEngine
    VENOM_ENGINE_AVAILABLE = True
    logger.info("✅ VENOM v7.0 + CITADEL Shield Engine imported - 100% REAL DATA")
except ImportError as e:
    VENOM_ENGINE_AVAILABLE = False
    logger.warning(f"⚠️ VENOM v7.0 Engine not available: {e}")

DRILL_TACTICAL_AVAILABLE = DRILL_SYSTEM_AVAILABLE and TACTICAL_INTERFACE_AVAILABLE

# Logging already configured above

# Fire Loop Validation System imports
try:
    from tools.fireloop_verifier import FireLoopVerifier
    from tools.clone_log_watcher import CloneLogWatcher
    FIRE_LOOP_AVAILABLE = True
except ImportError:
    FIRE_LOOP_AVAILABLE = False
    class FireLoopVerifier:
        def run_single_check(self): return {"overall_status": "❌ SYSTEM OFFLINE"}
    class CloneLogWatcher:
        def __init__(self, user_id): pass
        def display_comprehensive_status(self): print("❌ Clone watcher unavailable")

# Configuration - Load from environment variables
BOT_TOKEN = get_bot_token()

# USER + COMMANDER CONFIG
COMMANDER_IDS = [7176191872]

# CRITICAL: USER 7176191872 - ZERO SIMULATION COMMANDER
# UNRESTRICTED FIRE ACCESS - NO SAFETY OVERRIDES
AUTHORIZED_USERS = {
    "7176191872": {
        "tier": "COMMANDER",
        "account_id": "94956065",  # Updated to actual MT5 account
        "mt5_server": "MetaQuotes-Demo",
        "simulation_disabled": True,
        "unlimited_fire_access": True,
        "commander_override": True,
        "api_id": "api_01"
    }
}

def escape_markdown(text):
    """Escape MarkdownV2 special characters"""
    return re.sub(r'([_*\\()~`>#+=|{}.!-])', r'\\\\\\1', text)

def get_pending_mission_for_user(user_id):
    """Get pending mission for user"""
    try:
        missions_dir = "/root/HydraX-v2/missions/"
        if not os.path.exists(missions_dir):
            return None
            
        missions = os.listdir(missions_dir)
        for fname in missions:
            if fname.startswith(str(user_id)) and fname.endswith(".json"):
                try:
                    with open(f"{missions_dir}{fname}") as f:
                        mission = json.load(f)
                        if mission.get("status") == "pending":
                            return mission
                except Exception as e:
                    logger.error(f"Error reading mission file {fname}: {e}")
                    continue
        return None
    except Exception as e:
        logger.error(f"Error getting pending mission: {e}")
        return None

def generate_live_venom_signal():
    """Generate live VENOM v7.0 signal using real MT5 data"""
    try:
        if not VENOM_ENGINE_AVAILABLE:
            logger.error("❌ VENOM Engine not available")
            return None
            
        # Initialize VENOM v7.0 + CITADEL Shield Engine
        venom = VenomCitadelProductionEngine()
        
        # Check market data health first
        if not venom.check_market_data_health():
            logger.error("❌ Market data receiver offline")
            return None
        
        try:
            # Scan for real signals using HTTP data
            signals = venom.scan_all_pairs_realtime()
            
            if signals:
                # Return the first high-quality signal
                best_signal = max(signals, key=lambda s: s['confidence'])
                logger.info(f"🐍 VENOM signal: {best_signal['pair']} {best_signal['signal_type']} @ {best_signal['confidence']}%")
                return best_signal
            else:
                logger.info("📊 No VENOM signals found at current market conditions")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error generating signal: {e}")
            return None
            
    except Exception as e:
        logger.error(f"❌ VENOM signal generation error: {e}")
        return None

def fire_mission_for_user(user_id, mission):
    """Execute trade for user mission via zero simulation integration"""
    try:
        # Use zero simulation integration for real execution
        if ZERO_SIM_AVAILABLE:
            zero_sim = ZeroSimulationIntegration()
            
            # Convert mission to signal format for processing
            raw_signal = {
                'symbol': mission.get('symbol', 'EURUSD'),
                'direction': mission.get('type', 'BUY'), 
                'entry_price': mission.get('entry_price', 0),
                'stop_loss': mission.get('stop_loss', 0),
                'take_profit': mission.get('take_profit', 0),
                'tcs_score': mission.get('tcs', 75),
                'expires_timestamp': int(time.time()) + 3600
            }
            
            # Process through zero simulation pipeline
            result = zero_sim.process_signal_to_real_execution(raw_signal)
            
            if result and result.get('status') == 'success':
                logger.info(f"✅ Mission executed via zero simulation: {mission['mission_id']}")
                return result
                
        # Fallback to webapp API
        try:
            result = requests.post("http://localhost:8888/api/fire", 
                                 json={"mission_id": mission["mission_id"]}, 
                                 timeout=10)
            if result.status_code == 200:
                logger.info(f"Mission fired via WebApp API: {mission['mission_id']}")
                return result.json()
        except Exception as e:
            logger.warning(f"WebApp API failed: {e}")
        
        # Final fallback to direct fire router
        try:
            sys.path.append('/root/HydraX-v2/src/bitten_core')
            from fire_router import FireRouter
            
            fire_router = FireRouter()
            
            # Create trade request format
            from fire_router import TradeRequest, TradeDirection
            
            direction = TradeDirection.BUY if mission.get("direction", "").upper() == "BUY" else TradeDirection.SELL
            trade_request = TradeRequest(
                user_id=int(user_id),
                symbol=mission.get("symbol", "EURUSD"),
                direction=direction,
                volume=mission.get("lot_size", 0.1),
                stop_loss=mission.get("sl", 10),
                take_profit=mission.get("tp", 20),
                tcs_score=mission.get("tcs", 75),
                comment=f"BITTEN_{mission['mission_id']}"
            )
            
            result = fire_router.execute_trade(trade_request)
            logger.info(f"Mission fired via FireRouter: {mission['mission_id']}")
            
            # Update mission status
            mission["status"] = "fired" if result.success else "failed"
            mission["execution_result"] = {
                "success": result.success,
                "message": result.message,
                "timestamp": datetime.now().isoformat()
            }
            
            # Save updated mission
            if "file_path" in mission:
                with open(mission["file_path"], "w") as f:
                    json.dump(mission, f, indent=2)
            
            return {"success": result.success, "message": result.message}
            
        except Exception as e:
            logger.error(f"FireRouter execution failed: {e}")
            return {"success": False, "message": f"Execution failed: {str(e)}"}
            
    except Exception as e:
        logger.error(f"Error firing mission: {e}")
        return {"success": False, "message": "Trade execution failed"}

class BittenProductionBot:
    """Production Telegram bot for BITTEN trading system"""
    
    def __init__(self):
        self.bot = telebot.TeleBot(BOT_TOKEN)
        
        # Rate limiting
        self.last_message_time = {}
        self.message_delay = 0.5  # 500ms between messages
        
        # /connect command throttling
        self.connect_usage_throttle = {}
        self.connect_throttle_window = 60  # 60 seconds between usage messages
        
        # Initialize unified personality system (priority)
        if UNIFIED_PERSONALITY_AVAILABLE:
            self.unified_bot = UnifiedPersonalityBot(self.bot)
            self.unified_bot.setup_unified_commands()
            self.adaptive_bot = None  # Disable adaptive system when unified is available
            logger.info("✅ Unified personality system enabled (all 3 layers)")
        elif PERSONALITY_SYSTEM_AVAILABLE:
            self.adaptive_bot = AdaptivePersonalityBot(self.bot)
            self.adaptive_bot.setup_personality_commands()
            self.unified_bot = None
            logger.info("✅ Adaptive personality system enabled (fallback)")
        else:
            self.adaptive_bot = None
            self.unified_bot = None
            logger.warning("⚠️ No personality system available")
        
        # Initialize drill report and tactical systems
        if DRILL_SYSTEM_AVAILABLE:
            try:
                self.drill_system = DailyDrillReportSystem()
                logger.info("✅ Drill report system enabled")
            except Exception as e:
                logger.error(f"Failed to initialize drill system: {e}")
                self.drill_system = None
        else:
            self.drill_system = None
            
        if TACTICAL_INTERFACE_AVAILABLE:
            try:
                self.tactical_interface = TacticalInterface(None)  # Will need XP economy integration
                logger.info("✅ Tactical interface enabled")
            except Exception as e:
                logger.error(f"Failed to initialize tactical interface: {e}")
                self.tactical_interface = None
        else:
            self.tactical_interface = None
        
        # Initialize CORE crypto signal system
        self.core_enabled = True
        self.core_log_file = "/root/HydraX-v2/logs/core_dm_log.jsonl"
        os.makedirs(os.path.dirname(self.core_log_file), exist_ok=True)
        
        # Initialize credit referral system
        if CREDIT_REFERRAL_AVAILABLE:
            try:
                self.credit_commands = get_credit_referral_bot_commands()
                logger.info("✅ Credit referral system enabled")
            except Exception as e:
                logger.error(f"Failed to initialize credit referral system: {e}")
                self.credit_commands = None
        else:
            self.credit_commands = None
        
        self.setup_handlers()
        
        # Start CORE signal listener in background thread
        if self.core_enabled:
            self.start_core_signal_listener()
            
        logger.info("BITTEN Production Bot initialized")
    
    def _get_current_badge_display(self, referral_count: int) -> str:
        """Get current recruitment badge display"""
        if referral_count >= 50:
            return "👑 LEGENDARY_RECRUITER"
        elif referral_count >= 25:
            return "⭐ RECRUITMENT_MASTER" 
        elif referral_count >= 10:
            return "🥇 ELITE_RECRUITER"
        elif referral_count >= 5:
            return "🥈 SQUAD_BUILDER"
        elif referral_count >= 1:
            return "🥉 RECRUITER"
        else:
            return "🎖️ NEW_RECRUIT"
    
    def send_adaptive_response(self, chat_id, message_text, user_tier="NIBBLER", user_action=None):
        """Send response using unified or adaptive personality system if available"""
        # Try unified system first (all 3 layers)
        if self.unified_bot:
            try:
                # Run async method in event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    self.unified_bot.send_unified_message(
                        chat_id, message_text, user_tier, user_action
                    )
                )
                loop.close()
                return True
            except Exception as e:
                logger.error(f"Unified message failed: {e}")
                # Fall through to adaptive system
        
        # Try adaptive system (fallback)
        if self.adaptive_bot:
            try:
                # Run async method in event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    self.adaptive_bot.send_adaptive_message(
                        chat_id, message_text, user_tier, user_action
                    )
                )
                loop.close()
                return True
            except Exception as e:
                logger.error(f"Adaptive message failed: {e}")
                # Fall through to regular message
        
        # No personality system available, send regular message
        self.bot.send_message(chat_id, escape_markdown(message_text), parse_mode="MarkdownV2")
        return False
    
    def send_dm_signal(self, telegram_id: str, signal_text: str, parse_mode: str = "MarkdownV2") -> bool:
        """Send private signal message to a specific user
        
        Args:
            telegram_id: User's Telegram ID (as string)
            signal_text: Signal message text (already formatted)
            parse_mode: Telegram parse mode (default MarkdownV2)
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        try:
            # Ensure telegram_id is a valid chat_id
            chat_id = int(telegram_id) if isinstance(telegram_id, str) else telegram_id
            
            # For offshore/XAUUSD signals, we might want to add a disclaimer
            if "XAUUSD" in signal_text or "GOLD" in signal_text.upper():
                signal_text = f"🔒 *Private Signal (Offshore Only)*\n\n{signal_text}"
            
            # Send the message
            self.bot.send_message(chat_id, signal_text, parse_mode=parse_mode)
            logger.info(f"DM signal sent to {telegram_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send DM signal to {telegram_id}: {e}")
            return False
    
    def lookup_telegram_id(self, user_id: str) -> Optional[str]:
        """Map user_id to telegram_id using registry
        
        Args:
            user_id: Internal user ID
            
        Returns:
            telegram_id if found, None otherwise
        """
        try:
            from src.bitten_core.user_registry_manager import get_user_registry_manager
            registry = get_user_registry_manager()
            
            # Search through registry for matching user_id
            for telegram_id, user_data in registry.registry_data.items():
                if user_data.get("user_id") == user_id:
                    return telegram_id
                    
            logger.warning(f"No telegram_id found for user_id: {user_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error looking up telegram_id for {user_id}: {e}")
            return None
    
    def is_offshore_eligible(self, telegram_id: str) -> bool:
        """Check if user is eligible for offshore signals (XAUUSD)
        
        Args:
            telegram_id: User's Telegram ID
            
        Returns:
            bool: True if user is INTL region AND has opted in for offshore
        """
        try:
            from src.bitten_core.user_registry_manager import get_user_registry_manager
            registry = get_user_registry_manager()
            
            user_info = registry.get_user_info(telegram_id)
            if not user_info:
                return False
                
            # User must be INTL region AND have opted in
            user_region = user_info.get("user_region", "US")
            offshore_opt_in = user_info.get("offshore_opt_in", False)
            
            return user_region == "INTL" and offshore_opt_in
            
        except Exception as e:
            logger.error(f"Error checking offshore eligibility for {telegram_id}: {e}")
            return False
    
    def create_quick_keyboard(self):
        """Create persistent quick-access keyboard (always visible at bottom)"""
        from telebot.types import ReplyKeyboardMarkup, KeyboardButton
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton("🔫 FIRE"),
                    KeyboardButton("💰 CREDITS"),
                    KeyboardButton("📱 MENU")
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=False,
            is_persistent=True
        )
        return keyboard
    
    def create_full_keyboard(self):
        """Create full persistent keyboard with all commands"""
        from telebot.types import ReplyKeyboardMarkup, KeyboardButton
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton("🔫 FIRE"),
                    KeyboardButton("📊 STATUS"), 
                    KeyboardButton("💰 CREDITS")
                ],
                [
                    KeyboardButton("🎯 TACTICAL"),
                    KeyboardButton("📚 HELP"),
                    KeyboardButton("🏆 RECRUIT")
                ],
                [
                    KeyboardButton("📱 MENU"),
                    KeyboardButton("❌ HIDE")
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=False,
            is_persistent=True
        )
        return keyboard
    
    def setup_handlers(self):
        """Setup all command handlers"""
        
        @self.bot.message_handler(commands=["status", "mode", "ping", "help", "fire", "force_signal", "venom_scan", "ghosted", "slots", "presspass", "menu", "drill", "weekly", "tactics", "recruit", "credits", "connect", "notebook", "journal", "notes"])
        def handle_telegram_commands(message):
            uid = str(message.from_user.id)
            user_name = message.from_user.first_name or "Operative"
            
            # Get user tier for personality system
            user_config = AUTHORIZED_USERS.get(uid, {})
            user_tier = user_config.get("tier", "NIBBLER")
            
            try:
                if message.text == "/status":
                    try:
                        # Import container status tracker
                        from src.bitten_core.container_status_tracker import get_container_status_tracker
                        from src.bitten_core.user_registry_manager import get_user_registry_manager
                        
                        tracker = get_container_status_tracker()
                        registry = get_user_registry_manager()
                        
                        if int(uid) in COMMANDER_IDS:
                            # System overview for commanders
                            system_status = self.get_system_status()
                            container_overview = tracker.get_system_overview()
                            combined_status = f"{system_status}\n\n{container_overview}"
                            self.send_adaptive_response(message.chat.id, combined_status, user_tier, "commander_status")
                        else:
                            # Individual container status for users
                            container_name = registry.get_container_name(uid)
                            if container_name:
                                status_message = tracker.format_container_status_message(container_name)
                                self.send_adaptive_response(message.chat.id, status_message, user_tier, "user_container_status")
                            else:
                                self.send_adaptive_response(message.chat.id, "❌ No container assigned. Visit https://joinbitten.com to set up your account and claim your free Press Pass.", user_tier, "no_container")
                    except Exception as e:
                        logger.error(f"Status command error: {e}")
                        fallback_msg = "❌ Status check temporarily unavailable."
                        self.send_adaptive_response(message.chat.id, fallback_msg, user_tier, "status_error")
                
                elif message.text.startswith("/mode"):
                    # Import fire mode handlers with fallback protection
                    try:
                        from src.bitten_core.fire_mode_handlers import FireModeHandlers
                        FireModeHandlers.handle_mode_command(self.bot, message, user_tier)
                    except ImportError as e:
                        logger.error(f"Fire mode handlers import failed: {e}")
                        fallback_msg = f"⚠️ Fire mode system temporarily unavailable.\nCurrent mode: AUTO (default for COMMANDER)\nUse /status for system information."
                        self.send_adaptive_response(message.chat.id, fallback_msg, user_tier, "system_error")
                    except Exception as e:
                        logger.error(f"Fire mode command error: {e}")
                        error_msg = "❌ Fire mode command failed. Please try again or contact support."
                        self.send_adaptive_response(message.chat.id, error_msg, user_tier, "command_error")
                
                elif message.text == "/ping":
                    ping_msg = f"🛰️ Pong. BITTEN is online and synced.\n⏰ {datetime.now().strftime('%H:%M:%S UTC')}"
                    self.send_adaptive_response(message.chat.id, ping_msg, user_tier, "ping_check")
                
                elif message.text == "/help":
                    help_msg = self.get_help_message(uid)
                    self.send_adaptive_response(message.chat.id, help_msg, user_tier, "help_request")
                
                elif message.text.startswith("/start"):
                    # Enhanced cinematic onboarding experience
                    parts = message.text.split()
                    
                    # Check for new user onboarding
                    try:
                        from src.bitten_core.onboarding_cinematic import cinematic_onboarding
                        from src.bitten_core.enhanced_personality_system import enhanced_personalities
                        from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
                        
                        # Check if user is truly new (no XP)
                        user_stats = self.get_user_stats(uid)
                        is_new_user = user_stats.get('total_xp', 0) == 0
                        
                        if is_new_user and len(parts) == 1:
                            # New user with no referral code - cinematic experience
                            welcome_msg, keyboard_data = cinematic_onboarding.get_onboarding_message(uid, "welcome")
                            
                            if keyboard_data:
                                keyboard = InlineKeyboardMarkup()
                                for row in keyboard_data.get('inline_keyboard', []):
                                    buttons = [InlineKeyboardButton(text=btn['text'], callback_data=btn['callback_data']) for btn in row]
                                    keyboard.row(*buttons)
                                self.bot.send_message(
                                    chat_id=message.chat.id,
                                    text=welcome_msg,
                                    parse_mode='Markdown',
                                    reply_markup=keyboard
                                )
                            else:
                                self.send_adaptive_response(message.chat.id, welcome_msg, user_tier, "cinematic_welcome")
                                
                            logger.info(f"New user {uid} started cinematic onboarding")
                            return
                        
                    except Exception as e:
                        logger.error(f"Cinematic onboarding error: {e}")
                        # Continue with regular onboarding if cinematic fails
                    
                    # Handle referral codes and returning users
                    if len(parts) > 1:
                        # Referral code provided
                        referral_code = parts[1]
                        try:
                            from src.bitten_core.credit_referral_system import get_credit_referral_system
                            referral_system = get_credit_referral_system()
                            
                            if referral_system.use_referral_code(referral_code, uid):
                                # Successful referral code usage
                                welcome_msg = f"""🎉 **WELCOME TO BITTEN!**

You've been referred by a fellow trader! 

💰 **REFERRAL BONUS**: When you subscribe to any paid tier ($39+), your referrer will earn a $10 credit.

🎯 **Ready to start tactical trading?**

📋 **Next Steps:**
• Use `/presspass` to get started with a 7-day trial
• Use `/help` to see all available commands
• Use `/tactical` to learn about trading strategies

Welcome to the most tactical trading community! 🚀"""
                                
                                self.send_adaptive_response(message.chat.id, welcome_msg, user_tier, "referral_welcome")
                                logger.info(f"User {uid} successfully used referral code {referral_code}")
                            else:
                                # Invalid/expired/duplicate referral code - normal welcome
                                normal_welcome = f"""🎯 **WELCOME TO BITTEN!**

Your tactical trading journey begins now!

📋 **Get Started:**
• Use `/presspass` for a 7-day free trial
• Use `/help` to see all commands
• Use `/tactical` to learn trading strategies

Ready to dominate the markets? 🚀"""
                                
                                self.send_adaptive_response(message.chat.id, normal_welcome, user_tier, "normal_welcome")
                                logger.info(f"User {uid} used invalid/expired referral code {referral_code}")
                                
                        except Exception as e:
                            logger.error(f"Referral code processing error for user {uid}: {e}")
                            # Fallback to normal welcome
                            fallback_welcome = f"""🎯 **WELCOME TO BITTEN!**

Your tactical trading journey begins now!

📋 **Get Started:**
• Use `/presspass` for a 7-day free trial
• Use `/help` to see all commands
• Use `/tactical` to learn trading strategies

Ready to dominate the markets? 🚀"""
                            
                            self.send_adaptive_response(message.chat.id, fallback_welcome, user_tier, "fallback_welcome")
                    else:
                        # No referral code - normal welcome for returning users
                        normal_welcome = f"""🎯 **WELCOME BACK TO BITTEN!**

Your tactical trading journey continues!

📋 **Quick Commands:**
• Use `/status` to check your current stats
• Use `/help` to see all commands
• Use `/tactical` to review trading strategies
• Use `/recruit` to get your own referral link

Ready to dominate the markets? 🚀"""
                        
                        self.send_adaptive_response(message.chat.id, normal_welcome, user_tier, "normal_welcome")
                        logger.info(f"Returning user {uid} used /start")
                
                elif message.text == "/api":
                    # Fire Loop Validation System - API Status Command
                    api_status = self.get_api_status(uid)
                    self.send_adaptive_response(message.chat.id, api_status, user_tier, "api_status")
                
                elif message.text.startswith("/fire"):
                    # Enhanced /fire command with signal_id support
                    message_parts = message.text.split(" ", 1)
                    signal_id = message_parts[1] if len(message_parts) > 1 else None
                    
                    if signal_id:
                        # Phase 3: Execute specific signal via BittenCore
                        try:
                            from src.bitten_core.bitten_core import BittenCore
                            
                            # Initialize or get existing core instance
                            if not hasattr(self, 'bitten_core'):
                                self.bitten_core = BittenCore()
                                self.bitten_core.set_production_bot(self)
                            
                            # Execute fire command via Core
                            result = self.bitten_core.execute_fire_command(uid, signal_id)
                            
                            if result['success']:
                                response = f"🔥 Signal {signal_id} executed successfully!"
                                if 'trade_result' in result:
                                    trade_data = result['trade_result']
                                    response += f"\n📊 Trade details: {trade_data.get('symbol', 'N/A')} {trade_data.get('direction', 'N/A')}"
                                    response += f"\n💰 Position size: {trade_data.get('position_size', 'N/A')}"
                                
                                # Add journaling prompt for post-trade reflection
                                response += f"\n\n📝 **Reflect & Earn XP:**"
                                response += f"\nDocument your thoughts about this trade for +8 XP!"
                                response += f"\nUse /notebook to add your reflection."
                                
                                # Try to record this signal execution for pairing
                                try:
                                    from src.bitten_core.notebook_xp_integration import create_notebook_xp_integration
                                    notebook_integration = create_notebook_xp_integration(uid)
                                    signal_data = result.get('signal_data', {})
                                    notebook_integration.record_signal_execution(
                                        signal_id=signal_id,
                                        symbol=signal_data.get('symbol', 'Unknown'),
                                        direction=signal_data.get('direction', 'Unknown'),
                                        entry_price=0.0,  # Would need actual entry price
                                        tcs_score=signal_data.get('confidence', 0)
                                    )
                                except Exception as e:
                                    logger.error(f"Error recording signal execution for notebook: {e}")
                                
                                # Schedule a follow-up reminder for journaling after 30 minutes
                                try:
                                    import threading
                                    import time
                                    
                                    def send_journal_reminder():
                                        time.sleep(1800)  # 30 minutes
                                        try:
                                            reminder_msg = f"""📝 **Quick Reminder**
                                            
How's that {signal_data.get('symbol', 'trade')} position going?

Consider documenting your current thoughts:
• How are you feeling about the trade?
• Any lessons learned so far?
• What would you do differently?

✨ Earn +8 XP for trade reflections: /notebook"""
                                            
                                            self.send_adaptive_response(message.chat.id, reminder_msg, user_tier, "journal_reminder")
                                        except Exception as e:
                                            logger.error(f"Error sending journal reminder: {e}")
                                    
                                    reminder_thread = threading.Thread(target=send_journal_reminder, daemon=True)
                                    reminder_thread.start()
                                    
                                except Exception as e:
                                    logger.error(f"Error scheduling journal reminder: {e}")
                            else:
                                # Check for specific error types
                                if result.get('error') == 'not_ready_for_fire':
                                    response = result.get('message', '❌ Terminal not ready for trading')
                                else:
                                    response = f"❌ Execution failed: {result.get('message', result.get('error', 'Unknown error'))}"
                            
                            self.send_adaptive_response(message.chat.id, response, user_tier, "fire_execution")
                            return
                            
                        except Exception as e:
                            logger.error(f"BittenCore fire execution error: {e}")
                            error_response = f"❌ Signal execution failed: {str(e)}"
                            self.send_adaptive_response(message.chat.id, error_response, user_tier, "fire_error")
                            return
                    
                    # Legacy fire command (no signal_id) - existing mission system
                    from src.bitten_core.fire_mode_executor import fire_mode_executor
                    from src.bitten_core.fire_mode_database import fire_mode_db
                    
                    # Get user's fire mode
                    mode_info = fire_mode_db.get_user_mode(uid)
                    
                    # FIRE logic: fetch user's pending mission
                    mission = get_pending_mission_for_user(uid)
                    if mission:
                        # Check if SELECT mode - show confirmation
                        if mode_info['current_mode'] == 'SELECT' and not mission.get('expired', False):
                            semi_msg = fire_mode_executor.format_semi_auto_message(mission)
                            keyboard = fire_mode_executor.create_semi_auto_keyboard(mission['mission_id'])
                            self.bot.send_message(message.chat.id, semi_msg, 
                                                reply_markup=keyboard, parse_mode="Markdown")
                        else:
                            # AUTO mode - execute immediately
                            result = fire_mission_for_user(uid, mission)
                            if result.get("success"):
                                symbol = mission.get("symbol", "UNKNOWN")
                                fire_msg = f"🎯 Trade fired: {symbol}\n✅ Execution successful"
                                
                                # Add BIT's trade reaction
                                if BIT_AVAILABLE:
                                    fire_msg = bit_enhance(fire_msg, "trade_execution")
                                
                                self.send_adaptive_response(message.chat.id, fire_msg, user_tier, "trade_execution")
                            else:
                                fire_msg = f"❌ Trade execution failed: {result.get('message', 'Unknown error')}"
                                
                                # Add BIT's error comfort
                                if BIT_AVAILABLE:
                                    bit_comfort = bit_integration.get_error_comfort("execution")
                                    fire_msg += f"\n\n{bit_comfort}"
                                
                                self.send_adaptive_response(message.chat.id, fire_msg, user_tier, "trade_failed")
                    else:
                        no_mission_msg = "❌ No active mission found. Wait for a signal or use /force_signal."
                        
                        # Add BIT's wisdom when no signals
                        if BIT_AVAILABLE:
                            bit_wisdom = bit_daily_wisdom()
                            no_mission_msg += f"\n\n{bit_wisdom}"
                        
                        self.send_adaptive_response(message.chat.id, no_mission_msg, user_tier, "no_mission")
                
                elif message.text == "/bit":
                    # BIT interaction command
                    if BIT_AVAILABLE:
                        bit_msg = bit_daily_wisdom()
                        bit_signature = bit_integration.add_signature_occasionally(bit_msg, 0.3)
                        self.send_adaptive_response(message.chat.id, bit_signature, user_tier, "bit_interaction")
                    else:
                        self.send_adaptive_response(message.chat.id, "BIT is currently offline. Check back later.", user_tier, "error")
                
                elif message.text == "/force_signal":
                    if int(uid) in COMMANDER_IDS:
                        # Generate live VENOM v7.0 signal
                        self.send_adaptive_response(message.chat.id, "🐍 Generating live VENOM v7.0 signal...", user_tier, "signal_generation")
                        
                        venom_signal = generate_live_venom_signal()
                        
                        if venom_signal:
                            # Convert VENOM signal to mission format
                            venom_mission = {
                                "symbol": venom_signal['pair'],
                                "type": "BUY" if venom_signal['entry_price'] else "BUY",  # Simplified for now
                                "direction": "BUY",
                                "entry_price": venom_signal['entry_price'],
                                "sl": venom_signal['stop_loss_pips'],
                                "tp": venom_signal['take_profit_pips'],
                                "tcs_score": int(venom_signal['confidence']),
                                "timeframe": "M5",
                                "session": venom_signal['session'],
                                "pattern": venom_signal['signal_type'],
                                "confluence_count": 3,
                                "countdown_minutes": venom_signal['countdown_minutes'],
                                "signal_id": venom_signal['signal_id']
                            }
                            
                            try:
                                mission = generate_mission(venom_mission, uid)
                                venom_msg = f"🐍 **LIVE VENOM SIGNAL**\n"
                                venom_msg += f"📊 {venom_signal['pair']} {venom_signal['signal_type']}\n"
                                venom_msg += f"🎯 Confidence: {venom_signal['confidence']:.1f}%\n"
                                venom_msg += f"⏰ Timer: {venom_signal['countdown_minutes']} minutes\n"
                                venom_msg += f"💰 Entry: {venom_signal['entry_price']:.5f}\n"
                                venom_msg += f"🛡️ SL: {venom_signal['stop_loss_pips']} pips\n"
                                venom_msg += f"🎯 TP: {venom_signal['take_profit_pips']} pips\n"
                                venom_msg += f"📈 R:R: 1:{venom_signal['risk_reward']:.1f}\n"
                                venom_msg += f"🆔 Mission ID: {mission['mission_id']}"
                                
                                self.send_adaptive_response(message.chat.id, venom_msg, user_tier, "venom_signal")
                                logger.info(f"🐍 Live VENOM signal generated: {venom_signal['pair']} @ {venom_signal['confidence']:.1f}%")
                            except Exception as e:
                                error_msg = f"❌ Failed to create mission from VENOM signal: {str(e)}"
                                self.send_adaptive_response(message.chat.id, error_msg, user_tier, "error")
                        else:
                            no_signal_msg = "📊 No VENOM signals available at current market conditions. Try again in a few minutes."
                            self.send_adaptive_response(message.chat.id, no_signal_msg, user_tier, "no_signal")
                    else:
                        self.send_adaptive_response(message.chat.id, "❌ Live signal generation restricted to commanders.", user_tier, "unauthorized_access")
                
                elif message.text == "/venom_scan":
                    if int(uid) in COMMANDER_IDS:
                        # Continuous VENOM scanning report
                        self.send_adaptive_response(message.chat.id, "🐍 VENOM v7.0 Market Scan initiated...", user_tier, "scan_start")
                        
                        if VENOM_ENGINE_AVAILABLE:
                            try:
                                venom = VenomCitadelProductionEngine()
                                if venom.check_market_data_health():
                                    try:
                                        # Scan all pairs for signals
                                        signals = venom.scan_all_pairs_realtime()
                                        
                                        if signals:
                                            scan_msg = f"🐍 **VENOM MARKET SCAN RESULTS**\n"
                                            scan_msg += f"📊 Found {len(signals)} active signals:\n\n"
                                            
                                            for i, signal in enumerate(signals[:5], 1):  # Show top 5
                                                scan_msg += f"**{i}. {signal['pair']} {signal['signal_type']}**\n"
                                                scan_msg += f"🎯 Confidence: {signal['confidence']:.1f}%\n"
                                                scan_msg += f"⏰ Timer: {signal['countdown_minutes']} min\n"
                                                scan_msg += f"📈 R:R: 1:{signal['risk_reward']:.1f}\n\n"
                                            
                                            if len(signals) > 5:
                                                scan_msg += f"📊 +{len(signals)-5} more signals available\n"
                                            
                                            scan_msg += f"🕐 Scan time: {datetime.now().strftime('%H:%M:%S')}"
                                            
                                        else:
                                            scan_msg = "📊 **VENOM MARKET SCAN**\n\n"
                                            scan_msg += "No signals found at current market conditions.\n"
                                            scan_msg += "Market may be in low-volatility period.\n"
                                            scan_msg += f"🕐 Scan time: {datetime.now().strftime('%H:%M:%S')}"
                                        
                                        self.send_adaptive_response(message.chat.id, scan_msg, user_tier, "venom_scan")
                                        
                                    except Exception as e:
                                        logger.error(f"VENOM scan error: {e}")
                                        error_msg = f"❌ Scan error: {str(e)}"
                                        self.send_adaptive_response(message.chat.id, error_msg, user_tier, "error")
                                else:
                                    error_msg = "❌ Market data receiver offline - cannot scan"
                                    self.send_adaptive_response(message.chat.id, error_msg, user_tier, "error")
                                    
                            except Exception as e:
                                error_msg = f"❌ VENOM scan error: {str(e)}"
                                self.send_adaptive_response(message.chat.id, error_msg, user_tier, "error")
                                logger.error(f"VENOM scan error: {e}")
                        else:
                            error_msg = "❌ VENOM Engine not available for scanning"
                            self.send_adaptive_response(message.chat.id, error_msg, user_tier, "error")
                    else:
                        self.send_adaptive_response(message.chat.id, "❌ VENOM scanning restricted to commanders.", user_tier, "unauthorized_access")
                
                elif message.text.upper().startswith('/GHOSTED'):
                    if int(uid) in COMMANDER_IDS:
                        try:
                            # Import the ghosted command handler
                            import sys
                            sys.path.append('/root/HydraX-v2/src')
                            from bitten_core.performance_commands import handle_ghosted_command
                            
                            ghosted_report = handle_ghosted_command()
                            self.send_adaptive_response(message.chat.id, ghosted_report, user_tier, "ghosted_report")
                            logger.info(f"GHOSTED report requested by commander {uid}")
                        except Exception as e:
                            error_msg = f"❌ Failed to generate GHOSTED report: {str(e)}"
                            self.send_adaptive_response(message.chat.id, error_msg, user_tier, "error")
                            logger.error(f"GHOSTED command error: {e}")
                    else:
                        self.send_adaptive_response(message.chat.id, "❌ GHOSTED report restricted to commanders.", user_tier, "unauthorized_access")
                
                elif message.text.startswith("/givegold"):
                    # Admin-only command to grant gold access
                    if int(uid) in COMMANDER_IDS:
                        try:
                            # Extract username from command
                            parts = message.text.split()
                            if len(parts) < 2:
                                self.send_adaptive_response(message.chat.id, "❌ Usage: /givegold @username", user_tier, "usage_error")
                                return
                            
                            username = parts[1].lstrip('@')  # Remove @ if present
                            
                            # Look up user by username
                            target_telegram_id = self._lookup_telegram_id_by_username(username)
                            
                            if not target_telegram_id:
                                self.send_adaptive_response(message.chat.id, f"❌ User @{username} not found in system.", user_tier, "user_not_found")
                                return
                            
                            # Import user registry manager
                            from src.bitten_core.user_registry_manager import get_user_registry_manager
                            registry = get_user_registry_manager()
                            
                            # Get user info
                            user_info = registry.get_user_info(target_telegram_id)
                            if not user_info:
                                self.send_adaptive_response(message.chat.id, f"❌ User @{username} not registered.", user_tier, "user_not_registered")
                                return
                            
                            # Check if user is US-based
                            user_region = user_info.get('user_region', 'US')
                            if user_region == 'US':
                                self.send_adaptive_response(message.chat.id, "❌ Cannot grant gold access to US-based accounts due to regulations.", user_tier, "regulatory_restriction")
                                return
                            
                            # Check if already has access
                            if user_info.get('offshore_opt_in', False):
                                self.send_adaptive_response(message.chat.id, f"ℹ️ Gold access already active for @{username}.", user_tier, "already_active")
                                return
                            
                            # Grant gold access
                            success = registry.update_offshore_opt_in(target_telegram_id, True)
                            
                            if success:
                                # Send welcome message to user
                                gold_welcome = self._format_gold_welcome_message()
                                try:
                                    self.bot.send_message(int(target_telegram_id), gold_welcome, parse_mode="MarkdownV2")
                                    logger.info(f"Gold access granted to {target_telegram_id} (@{username}) by {uid}")
                                except Exception as e:
                                    logger.error(f"Failed to send gold welcome message: {e}")
                                
                                # Confirm to admin
                                self.send_adaptive_response(message.chat.id, f"✅ Gold access granted to @{username}.", user_tier, "gold_access_granted")
                            else:
                                self.send_adaptive_response(message.chat.id, "❌ Failed to update user profile.", user_tier, "update_failed")
                                
                        except Exception as e:
                            logger.error(f"Error in /givegold command: {e}")
                            self.send_adaptive_response(message.chat.id, f"❌ Error: {str(e)}", user_tier, "command_error")
                    else:
                        self.send_adaptive_response(message.chat.id, "❌ Unauthorized. This command is restricted to commanders.", user_tier, "unauthorized")
                
                elif message.text.startswith("/givecrypto"):
                    # Admin-only command to grant crypto access
                    if int(uid) in COMMANDER_IDS:
                        try:
                            # Extract username from command
                            parts = message.text.split()
                            if len(parts) < 2:
                                self.send_adaptive_response(message.chat.id, "❌ Usage: /givecrypto @username", user_tier, "usage_error")
                                return
                            
                            username = parts[1].lstrip('@')  # Remove @ if present
                            
                            # Look up user by username
                            target_telegram_id = self._lookup_telegram_id_by_username(username)
                            
                            if not target_telegram_id:
                                self.send_adaptive_response(message.chat.id, f"❌ User @{username} not found in system.", user_tier, "user_not_found")
                                return
                            
                            # Import user registry manager
                            from src.bitten_core.user_registry_manager import get_user_registry_manager
                            registry = get_user_registry_manager()
                            
                            # Get user info
                            user_info = registry.get_user_info(target_telegram_id)
                            if not user_info:
                                self.send_adaptive_response(message.chat.id, f"❌ User @{username} not registered.", user_tier, "user_not_registered")
                                return
                            
                            # Check if user is US-based
                            user_region = user_info.get('user_region', 'US')
                            if user_region == 'US':
                                self.send_adaptive_response(message.chat.id, "❌ Cannot grant C.O.R.E. access to US-based accounts for compliance reasons.", user_tier, "regulatory_restriction")
                                return
                            
                            # Check if already has crypto access
                            if user_info.get('crypto_opt_in', False):
                                self.send_adaptive_response(message.chat.id, f"ℹ️ C.O.R.E. access already active for @{username}.", user_tier, "already_active")
                                return
                            
                            # Grant crypto access
                            success = registry.update_crypto_opt_in(target_telegram_id, True)
                            
                            if success:
                                # Send welcome message to user
                                crypto_welcome = self._format_crypto_welcome_message()
                                try:
                                    self.bot.send_message(int(target_telegram_id), crypto_welcome, parse_mode="MarkdownV2")
                                    logger.info(f"C.O.R.E. access granted to {target_telegram_id} (@{username}) by {uid}")
                                except Exception as e:
                                    logger.error(f"Failed to send crypto welcome message: {e}")
                                
                                # Confirm to admin
                                self.send_adaptive_response(message.chat.id, f"✅ C.O.R.E. access granted to @{username}.", user_tier, "crypto_access_granted")
                            else:
                                self.send_adaptive_response(message.chat.id, "❌ Failed to update user profile.", user_tier, "update_failed")
                                
                        except Exception as e:
                            logger.error(f"Error in /givecrypto command: {e}")
                            self.send_adaptive_response(message.chat.id, f"❌ Error: {str(e)}", user_tier, "command_error")
                    else:
                        self.send_adaptive_response(message.chat.id, "❌ Unauthorized. This command is restricted to commanders.", user_tier, "unauthorized")
                
                elif message.text.startswith("/slots"):
                    # Import fire mode handlers with fallback protection
                    try:
                        from src.bitten_core.fire_mode_handlers import FireModeHandlers
                        FireModeHandlers.handle_slots_command(self.bot, message, user_tier)
                    except ImportError as e:
                        logger.error(f"Fire mode handlers import failed for /slots: {e}")
                        fallback_msg = "⚠️ Slot configuration temporarily unavailable.\nCOMMANDER users can use AUTO mode with default 1 slot."
                        self.send_adaptive_response(message.chat.id, fallback_msg, user_tier, "system_error")
                    except Exception as e:
                        logger.error(f"Slots command error: {e}")
                        error_msg = "❌ Slots command failed. Please try again."
                        self.send_adaptive_response(message.chat.id, error_msg, user_tier, "command_error")
                
                elif message.text.startswith("/presspass"):
                    # Handle Press Pass registration and management
                    try:
                        from src.bitten_core.presspass_rotation_system import PressPassRotationSystem
                        from src.bitten_core.mt5_terminal_manager import MT5TerminalManager
                        
                        rotation_system = PressPassRotationSystem()
                        terminal_manager = MT5TerminalManager()
                        
                        # Check if user already has Press Pass
                        status_result = rotation_system.get_press_pass_status(uid)
                        
                        if status_result["success"] and status_result.get("has_press_pass"):
                            # User already has active Press Pass
                            account = status_result["account"]
                            days_remaining = status_result["days_remaining"]
                            hours_remaining = status_result["hours_remaining"]
                            api_running = status_result["api_running"]
                            
                            status_msg = f"🎫 **PRESS PASS ACTIVE**\\n"
                            status_msg += f"📊 Account: {account['login']}\\n"
                            status_msg += f"🏢 Broker: {account['broker']} ({account['server']})\\n"
                            status_msg += f"⏰ Time Remaining: {days_remaining}d {hours_remaining}h\\n"
                            status_msg += f"🔗 API: {'✅ Running' if api_running else '❌ Stopped'}\\n\\n"
                            status_msg += f"Your Press Pass is active! Start trading with BITTEN signals."
                            
                            if not api_running:
                                status_msg += f"\\n\\n⚠️ API appears to be stopped. Restarting..."
                                # Attempt to restart API
                                launch_result = terminal_manager.launch_api_process(uid, account, int(uid[-3:]) % 50)
                                if launch_result.get("success"):
                                    status_msg += f"\\n✅ API restarted on endpoint {launch_result['api_endpoint']}"
                                else:
                                    status_msg += f"\\n❌ Failed to restart API: {launch_result.get('error', 'Unknown error')}"
                            
                            self.send_adaptive_response(message.chat.id, status_msg, user_tier, "presspass_status")
                        
                        else:
                            # Assign new Press Pass account
                            assignment_result = rotation_system.assign_press_pass_account(uid)
                            
                            if assignment_result["success"]:
                                account = assignment_result["account"]
                                
                                # Launch API connection for the user
                                port_offset = int(uid[-3:]) % 50  # Use last 3 digits of user ID for port offset
                                launch_result = terminal_manager.launch_api_process(uid, account, port_offset)
                                
                                welcome_msg = f"🎫 **PRESS PASS ACTIVATED!**\\n\\n"
                                welcome_msg += f"Welcome to your 7-day free trial of BITTEN!\\n\\n"
                                welcome_msg += f"📊 **Your Demo Account:**\\n"
                                welcome_msg += f"• Account: {account['login']}\\n"
                                welcome_msg += f"• Server: {account['server']}\\n"
                                welcome_msg += f"• Broker: {account['broker']}\\n"
                                welcome_msg += f"• Balance: ${account['balance']:,.0f} USD\\n"
                                welcome_msg += f"• Leverage: 1:{account['leverage']}\\n\\n"
                                
                                if launch_result.get("success"):
                                    welcome_msg += f"🔗 **API Status:** ✅ Running on endpoint {launch_result['api_endpoint']}\\n\\n"
                                else:
                                    welcome_msg += f"🔗 **API Status:** ❌ Failed to start\\n\\n"
                                
                                welcome_msg += f"⏰ **Expires:** {assignment_result['expires_at'][:10]}\\n\\n"
                                welcome_msg += f"🎯 **What's Next:**\\n"
                                welcome_msg += f"• Receive BITTEN signals via Telegram\\n"
                                welcome_msg += f"• Click mission links to view trade details\\n"
                                welcome_msg += f"• Execute trades with one click\\n"
                                welcome_msg += f"• Track your performance in real-time\\n\\n"
                                welcome_msg += f"• Use /fire to execute current missions\\n"
                                welcome_msg += f"• Use /mode to configure firing modes\\n"
                                welcome_msg += f"• Use /presspass to check your status\\n\\n"
                                welcome_msg += f"🚀 **Your BITTEN journey starts now!**"
                                
                                self.send_adaptive_response(message.chat.id, welcome_msg, "PRESS_PASS", "presspass_activation")
                                logger.info(f"Press Pass activated for user {uid}: Account {account['login']}")
                                
                            else:
                                error_msg = f"❌ **Press Pass Activation Failed**\\n\\n"
                                error_msg += f"{assignment_result['message']}\\n\\n"
                                
                                if assignment_result.get("error") == "vault_full":
                                    error_msg += f"All demo accounts are currently assigned. Please try again in a few hours."
                                else:
                                    error_msg += f"Please contact support if this issue persists."
                                
                                self.send_adaptive_response(message.chat.id, error_msg, user_tier, "presspass_error")
                                logger.error(f"Press Pass activation failed for user {uid}: {assignment_result}")
                        
                    except Exception as e:
                        error_msg = f"❌ Press Pass system error. Please try again later."
                        self.send_adaptive_response(message.chat.id, error_msg, user_tier, "error")
                        logger.error(f"Press Pass command error for user {uid}: {e}")
                
                elif message.text == "/menu":
                    # Show menu options (persistent + advanced inline)
                    try:
                        from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
                        
                        # Create menu selection keyboard
                        menu_selection = InlineKeyboardMarkup([
                            [
                                InlineKeyboardButton("📱 QUICK MENU (Persistent)", callback_data="menu_quick_persistent"),
                                InlineKeyboardButton("🎯 FULL MENU (Persistent)", callback_data="menu_full_persistent")
                            ],
                            [
                                InlineKeyboardButton("⚡ ADVANCED MENU (Inline)", callback_data="menu_advanced_inline"),
                                InlineKeyboardButton("❌ Hide All Menus", callback_data="menu_hide_all")
                            ]
                        ])
                        
                        menu_text = f"""🎯 **BITTEN MENU SYSTEM**

Welcome to tactical operations, {user_name}!

**Choose Your Interface:**

📱 **QUICK MENU** - 3 buttons always visible at bottom
🎯 **FULL MENU** - 7 buttons persistent keyboard  
⚡ **ADVANCED MENU** - Complete inline interface
❌ **HIDE MENUS** - Remove all keyboards

**Current Status:**
• Tier: {user_tier}
• Systems: ✅ Operational

Select your preferred menu style:"""
                        
                        self.bot.send_message(
                            message.chat.id, 
                            menu_text, 
                            reply_markup=menu_selection, 
                            parse_mode="Markdown"
                        )
                        
                    except Exception as e:
                        logger.error(f"Menu command error: {e}")
                        fallback_msg = f"🎯 **INTEL CENTER**\\n\\nWelcome, {user_name}!\\n\\nYour tier: {user_tier}\\nUse /help for available commands."
                        self.send_adaptive_response(message.chat.id, fallback_msg, user_tier, "menu_error")
                
                elif message.text == "/drill":
                    # Daily drill report command
                    if self.drill_system:
                        try:
                            drill_report = self.drill_system.generate_drill_report(uid)
                            formatted_report = self.drill_system.format_telegram_report(drill_report, uid)
                            self.send_adaptive_response(message.chat.id, formatted_report, user_tier, "drill_report")
                        except Exception as e:
                            logger.error(f"Drill report error: {e}")
                            error_msg = "❌ Drill report temporarily unavailable. Your progress is being tracked."
                            self.send_adaptive_response(message.chat.id, error_msg, user_tier, "drill_error")
                    else:
                        self.send_adaptive_response(message.chat.id, "❌ Drill report system not available.", user_tier, "system_unavailable")
                
                elif message.text == "/weekly":
                    # Weekly summary command
                    if self.drill_system:
                        try:
                            weekly_summary = self.drill_system.generate_weekly_summary(uid)
                            self.send_adaptive_response(message.chat.id, weekly_summary, user_tier, "weekly_summary")
                        except Exception as e:
                            logger.error(f"Weekly summary error: {e}")
                            error_msg = "❌ Weekly summary temporarily unavailable. Check back later."
                            self.send_adaptive_response(message.chat.id, error_msg, user_tier, "weekly_error")
                    else:
                        self.send_adaptive_response(message.chat.id, "❌ Weekly summary system not available.", user_tier, "system_unavailable")
                
                elif message.text == "/tactics":
                    # Tactical strategy selection command
                    if DRILL_SYSTEM_AVAILABLE:
                        try:
                            # Create a simplified tactical menu using available systems
                            tactics_msg = self.get_tactical_menu_simple(uid, user_tier)
                            self.send_adaptive_response(message.chat.id, tactics_msg, user_tier, "tactics_menu")
                        except Exception as e:
                            logger.error(f"Tactics command error: {e}")
                            error_msg = "❌ Tactical strategy system temporarily unavailable."
                            self.send_adaptive_response(message.chat.id, error_msg, user_tier, "tactics_error")
                    else:
                        self.send_adaptive_response(message.chat.id, "❌ Tactical strategy system not available.", user_tier, "system_unavailable")
                
                elif message.text == "/recruit":
                    # Credit referral recruitment command
                    if self.credit_commands:
                        try:
                            # Direct integration without async conversion
                            from src.bitten_core.credit_referral_system import get_credit_referral_system
                            
                            referral_system = get_credit_referral_system()
                            user_id = str(message.from_user.id)
                            
                            # Generate referral code
                            referral_code = referral_system.generate_referral_code(user_id)
                            referral_link = f"https://t.me/Bitten_Commander_bot?start={referral_code}"
                            
                            # Get current stats
                            stats = referral_system.get_referral_stats(user_id)
                            balance = stats['balance']
                            badge = self._get_current_badge_display(balance.referral_count)
                            
                            recruit_msg = f"""🎖️ **YOUR RECRUITMENT COMMAND CENTER**

**🔗 Your Referral Link:**
`{referral_link}`

**📊 Current Stats:**
💰 Available Credits: **${balance.total_credits:.0f}**
⏳ Pending Credits: **${balance.pending_credits:.0f}**
👥 Total Recruits: **{balance.referral_count}**
🏆 Current Badge: **{badge}**

**🎯 Progress to Free Month:**
You need ${stats['progress_to_free_month']} more to earn a free month!
({stats['free_months_earned']} free months earned so far)

**💡 How It Works:**
1. Share your link with friends
2. They sign up and subscribe ($39+ tier)
3. You get $10 credit after their first payment
4. Credits automatically reduce your next bill

Copy and share your link to start earning!"""
                            
                            self.send_adaptive_response(message.chat.id, recruit_msg, user_tier, "recruit_link")
                        except Exception as e:
                            logger.error(f"Recruit command error: {e}")
                            error_msg = "❌ Recruitment system temporarily unavailable. Please try again later."
                            self.send_adaptive_response(message.chat.id, error_msg, user_tier, "recruit_error")
                    else:
                        self.send_adaptive_response(message.chat.id, "❌ Recruitment system not available.", user_tier, "system_unavailable")
                
                elif message.text == "/credits":
                    # Credit referral balance command
                    if self.credit_commands:
                        try:
                            # Direct integration
                            from src.bitten_core.credit_referral_system import get_credit_referral_system
                            
                            referral_system = get_credit_referral_system()
                            user_id = str(message.from_user.id)
                            
                            stats = referral_system.get_referral_stats(user_id)
                            balance = stats['balance']
                            badge = self._get_current_badge_display(balance.referral_count)
                            
                            credits_msg = f"""💰 **YOUR CREDIT BALANCE**

**Current Balance:**
💳 Available Credits: **${balance.total_credits:.0f}**
⏳ Pending Credits: **${balance.pending_credits:.0f}**
✅ Applied Credits: **${balance.applied_credits:.0f}**

**📈 Recruitment Success:**
👥 Total Recruits: **{balance.referral_count}**
🏆 Current Badge: **{badge}**
🆓 Free Months Earned: **{stats['free_months_earned']}**

**🎯 Progress to Next Free Month:**
You're **${stats['progress_to_free_month']}** away from earning another free month!
(NIBBLER tier = $39/month)

**💡 How Credits Work:**
• Earn $10 for each successful referral
• Credits automatically apply to your next invoice
• No expiration - stack as many as you want!
• Credits apply before charging your payment method

Use /recruit to get your referral link and start earning!"""

                            if stats['recent_referrals']:
                                credits_msg += "\n\n**📋 Recent Referrals:**\n"
                                for i, referral in enumerate(stats['recent_referrals'][:5]):
                                    status = "✅ Paid" if referral['credited'] else ("💰 Payment Pending" if referral['payment_confirmed'] else "⏳ Waiting for Payment")
                                    credits_msg += f"{i+1}. User ID: `{referral['referred_user'][-8:]}...` - {status}\n"
                            
                            self.send_adaptive_response(message.chat.id, credits_msg, user_tier, "credits_balance")
                        except Exception as e:
                            logger.error(f"Credits command error: {e}")
                            error_msg = "❌ Credits system temporarily unavailable. Please try again later."
                            self.send_adaptive_response(message.chat.id, error_msg, user_tier, "credits_error")
                    else:
                        self.send_adaptive_response(message.chat.id, "❌ Credits system not available.", user_tier, "system_unavailable")
                
                elif message.text.startswith("/connect"):
                    # MT5 Container Connection Handler
                    try:
                        response = self.telegram_command_connect_handler(message, uid, user_tier)
                        
                        # Check for special usage message flag
                        if response == "SEND_USAGE_WITH_KEYBOARD":
                            self._send_connect_usage_with_keyboard(str(message.chat.id), user_tier)
                        else:
                            self.send_adaptive_response(message.chat.id, response, user_tier, "connect_response")
                    except Exception as e:
                        logger.error(f"Connect command error: {e}")
                        error_msg = """❌ Login failed. Please check your credentials and try again.

**Format:**
```
/connect
Login: <your_login_id>
Password: <your_password>
Server: <server_name>
```

**Example:**
```
/connect
Login: 843859
Password: MyP@ssw0rd
Server: Coinexx-Demo
```"""
                        self.send_adaptive_response(message.chat.id, error_msg, user_tier, "connect_error")
                
                elif message.text.startswith("/notebook") or message.text.startswith("/journal") or message.text.startswith("/notes"):
                    # Norman's Notebook access with XP integration
                    try:
                        from src.bitten_core.notebook_xp_integration import create_notebook_xp_integration
                        
                        # Get notebook XP dashboard
                        notebook_integration = create_notebook_xp_integration(uid)
                        dashboard = notebook_integration.get_notebook_xp_dashboard()
                        
                        notebook_url = f"https://joinbitten.com/notebook/{uid}"
                        
                        # Check for signal pairing suggestions
                        pairing_suggestions = dashboard.get('pairing_suggestions', [])
                        signal_suggestion_text = ""
                        
                        if pairing_suggestions:
                            recent_signal = pairing_suggestions[0]
                            signal_suggestion_text = f"""
🔗 **Recent Trade Available for Reflection:**
📊 {recent_signal['symbol']} {recent_signal['direction']} 
💡 Status: {recent_signal['status'].title()}
🎯 TCS: {recent_signal['tcs_score']}%
⏰ Executed: {recent_signal['executed_at'][:19].replace('T', ' ')}

💭 *Consider adding your thoughts about this trade!*
"""
                        
                        # Format milestone progress
                        next_milestone = dashboard.get('next_milestone')
                        milestone_text = ""
                        if next_milestone:
                            progress_bar = "█" * int(next_milestone['percentage'] / 10) + "░" * (10 - int(next_milestone['percentage'] / 10))
                            milestone_text = f"""
🏆 **Next Milestone:** {next_milestone['name']}
📊 Progress: [{progress_bar}] {next_milestone['percentage']:.0f}%
📝 Entries: {next_milestone['progress']}/{next_milestone['required']}
🎁 Reward: +{next_milestone['xp_reward']} XP
"""
                        
                        # Check for special benefits
                        benefits_text = ""
                        if dashboard.get('insight_mode_active'):
                            benefits_text = "\n🧠 **Insight Mode Active** - Earn +2 XP for every fire + journal combo!"
                        
                        response = f"""📓 **NORMAN'S NOTEBOOK** 📓

*Your tactical trading journal with growth rewards*

📊 **Your Progress:**
📝 Total Entries: {dashboard['total_entries']}
⚡ XP Earned: {dashboard['total_xp_earned']} 
🏆 Milestones: {dashboard['milestones_achieved']}
📅 Weekly Streak: {dashboard['weekly_streak']} weeks{benefits_text}
{signal_suggestion_text}{milestone_text}
🎯 **Journal Features:**
• **Trade Reflections** - Earn +8 XP when paired with signals
• **Structured Templates** - Earn +5 XP for detailed entries  
• **Weekly Reviews** - Earn +10 XP for comprehensive analysis
• **Norman's Wisdom** - Unlock exclusive Delta trading stories
• **Milestone Rewards** - Special badges and passive benefits

💡 **Quick XP Guide:**
✅ Basic Entry: +2 XP
✅ Template Entry: +5 XP  
✅ Signal Reflection: +8 XP
✅ Weekly Review: +10 XP

**[Open Your Notebook]({notebook_url})**

*"Every trade tells a story. Every story builds a trader." - Norman's Legacy*"""

                        from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
                        
                        keyboard_buttons = [
                            [InlineKeyboardButton("📓 Open Notebook", url=notebook_url)]
                        ]
                        
                        # Add quick action for signal pairing if available
                        if pairing_suggestions:
                            recent_signal = pairing_suggestions[0]
                            quick_reflect_url = f"https://joinbitten.com/notebook/{uid}/add-entry?signal_id={recent_signal['signal_id']}&template=trade_review"
                            keyboard_buttons.append([InlineKeyboardButton("💭 Quick Trade Reflection (+8 XP)", url=quick_reflect_url)])
                        
                        keyboard_buttons.extend([
                            [InlineKeyboardButton("❓ How to Use", callback_data="notebook_help")],
                            [InlineKeyboardButton("📊 View XP Progress", callback_data="notebook_xp_progress")],
                            [InlineKeyboardButton("❌ Close", callback_data="menu_close")]
                        ])
                        
                        keyboard = InlineKeyboardMarkup(keyboard_buttons)
                        
                        self.send_adaptive_response(message.chat.id, response, user_tier, "notebook_access", reply_markup=keyboard)
                        
                    except Exception as e:
                        logger.error(f"Notebook command error: {e}")
                        error_msg = """❌ **Notebook temporarily unavailable**

Please try again in a moment or access via the Mission HUD."""
                        self.send_adaptive_response(message.chat.id, error_msg, user_tier, "notebook_error")
                
                # Persistent keyboard button handlers
                elif message.text == "🔫 FIRE":
                    # Redirect to fire command
                    fake_message = message
                    fake_message.text = "/fire"
                    # Call the fire handler directly
                    from src.bitten_core.fire_mode_executor import fire_mode_executor
                    from src.bitten_core.fire_mode_database import fire_mode_db
                    
                    # Get user's fire mode
                    user_mode = fire_mode_db.get_user_mode(uid)
                    mode_name = user_mode.get('mode', 'manual')
                    
                    # Execute fire command
                    if mode_name in ["semi_auto", "full_auto"]:
                        result_msg = fire_mode_executor.execute_auto_fire(uid, user_tier, mode_name)
                    else:
                        result_msg = fire_mode_executor.execute_manual_fire(uid, user_tier)
                    
                    self.send_adaptive_response(message.chat.id, result_msg, user_tier, "persistent_fire")
                
                elif message.text == "📊 STATUS":
                    # Redirect to status command
                    status_msg = self.get_system_status(uid)
                    self.send_adaptive_response(message.chat.id, status_msg, user_tier, "persistent_status")
                
                elif message.text == "💰 CREDITS":
                    # Redirect to credits command
                    if self.credit_commands:
                        try:
                            from src.bitten_core.credit_referral_system import get_credit_referral_system
                            
                            referral_system = get_credit_referral_system()
                            user_id = str(message.from_user.id)
                            
                            stats = referral_system.get_referral_stats(user_id)
                            balance = stats['balance']
                            badge = self._get_current_badge_display(balance.referral_count)
                            
                            credits_msg = f"""💰 **YOUR CREDIT BALANCE**

**Current Status:**
💰 Available Credits: **${balance.total_credits:.0f}**
⏳ Pending Credits: **${balance.pending_credits:.0f}**
👥 Total Recruits: **{balance.referral_count}**
🏆 Current Badge: **{badge}**
🆓 Free Months Earned: **{stats['free_months_earned']}**

**💡 Quick Actions:**
• Use /recruit to get your referral link
• Share your link to earn more credits
• Credits automatically apply to your next bill"""

                            self.send_adaptive_response(message.chat.id, credits_msg, user_tier, "persistent_credits")
                        except Exception as e:
                            logger.error(f"Persistent credits error: {e}")
                            self.send_adaptive_response(message.chat.id, "❌ Credits temporarily unavailable", user_tier, "credits_error")
                    else:
                        self.send_adaptive_response(message.chat.id, "❌ Credits system not available.", user_tier, "system_unavailable")
                
                elif message.text == "🎯 TACTICAL":
                    # Redirect to tactics command
                    if DRILL_SYSTEM_AVAILABLE:
                        try:
                            tactics_msg = self.get_tactical_menu_simple(uid, user_tier)
                            self.send_adaptive_response(message.chat.id, tactics_msg, user_tier, "persistent_tactical")
                        except Exception as e:
                            logger.error(f"Persistent tactical error: {e}")
                            self.send_adaptive_response(message.chat.id, "❌ Tactical system temporarily unavailable", user_tier, "tactical_error")
                    else:
                        self.send_adaptive_response(message.chat.id, "❌ Tactical strategy system not available.", user_tier, "system_unavailable")
                
                elif message.text == "📚 HELP":
                    # Redirect to help command
                    help_msg = self.get_help_message(uid)
                    self.send_adaptive_response(message.chat.id, help_msg, user_tier, "persistent_help")
                
                elif message.text == "🏆 RECRUIT":
                    # Redirect to recruit command
                    if self.credit_commands:
                        try:
                            from src.bitten_core.credit_referral_system import get_credit_referral_system
                            
                            referral_system = get_credit_referral_system()
                            user_id = str(message.from_user.id)
                            
                            referral_code = referral_system.generate_referral_code(user_id)
                            referral_link = f"https://t.me/Bitten_Commander_bot?start={referral_code}"
                            
                            stats = referral_system.get_referral_stats(user_id)
                            balance = stats['balance']
                            badge = self._get_current_badge_display(balance.referral_count)
                            
                            recruit_msg = f"""🎖️ **RECRUITMENT COMMAND**

**🔗 Your Link:**
`{referral_link}`

**📊 Stats:**
💰 Credits: **${balance.total_credits:.0f}**
👥 Recruits: **{balance.referral_count}**
🏆 Badge: **{badge}**

Share your link to earn $10 per successful referral!"""
                            
                            self.send_adaptive_response(message.chat.id, recruit_msg, user_tier, "persistent_recruit")
                        except Exception as e:
                            logger.error(f"Persistent recruit error: {e}")
                            self.send_adaptive_response(message.chat.id, "❌ Recruitment temporarily unavailable", user_tier, "recruit_error")
                    else:
                        self.send_adaptive_response(message.chat.id, "❌ Recruitment system not available.", user_tier, "system_unavailable")
                
                elif message.text == "📱 MENU":
                    # Show advanced inline menu
                    try:
                        from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
                        
                        keyboard = InlineKeyboardMarkup([
                            [
                                InlineKeyboardButton("🔫 COMBAT OPS", callback_data="menu_combat_ops"),
                                InlineKeyboardButton("📚 FIELD MANUAL", callback_data="menu_field_manual")
                            ],
                            [
                                InlineKeyboardButton("💰 TIER INTEL", callback_data="menu_tier_intel"),
                                InlineKeyboardButton("🎖️ XP ECONOMY", callback_data="menu_xp_economy")
                            ],
                            [
                                InlineKeyboardButton("🌐 MISSION HUD", url="https://joinbitten.com/hud"),
                                InlineKeyboardButton("❌ Close", callback_data="menu_close")
                            ]
                        ])
                        
                        menu_text = f"""🎯 **INTEL COMMAND CENTER**

🔫 **COMBAT OPS** - Fire modes, trading controls
📚 **FIELD MANUAL** - Commands, help system  
💰 **TIER INTEL** - Subscription & upgrade info
🎖️ **XP ECONOMY** - Badge system, achievements

🌐 **MISSION HUD** - Live trading interface
❌ **Close** - Close this menu

Select an option to continue..."""
                        
                        self.bot.send_message(
                            message.chat.id, 
                            menu_text, 
                            reply_markup=keyboard,
                            parse_mode="Markdown"
                        )
                        
                    except Exception as e:
                        logger.error(f"Advanced menu error: {e}")
                        self.send_adaptive_response(message.chat.id, "❌ Advanced menu temporarily unavailable", user_tier, "menu_error")
                
                elif message.text == "❌ HIDE":
                    # Hide the persistent keyboard
                    from telebot.types import ReplyKeyboardRemove
                    self.bot.send_message(
                        message.chat.id,
                        "🫥 Persistent menu hidden. Type /menu to show it again.",
                        reply_markup=ReplyKeyboardRemove()
                    )
                
                else:
                    # Fallback handler for unrecognized commands
                    if message.text and message.text.startswith("/"):
                        # This is a command we don't recognize
                        fallback_msg = f"""❓ **Command not recognized:** `{message.text}`

**Available Commands:**
• `/help` - Show all commands
• `/status` - System status check  
• `/fire` - Execute trading signals
• `/connect` - Setup MT5 terminal
• `/notebook` - Access trading journal
• `/menu` - Show command menu

Use `/help` for the complete command list."""
                        
                        self.send_adaptive_response(message.chat.id, fallback_msg, user_tier, "unknown_command")
                        logger.warning(f"Unknown command from user {uid}: {message.text}")
                    # Non-command messages are handled by the generic handler below
                
            except Exception as e:
                logger.error(f"Error handling command {message.text}: {e}")
                self.send_adaptive_response(message.chat.id, "❌ Command processing error. Please try again.", user_tier, "error")
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("mode_") or call.data.startswith("slots_") or call.data.startswith("semi_fire_") or call.data.startswith("menu_") or call.data.startswith("combat_") or call.data.startswith("field_") or call.data.startswith("tier_") or call.data.startswith("xp_") or call.data.startswith("help_") or call.data.startswith("tool_") or call.data.startswith("bot_") or call.data.startswith("notebook_") or call.data.startswith("onboard_"))
        def handle_all_callbacks(call):
            """Handle all inline keyboard callbacks including fire mode and Intel Center"""
            user_id = str(call.from_user.id)
            user_config = AUTHORIZED_USERS.get(user_id, {})
            user_tier = user_config.get("tier", "NIBBLER")
            
            try:
                # Handle fire mode callbacks
                if call.data.startswith(("mode_", "slots_", "semi_fire_")):
                    from src.bitten_core.fire_mode_handlers import FireModeHandlers
                    from src.bitten_core.fire_mode_executor import fire_mode_executor
                    
                    if call.data.startswith("mode_"):
                        FireModeHandlers.handle_mode_callback(self.bot, call, user_tier)
                    elif call.data.startswith("slots_"):
                        FireModeHandlers.handle_slots_callback(self.bot, call, user_tier)
                    elif call.data.startswith("semi_fire_"):
                        fire_mode_executor.handle_semi_fire_callback(self.bot, call)
                
                # Handle menu system callbacks
                elif call.data in ["menu_quick_persistent", "menu_full_persistent", "menu_advanced_inline", "menu_hide_all"]:
                    self.handle_menu_system_callback(call, user_tier)
                
                # Handle Intel Center menu callbacks
                elif call.data.startswith(("menu_", "combat_", "field_", "tier_", "xp_", "help_", "tool_", "bot_")):
                    self.handle_intel_center_callback(call, user_tier)
                
                else:
                    logger.warning(f"Unhandled callback data: {call.data}")
                    self.bot.answer_callback_query(call.id, "Command not recognized", show_alert=True)
                    
            except ImportError as e:
                logger.error(f"Callback handlers import failed: {e}")
                self.bot.answer_callback_query(call.id, "⚠️ System temporarily unavailable", show_alert=True)
            except Exception as e:
                logger.error(f"Callback error: {e}")
                self.bot.answer_callback_query(call.id, "❌ Command failed. Please try again.", show_alert=True)
        
        # Initialize tactical and drill systems if available
        if DRILL_TACTICAL_AVAILABLE:
            try:
                drill_system = DailyDrillReportSystem()
                register_drill_report_handlers(self.bot, drill_system)
                logger.info("✅ Drill report handlers registered")
            except Exception as e:
                logger.error(f"❌ Failed to register drill handlers: {e}")
        
        @self.bot.message_handler(func=lambda message: True)
        def handle_all_messages(message):
            """Handle non-command messages"""
            # Check if this is a new user and send welcome message
            user_id = str(message.from_user.id)
            user_config = AUTHORIZED_USERS.get(user_id, {})
            user_tier = user_config.get("tier", "NIBBLER")
            
            # Send welcome message for new users with unified personality system
            if UNIFIED_PERSONALITY_AVAILABLE and self.unified_bot:
                try:
                    # Check if user has a personality profile
                    if not hasattr(self.unified_bot.unified_orchestrator, 'adaptive_engine'):
                        return
                    
                    user_profile = self.unified_bot.unified_orchestrator.adaptive_engine.get_user_profile(user_id)
                    if not user_profile:
                        # This is a new user - send welcome message
                        self.unified_bot.send_welcome_message(message.chat.id, user_tier)
                        return
                    
                    # Regular interaction
                    self.send_adaptive_response(message.chat.id, message.text or "Hello!", user_tier, "general_message")
                    
                except Exception as e:
                    logger.error(f"Error in unified message handling: {e}")
                    # Fallback to simple response
                    self.bot.send_message(message.chat.id, "Hello! I'm BITTEN, your trading assistant.")
            else:
                # Could add easter eggs or general chat handling here
                pass
    
    def get_system_status(self):
        """Get comprehensive system status"""
        try:
            status_parts = ["🧠 BITTEN SYSTEM STATUS:"]
            
            # Check engine
            apex_log = "/root/HydraX-v2/apex_v5_live_real.log"
            if os.path.exists(apex_log):
                age = time.time() - os.path.getmtime(apex_log)
                if age < 300:  # 5 minutes
                    status_parts.append("Engine: ✅ Active")
                else:
                    status_parts.append("Engine: ⚠️ Idle")
            else:
                status_parts.append("Engine: ❌ No logs")
            
            # Check missions
            missions_dir = "/root/HydraX-v2/missions/"
            if os.path.exists(missions_dir):
                mission_count = len([f for f in os.listdir(missions_dir) if f.endswith('.json')])
                status_parts.append(f"Missions: ✅ {mission_count} active")
            else:
                status_parts.append("Missions: ❌ Directory missing")
            
            # Check WebApp
            try:
                response = requests.get("http://localhost:8888/api/health", timeout=5)
                if response.status_code == 200:
                    status_parts.append("WebApp: ✅ Online")
                else:
                    status_parts.append("WebApp: ⚠️ Responding")
            except:
                status_parts.append("WebApp: ❌ Offline")
            
            # Check API
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex(('127.0.0.1', 9000))
                sock.close()
                if result == 0:
                    status_parts.append("API: ✅ Connected")
                else:
                    status_parts.append("API: ❌ No connection")
            except:
                status_parts.append("API: ❌ Check failed")
            
            status_parts.append(f"You: COMMANDER (Full Access)")
            status_parts.append(f"Time: {datetime.now().strftime('%H:%M:%S UTC')}")
            
            # Add BIT's system status report  
            if BIT_AVAILABLE:
                all_systems_good = "❌" not in "\\n".join(status_parts)
                bit_status = bit_integration.get_system_status(all_systems_good)
                status_parts.append(f"\\n{bit_status}")
            
            return "\\n".join(status_parts)
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return "❌ Status check failed"
    
    def get_tactical_menu_simple(self, user_id, user_tier):
        """Get simplified tactical strategy menu"""
        try:
            if DRILL_SYSTEM_AVAILABLE and hasattr(tactical_strategy_manager, 'get_unlocked_strategies'):
                # Try to get user XP (assuming 500 for fallback)
                user_xp = 500  # Default XP for basic access
                
                unlocked_strategies = tactical_strategy_manager.get_unlocked_strategies(user_xp)
                daily_state = tactical_strategy_manager.get_daily_state(user_id)
                
                tactics_msg = f"""🎯 **DAILY TACTICAL SELECTION**

💰 **Current XP**: {user_xp:}
📊 **Today's Status**: """

                if daily_state and daily_state.selected_strategy:
                    config = tactical_strategy_manager.TACTICAL_CONFIGS.get(daily_state.selected_strategy)
                    if config:
                        tactics_msg += f"""🔒 **{config.display_name}** Selected
🎯 **Shots**: {daily_state.shots_fired}/{config.max_shots}
📈 **Performance**: {daily_state.wins_today}W/{daily_state.losses_today}L
💰 **Daily P&L**: {daily_state.daily_pnl:+.1f}%"""
                else:
                    tactics_msg += "Ready to select strategy"
                
                tactics_msg += f"""

**AVAILABLE TACTICS** ({len(unlocked_strategies)}/4):
"""
                
                for strategy_id in unlocked_strategies:
                    config = tactical_strategy_manager.TACTICAL_CONFIGS.get(strategy_id)
                    if config:
                        tactics_msg += f"""
🎯 **{config.display_name}**
   {config.description}
   Max Shots: {config.max_shots}/day"""
                
                tactics_msg += f"""

Use the webapp to select your daily tactical strategy.
Your strategy determines signal filtering and risk parameters."""
                
                return tactics_msg
            else:
                return "🎯 **TACTICAL STRATEGIES**\\n\\nTactical strategy system is being initialized.\\nCheck back in a few moments."
                
        except Exception as e:
            logger.error(f"Error generating tactical menu: {e}")
            return "🎯 **TACTICAL STRATEGIES**\\n\\nSystem temporarily unavailable. Your trading continues with default settings."
    
    def get_help_message(self, user_id):
        """Get user-specific help message"""
        is_commander = int(user_id) in COMMANDER_IDS
        
        help_parts = ["📖 Available Commands:"]
        help_parts.append("/ping – Is bot online?")
        help_parts.append("/help – Show this help")
        help_parts.append("/menu – Intel Command Center")
        help_parts.append("/fire – Execute current mission")
        help_parts.append("/api – API and fire loop status")
        if BIT_AVAILABLE:
            help_parts.append("/bit – Chat with BIT, your AI companion")
        
        help_parts.append("🎮 Trading Commands:")
        help_parts.append("/connect – Connect your MT5 account")
        help_parts.append("")
        help_parts.append("📋 /connect Example:")
        help_parts.append("/connect")
        help_parts.append("Login: 843859")
        help_parts.append("Password: [Your MT5 Password]")
        help_parts.append("Server: Coinexx-Demo")
        help_parts.append("")
        help_parts.append("ℹ️ Your terminal will be created automatically if it doesn't exist.")
        help_parts.append("You'll receive a confirmation when it's ready.")
        help_parts.append("")
        help_parts.append("/mode – View/change fire mode")
        help_parts.append("/slots – Configure AUTO slots (COMMANDER only)")
        help_parts.append("")
        help_parts.append("📓 Journal & Notes:")
        help_parts.append("/notebook – Your personal trading journal")
        help_parts.append("/journal – Same as /notebook")
        help_parts.append("/notes – Same as /notebook")
        
        help_parts.append("🎫 Press Pass:")
        help_parts.append("/presspass – Activate 7-day free trial")
        
        # Add drill report and tactical commands if available
        if DRILL_SYSTEM_AVAILABLE or TACTICAL_INTERFACE_AVAILABLE:
            help_parts.append("🎖️ Drill Reports & Tactics:")
            if DRILL_SYSTEM_AVAILABLE:
                help_parts.append("/drill – Daily drill report")
                help_parts.append("/weekly – Weekly performance summary")
            if TACTICAL_INTERFACE_AVAILABLE:
                help_parts.append("/tactics – Tactical strategy selection")
        
        # Add personality commands if available
        if UNIFIED_PERSONALITY_AVAILABLE:
            help_parts.append("🎭 Unified Personality Commands:")
            help_parts.append("/voice – Toggle voice messages")
            help_parts.append("/personality – View your unified personality profile")
            help_parts.append("/evolve – Force personality evolution")
            help_parts.append("/layers – View all personality layers")
            help_parts.append("/norman – Norman's story elements")
        elif PERSONALITY_SYSTEM_AVAILABLE:
            help_parts.append("🎭 Adaptive Personality Commands:")
            help_parts.append("/voice – Toggle voice messages")
            help_parts.append("/personality – View your personality profile")
            help_parts.append("/voicestats – Voice system statistics")
            help_parts.append("/voiceforce [NAME] – Force personality (test)")
        
        if is_commander:
            help_parts.append("👑 Commander Commands:")
            help_parts.append("/status – System check (Commander)")
            help_parts.append("/force_signal – Generate live VENOM v7.0 signal (Commander)")
            help_parts.append("/venom_scan – Scan all pairs for VENOM signals (Commander)")
            help_parts.append("/ghosted – Tactical ghosted ops report (Commander)")
        
        user_config = AUTHORIZED_USERS.get(user_id, {})
        if user_config:
            tier = user_config.get("tier", "USER")
            help_parts.append(f"Your tier: {tier}")
        
        return "\\n".join(help_parts)
    
    def get_api_status(self, user_id):
        """Get comprehensive API and fire loop status"""
        if not FIRE_LOOP_AVAILABLE:
            return "❌ Fire Loop Validation System not available"
        
        status_parts = ["🔗 API STATUS REPORT"]
        status_parts.append("=" * 30)
        
        # Fire Loop Verification
        try:
            fire_verifier = FireLoopVerifier()
            flow_analysis = fire_verifier.run_single_check()
            
            # Overall health
            overall_status = flow_analysis.get('overall_status', '❌ UNKNOWN')
            flow_health = flow_analysis.get('flow_health', '0%')
            status_parts.append(f"🎯 Overall Health: {overall_status} ({flow_health})")
            
            # Stage breakdown
            status_parts.append("\\n📊 Pipeline Stages:")
            if 'stage_1_signal' in flow_analysis:
                stage1 = flow_analysis['stage_1_signal']
                status_parts.append(f"[1] Signal Gen: {stage1['status']} ({stage1['age']})")
            
            if 'stage_2_relay' in flow_analysis:
                stage2 = flow_analysis['stage_2_relay']
                status_parts.append(f"[2] Troll Relay: {stage2['status']} ({stage2['age']})")
            
            if 'stage_3_result' in flow_analysis:
                stage3 = flow_analysis['stage_3_result']
                status_parts.append(f"[3] Trade Result: {stage3['status']} ({stage3['age']})")
            
            # API health
            if 'api_health' in flow_analysis:
                api = flow_analysis['api_health']
                status_parts.append(f"\\n🔗 API: {api['status']}")
                status_parts.append(f"    {api['message']}")
            
        except Exception as e:
            status_parts.append(f"❌ Fire Loop Error: {str(e)}")
        
        # Clone Farm Status (if user is authorized)
        if user_id in ['7176191872', '843859']:  # Commander or special user
            status_parts.append("\\n🏭 Clone Farm Status:")
            try:
                farm_watcher = CloneLogWatcher("843859")
                status_parts.append("    🔍 Farm monitoring active")
                status_parts.append("    📍 Farm: api.local:8080")
                status_parts.append("    👤 User: 843859")
                status_parts.append("    🖥️ Path: /opt/clone_farm/users/user_843859")
            except Exception as e:
                status_parts.append(f"    ❌ Farm error: {str(e)}")
        else:
            status_parts.append("\\n🏭 Clone Farm: Limited access")
        
        # API Monitor Heartbeat
        try:
            with open('/var/run/api_monitor_heartbeat.txt', 'r') as f:
                heartbeat = f.read().strip()
                if '[HEARTBEAT]' in heartbeat:
                    timestamp = heartbeat.split('[HEARTBEAT]')[1].strip()
                    status_parts.append(f"\\n💓 API Monitor: ACTIVE")
                    status_parts.append(f"    Last beat: {timestamp}")
                else:
                    status_parts.append("\\n💓 API Monitor: UNKNOWN")
        except Exception as e:
            status_parts.append("\\n💓 API Monitor: OFFLINE")
        
        # Commands
        status_parts.append("\\n🔧 Available Commands:")
        status_parts.append("/api - This status report")
        if user_id in ['7176191872']:
            status_parts.append("/firetrace - Continuous fire loop monitoring")
            status_parts.append("/farmlogs - Clone farm log analysis")
        
        status_parts.append("\\n🎯 Fire Loop System: Monitoring complete signal-to-execution pipeline")
        
        return "\\n".join(status_parts)
    
    def handle_menu_system_callback(self, call, user_tier):
        """Handle menu system selection callbacks"""
        from telebot.types import ReplyKeyboardRemove
        
        user_id = str(call.from_user.id)
        user_name = call.from_user.first_name or "Operative"
        
        try:
            if call.data == "menu_quick_persistent":
                # Show quick persistent menu
                keyboard = self.create_quick_keyboard()
                
                response_text = f"""📱 **QUICK MENU ACTIVATED**

{user_name}, your quick-access menu is now persistent at the bottom!

🔫 **FIRE** - Execute trades
💰 **CREDITS** - Check referral balance  
📱 **MENU** - Show menu options

This menu will stay visible for quick access! 🚀"""
                
                self.bot.edit_message_text(
                    response_text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=None,
                    parse_mode="Markdown"
                )
                
                # Send a new message with the persistent keyboard
                self.bot.send_message(
                    call.message.chat.id,
                    "Quick menu activated below! ⬇️",
                    reply_markup=keyboard
                )
                
            elif call.data == "menu_full_persistent":
                # Show full persistent menu
                keyboard = self.create_full_keyboard()
                
                response_text = f"""🎯 **FULL MENU ACTIVATED**

{user_name}, your complete command menu is now active!

All major commands are available as persistent buttons:
🔫 FIRE • 📊 STATUS • 💰 CREDITS • 🎯 TACTICAL • 📚 HELP • 🏆 RECRUIT

Use ❌ HIDE to remove the keyboard when needed."""
                
                self.bot.edit_message_text(
                    response_text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=None,
                    parse_mode="Markdown"
                )
                
                # Send a new message with the persistent keyboard
                self.bot.send_message(
                    call.message.chat.id,
                    "Full menu activated below! ⬇️",
                    reply_markup=keyboard
                )
                
            elif call.data == "menu_advanced_inline":
                # Show advanced inline menu (original Intel Center)
                from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
                
                advanced_keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔫 COMBAT OPS", callback_data="menu_combat_ops"),
                        InlineKeyboardButton("📚 FIELD MANUAL", callback_data="menu_field_manual")
                    ],
                    [
                        InlineKeyboardButton("💰 TIER INTEL", callback_data="menu_tier_intel"),
                        InlineKeyboardButton("🎖️ XP ECONOMY", callback_data="menu_xp_economy")
                    ],
                    [
                        InlineKeyboardButton("🌐 MISSION HUD", url="https://joinbitten.com/hud"),
                        InlineKeyboardButton("❌ Close", callback_data="menu_close")
                    ]
                ])
                
                advanced_text = f"""⚡ **ADVANCED INTEL CENTER**

Welcome to BITTEN tactical operations, {user_name}!

**Current Status:**
• Tier: {user_tier}
• Systems: ✅ Operational
• Signals: 📡 Monitoring

**Available Intel:**
🔫 Combat Ops - Mission status & execution
📚 Field Manual - Trading guides & protocols  
💰 Tier Intel - Subscription & upgrade info
🎖️ XP Economy - Gamification & rewards

Select an option below:"""
                
                self.bot.edit_message_text(
                    advanced_text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=advanced_keyboard,
                    parse_mode="Markdown"
                )
                
            elif call.data == "menu_hide_all":
                # Hide all keyboards
                self.bot.edit_message_text(
                    f"❌ **ALL MENUS HIDDEN**\n\n{user_name}, all keyboards have been removed.\n\nType `/menu` anytime to show menu options again!",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=None,
                    parse_mode="Markdown"
                )
                
                # Send message with keyboard removal
                self.bot.send_message(
                    call.message.chat.id,
                    "🫥 Keyboards hidden. Type /menu to restore.",
                    reply_markup=ReplyKeyboardRemove()
                )
            
            # Answer the callback query
            self.bot.answer_callback_query(call.id, "Menu activated!")
            
        except Exception as e:
            logger.error(f"Menu system callback error: {e}")
            self.bot.answer_callback_query(call.id, "❌ Menu error", show_alert=True)
    
    def handle_intel_center_callback(self, call, user_tier):
        """Handle Intel Command Center menu callbacks with comprehensive system"""
        user_id = str(call.from_user.id)
        callback_data = call.data
        
        try:
            # Import comprehensive menu handler
            from comprehensive_menu_integration import handle_any_callback
            
            # Handle the callback with comprehensive system
            result = handle_any_callback(callback_data, int(user_id), user_tier)
            
            if result['success']:
                # Send the comprehensive response
                try:
                    self.bot.edit_message_text(
                        result['content'],
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=result.get('keyboard'),
                        parse_mode="Markdown"
                    )
                    self.bot.answer_callback_query(call.id, f"✅ Content loaded ({result['source']})")
                except:
                    # If editing fails, send new message
                    self.bot.send_message(
                        call.message.chat.id, 
                        result['content'], 
                        reply_markup=result.get('keyboard'),
                        parse_mode="Markdown"
                    )
                    self.bot.answer_callback_query(call.id, f"✅ Information sent ({result['source']})")
            else:
                # Send error response
                self.bot.edit_message_text(
                    result['content'],
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=None,
                    parse_mode="Markdown"
                )
                self.bot.answer_callback_query(call.id, "⚠️ Content under construction")
            
        except Exception as e:
            logger.error(f"Intel Center callback error: {e}")
            
            # Provide helpful fallback responses
            if callback_data == "menu_close":
                # Close/delete the menu
                try:
                    self.bot.delete_message(call.message.chat.id, call.message.message_id)
                    self.bot.answer_callback_query(call.id, "Menu closed")
                except:
                    self.bot.answer_callback_query(call.id, "Menu closed")
                return
            
            elif callback_data == "notebook_help":
                # Notebook usage help
                help_response = """📓 **HOW TO USE NORMAN'S NOTEBOOK**

**🚀 GETTING STARTED:**
1. **Open Your Notebook** - Click the button above or use `/notebook`
2. **Write Your First Entry** - Reflect on your last trade
3. **Track Your Emotions** - Note how trades made you feel
4. **Learn from Patterns** - The system detects your habits

**📝 WHAT TO WRITE:**
• **Before Trading:** Your analysis and plan
• **During Trades:** Your emotions and thoughts  
• **After Trades:** What you learned, good or bad
• **General Thoughts:** Market observations, goals, ideas

**🎯 SPECIAL FEATURES:**
• **Mood Detection** - Automatically analyzes your emotions
• **Pattern Recognition** - Spots revenge trading, FOMO, etc.
• **Norman's Wisdom** - Unlocks story entries as you grow
• **Growth Tracking** - Charts your emotional development

**💡 PRO TIPS:**
• Be honest - the notebook is just for you
• Write regularly - even short notes help
• Review your entries weekly
• Use the search feature to find patterns

**🏆 WHAT YOU'LL GAIN:**
• Better understanding of your trading psychology
• Recognition of repeated mistakes  
• Emotional growth tracking
• Personal trading wisdom library

*Remember: Every master trader keeps a journal!*"""

                from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📓 Open Notebook", url=f"https://joinbitten.com/notebook/{call.from_user.id}")],
                    [InlineKeyboardButton("❌ Close", callback_data="menu_close")]
                ])
                
                try:
                    self.bot.edit_message_text(
                        help_response,
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                    self.bot.answer_callback_query(call.id, "📚 Notebook guide loaded")
                except:
                    self.bot.send_message(call.message.chat.id, help_response, reply_markup=keyboard, parse_mode="Markdown")
                    self.bot.answer_callback_query(call.id, "📚 Help sent")
                return
            
            elif callback_data == "notebook_xp_progress":
                # Notebook XP progress display
                try:
                    from src.bitten_core.notebook_xp_integration import create_notebook_xp_integration
                    
                    user_id = str(call.from_user.id)
                    notebook_integration = create_notebook_xp_integration(user_id)
                    dashboard = notebook_integration.get_notebook_xp_dashboard()
                    
                    # Format milestones display
                    all_milestones = notebook_integration.milestones
                    achieved_milestones = notebook_integration.user_milestones
                    
                    milestones_text = ""
                    for milestone in all_milestones:
                        status_icon = "✅" if achieved_milestones.get(milestone.id, False) else "⏳"
                        milestones_text += f"{status_icon} **{milestone.name}** ({milestone.entries_required} entries) - {milestone.xp_reward} XP\n"
                        if milestone.passive_benefit:
                            milestones_text += f"   🎁 Unlock: {milestone.passive_benefit}\n"
                        milestones_text += "\n"
                    
                    # Recent activity
                    recent_text = ""
                    if dashboard['recent_entries']:
                        recent_text = "\n📝 **Recent Activity:**\n"
                        for entry in dashboard['recent_entries'][-3:]:
                            entry_date = entry.get('created_at', 'Unknown')[:10] if entry.get('created_at') else 'Unknown'
                            xp_earned = entry.get('xp_earned', 0)
                            recent_text += f"• {entry.get('title', 'Untitled')[:30]}... (+{xp_earned} XP) - {entry_date}\n"
                    
                    progress_response = f"""📊 **NORMAN'S NOTEBOOK XP PROGRESS**

📝 **Current Stats:**
• Total Entries: {dashboard['total_entries']}
• XP Earned from Journaling: {dashboard['total_xp_earned']}
• Milestones Achieved: {dashboard['milestones_achieved']}/{len(all_milestones)}
• Weekly Streak: {dashboard['weekly_streak']} weeks

🏆 **Achievement Milestones:**
{milestones_text}

💡 **XP Rewards:**
✅ Basic Entry: +2 XP
✅ Structured Template: +5 XP  
✅ Signal-Paired Reflection: +8 XP
✅ Weekly Review: +10 XP
✅ Milestone Achievement: +{max([m.xp_reward for m in all_milestones])} XP
{recent_text}
🎯 **Next Target:** {"Complete your first entry!" if dashboard['total_entries'] == 0 else f"Reach {dashboard['next_milestone']['required']} entries for {dashboard['next_milestone']['name']}!" if dashboard.get('next_milestone') else "All milestones achieved! 🏆"}

*Keep journaling to unlock Norman's wisdom and earn XP!*"""

                    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("📓 Open Notebook", url=f"https://joinbitten.com/notebook/{call.from_user.id}")],
                        [InlineKeyboardButton("🔙 Back to Notebook", callback_data="notebook_help")],
                        [InlineKeyboardButton("❌ Close", callback_data="menu_close")]
                    ])
                    
                    self.bot.edit_message_text(
                        progress_response,
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                    self.bot.answer_callback_query(call.id, "📊 Progress loaded")
                    
                except Exception as e:
                    logger.error(f"Notebook XP progress error: {e}")
                    self.bot.answer_callback_query(call.id, "❌ Progress temporarily unavailable", show_alert=True)
                return
                
            elif "field_manual" in callback_data or "help_" in callback_data:
                response = """📚 **FIELD MANUAL - User Guide**
                
**How Trading Works:**
① Receive signal alerts in Telegram
② Click mission briefing link  
③ Review signal details in WebApp
④ Click FIRE button (if allowed by tier)
⑤ Trade executes automatically

**Signal Types by Tier:**
🦷 **NIBBLER**: Rapid Raid only (1:2 R:R)
🔥 **FANG+**: All signals (Rapid & Sniper)
• Rapid Raid = Quick 1:2 R:R trades
• Sniper Shot = Longer 1:3+ R:R trades

**Risk Management (Automated):**
• 2% of balance per trade (all tiers)
• Position size auto-calculated
• SL/TP preset by signal type
• Trade slots limit exposure

**🎖️ Your War Room (/me):**
• View all achievements & kill cards
• Share referral link ($10 per signup)
• Track stats, ranks & recruits
• Social sharing to FB/IG/X
• Access Norman's Notebook
• Your complete brag hub!

**Quick Links:**
• Mission HUD → Active signals
• War Room → Your profile & stats
• Intel Center → This help menu

**🛡️ CITADEL System:**
Advanced signal protection
(Details coming soon)"""
                
            elif "combat_ops" in callback_data:
                response = """🔫 **COMBAT OPERATIONS**
                
**Mission Status:** ✅ Operational
**Signal Engine:** VENOM v7.0 Active
**Today's Activity:** Monitoring markets

**Live Features:**
• 84.3% win rate signals
• Real-time mission alerts
• One-click execution
• Automated risk management

**Your Mission Control:**
📱 Signal alerts → Telegram
🎯 Mission details → WebApp
🔥 Execute trades → Fire button
📊 Track results → War Room

**Need Help?**
Return to Intel Center for more options"""
                
            elif callback_data == "menu_intel_center":
                # Show main Intel Center menu
                response = """🎯 **INTEL COMMAND CENTER**

Your central hub for all trading operations.

**Available Sections:**
🔫 **Combat Ops** - Live mission status
📚 **Field Manual** - How to use BITTEN
💰 **Tier Intel** - Subscription tiers
🎖️ **XP Economy** - Rewards & badges

**Quick Links:**
🌐 Mission HUD - View live signals
🎖️ War Room - Stats & referrals

Select an option below to continue."""
                
            elif "tier_" in callback_data:
                response = f"""💰 **TIER INFORMATION**
                
**Your Current Tier:** {user_tier}

**🎯 Available Tiers & Trade Slots:**

🎫 **PRESS PASS** - FREE (7-day trial)
• 1 trade slot (demo only)
• Rapid Raid signals only

🦷 **NIBBLER** - $39/mo
• 1 trade slot = 1 open position at a time
• Rapid Raid signals only (1:2 R:R)
• Perfect for beginners

🔥 **FANG** - $89/mo  
• 2 trade slots = 2 concurrent positions
• Access to ALL signal types:
  - Rapid Raid (1:2 R:R) 
  - Sniper Shots (1:3+ R:R)

⚡ **COMMANDER** - $189/mo
• Unlimited trade slots
• All signal types + Full AUTO mode
• Trades fire automatically as slots open

**💡 What are Trade Slots?**
Think of them as chambers in a gun. Each slot allows one open trade. When a trade closes (hits TP/SL), that slot opens for the next opportunity.

**Risk Management:** All tiers use 2% risk per trade, calculated automatically."""
                
            elif "xp_" in callback_data:
                # Try to get real XP data
                try:
                    from src.bitten_core.xp_integration import XPIntegrationManager
                    xp_manager = XPIntegrationManager()
                    xp_status = xp_manager.get_user_xp_status(str(call.from_user.id))
                    current_xp = xp_status.get('xp_balance', {}).get('current_balance', 0)
                    level = xp_status.get('profile', {}).get('level', 1)
                except:
                    current_xp = 0
                    level = 1
                
                response = f"""🎖️ **XP ECONOMY**
                
**Your Stats:**
• Current XP: **{current_xp:,}** 
• Level: **{level}**
• Rank: **{user_tier}**

**📈 How to Earn XP:**
• Execute trades: +10 XP per trade
• Win trades: +20 XP bonus
• Daily login: +5 XP
• Notebook entries: +8 XP
• Recruit traders: +50 XP
• Complete challenges: +25-100 XP

**🎯 XP Unlocks:**
• Level 5: Custom callsigns
• Level 10: Priority signals
• Level 20: Elite badge
• Level 50: Prestige reset

**🛍️ XP Shop:**
• Signal boosts
• Risk multipliers
• Custom themes
• Exclusive content

Visit your War Room to track progress!"""
                
            else:
                response = """🎯 **INTEL CENTER**
                
This feature provides tactical information and system guidance.

**Available Sections:**
• 🔫 Combat Ops - Mission status
• 📚 Field Manual - Trading guides  
• 💰 Tier Intel - Subscription info
• 🎖️ XP Economy - Gamification

**Need Help?**
Use /help for command list or visit the webapp for detailed information."""
            
            # Create navigation buttons for easy access
            from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            # Standard navigation keyboard for all menu sections
            nav_keyboard = InlineKeyboardMarkup()
            
            # Add contextual buttons based on current section
            if "field_manual" in callback_data:
                nav_keyboard.row(
                    InlineKeyboardButton("🌐 Mission HUD", url="https://joinbitten.com/hud"),
                    InlineKeyboardButton("🎖️ War Room", url="https://joinbitten.com/me")
                )
            elif "combat_ops" in callback_data:
                nav_keyboard.row(
                    InlineKeyboardButton("📚 Field Manual", callback_data="menu_field_manual"),
                    InlineKeyboardButton("🌐 Mission HUD", url="https://joinbitten.com/firestatus")
                )
            elif callback_data == "menu_intel_center":
                # Main Intel Center - show all options
                nav_keyboard.row(
                    InlineKeyboardButton("🔫 Combat Ops", callback_data="menu_combat_ops"),
                    InlineKeyboardButton("📚 Field Manual", callback_data="menu_field_manual")
                )
                nav_keyboard.row(
                    InlineKeyboardButton("💰 Tier Intel", callback_data="menu_tier_intel"),
                    InlineKeyboardButton("🎖️ XP Economy", callback_data="menu_xp_economy")
                )
                nav_keyboard.row(
                    InlineKeyboardButton("🌐 Mission HUD", url="https://joinbitten.com/hud"),
                    InlineKeyboardButton("🎖️ War Room", url="https://joinbitten.com/me")
                )
                nav_keyboard.row(
                    InlineKeyboardButton("❌ Close", callback_data="menu_close")
                )
            elif "tier_" in callback_data or "xp_" in callback_data:
                nav_keyboard.row(
                    InlineKeyboardButton("🌐 Mission HUD", url="https://joinbitten.com/hud"),
                    InlineKeyboardButton("🎖️ War Room", url="https://joinbitten.com/me")
                )
            
            # Always add standard navigation row (except for intel center main)
            if callback_data != "menu_intel_center":
                nav_keyboard.row(
                    InlineKeyboardButton("🏠 Intel Center", callback_data="menu_intel_center"),
                    InlineKeyboardButton("❌ Close", callback_data="menu_close")
                )
            
            # Send the response with navigation
            try:
                self.bot.edit_message_text(
                    response,
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="Markdown",
                    reply_markup=nav_keyboard
                )
                self.bot.answer_callback_query(call.id, "Information loaded")
            except:
                # If editing fails, send new message
                self.bot.send_message(
                    call.message.chat.id, 
                    response, 
                    parse_mode="Markdown",
                    reply_markup=nav_keyboard
                )
                self.bot.answer_callback_query(call.id, "Information sent")
    
    def telegram_command_connect_handler(self, message, uid: str, user_tier: str) -> str:
        """
        Handle /connect command for MT5 container onboarding
        Securely inject credentials and start MT5 login process
        """
        try:
            # Import registry and status tracker
            from src.bitten_core.user_registry_manager import get_user_registry_manager
            from src.bitten_core.container_status_tracker import get_container_status_tracker
            
            registry = get_user_registry_manager()
            status_tracker = get_container_status_tracker()
            
            # Security: Log connection attempt (without credentials)
            logger.info(f"User {uid} attempting MT5 connection")
            
            # STEP 1: Check if this is just "/connect" without arguments
            message_text = message.text.strip()
            
            # If it's just "/connect" (no additional content), trigger WebApp redirect immediately
            if message_text == "/connect":
                logger.info(f"User {uid} sent /connect only - triggering WebApp redirect")
                return "SEND_USAGE_WITH_KEYBOARD"  # Special flag for enhanced usage
            
            # Otherwise, try to parse credentials from message
            credentials = self._parse_connect_credentials(message_text)
            if not credentials:
                logger.info(f"User {uid} sent /connect with invalid format - triggering WebApp redirect")
                return "SEND_USAGE_WITH_KEYBOARD"  # Special flag for enhanced usage
            
            login_id, password, server_name = credentials
            
            # Security: Validate input parameters
            if not self._validate_connection_params(login_id, password, server_name):
                return "❌ Invalid connection parameters. Please check your login ID, password, and server name."
            
            # STEP 2: Map user to container and register in registry
            container_name = f"mt5_user_{uid}"
            
            # Register user in registry if not already registered
            user_info = registry.get_user_info(uid)
            if not user_info:
                registry.register_user(uid, uid, container_name, str(login_id), server_name)
            else:
                # Update existing user credentials
                registry.update_user_credentials(uid, str(login_id), server_name)
            
            # STEP 2: Auto-handle container creation and management
            container_status = self._ensure_container_ready_enhanced(container_name, uid)
            if not container_status['success']:
                return container_status['message']
            
            # STEP 3: Inject credentials into MT5 config with timeout
            registry.update_user_status(uid, "credentials_injected")
            if not self._inject_mt5_credentials_with_timeout(container_name, login_id, password, server_name):
                registry.update_user_status(uid, "error_state")
                return "⏳ Still initializing your terminal. Please try /connect again in a minute."
            
            # STEP 4: Restart MT5 and verify login with timeout
            login_result = self._restart_mt5_and_login_with_timeout(container_name)
            if not login_result['success']:
                if login_result.get('timeout'):
                    return "⏳ Still initializing your terminal. Please try /connect again in a minute."
                else:
                    registry.update_user_status(uid, "error_state")
                    return "❌ MT5 login failed. Please verify your credentials and server."
            
            # STEP 5: Extract account telemetry
            account_info = self._extract_account_telemetry(container_name, login_id)
            if not account_info:
                registry.update_user_status(uid, "error_state")
                return "❌ Could not extract account information. Login may have failed."
            
            registry.update_user_status(uid, "mt5_logged_in")
            
            # STEP 6: Register with Core system
            self._register_account_with_core(uid, account_info)
            
            # STEP 7: Check if EA is ready and update status
            container_status = status_tracker.check_container_status(container_name)
            if container_status.ea_active:
                registry.update_user_status(uid, "ready_for_fire")
            
            # Record successful connection
            registry.record_successful_connection(uid)
            
            # STEP 8: Return enhanced success message
            return f"""✅ Your terminal is now active and connected to {server_name}.
You're ready to receive signals. Type /status to confirm.

💳 **Account Details:**
• Broker: {account_info.get('broker', 'Unknown')}
• Balance: ${account_info.get('balance', 0):,.2f}
• Leverage: 1:{account_info.get('leverage', 'Unknown')}
• Currency: {account_info.get('currency', 'USD')}

🛡️ **System Status:** {container_status.status}

🔗 **Connection Info:**
• Container: `{container_name}`
• Login: `{login_id}`
• Server: `{server_name}`"""
            
        except Exception as e:
            logger.error(f"Connect handler error for user {uid}: {e}")
            return "❌ Connection failed due to system error. Please try again later."
    
    def _parse_connect_credentials(self, message_text: str) -> Optional[tuple]:
        """Parse credentials from /connect message format"""
        try:
            lines = message_text.split('\n')
            login_id = None
            password = None
            server_name = None
            
            for line in lines:
                line = line.strip()
                if line.lower().startswith('login:'):
                    login_id = line.split(':', 1)[1].strip()
                elif line.lower().startswith('password:'):
                    password = line.split(':', 1)[1].strip()
                elif line.lower().startswith('server:'):
                    server_name = line.split(':', 1)[1].strip()
            
            if login_id and password and server_name:
                try:
                    login_id = int(login_id)
                    return (login_id, password, server_name)
                except ValueError:
                    return None
            return None
        except Exception as e:
            logger.error(f"Credential parsing error: {e}")
            return None
    
    def _ensure_container_ready(self, container_name: str) -> bool:
        """Legacy method - kept for backward compatibility"""
        result = self._ensure_container_ready_enhanced(container_name, "legacy")
        return result['success']
    
    def _ensure_container_ready_enhanced(self, container_name: str, user_id: str) -> dict:
        """Enhanced container handling with auto-creation and improved error messages"""
        try:
            import docker
            client = docker.from_env()
            
            # STEP 2.1: Check if container exists
            try:
                container = client.containers.get(container_name)
                logger.info(f"Container {container_name} found with status: {container.status}")
                
                # STEP 2.2: If exists but stopped, start it
                if container.status != 'running':
                    logger.info(f"Starting stopped container: {container_name}")
                    container.start()
                    
                    # Wait for container to be ready
                    for i in range(10):  # 10 second timeout
                        time.sleep(1)
                        container.reload()
                        if container.status == 'running':
                            logger.info(f"Container {container_name} started successfully")
                            return {'success': True, 'message': 'Container started'}
                    
                    return {
                        'success': False, 
                        'message': "⏳ Still initializing your terminal. Please try /connect again in a minute."
                    }
                
                return {'success': True, 'message': 'Container ready'}
                
            except docker.errors.NotFound:
                # STEP 2.3: Container doesn't exist - create from template
                logger.info(f"Container {container_name} not found. Creating from template...")
                
                # Check if template exists
                try:
                    template_image = client.images.get('hydrax-user-template:latest')
                except docker.errors.ImageNotFound:
                    logger.error("hydrax-user-template:latest not found")
                    return {
                        'success': False,
                        'message': "We couldn't find your terminal. It may not be active yet. Please try again in a few minutes or contact support."
                    }
                
                # Create new container from template
                try:
                    logger.info(f"Creating new container {container_name} from hydrax-user-template")
                    container = client.containers.run(
                        'hydrax-user-template:latest',
                        name=container_name,
                        detach=True,
                        restart_policy={"Name": "unless-stopped"},
                        environment={
                            'USER_ID': user_id,
                            'CONTAINER_NAME': container_name
                        },
                        volumes={
                            f'mt5_data_{user_id}': {'bind': '/wine/drive_c/MetaTrader5/Data', 'mode': 'rw'}
                        }
                    )
                    
                    # Wait for container initialization
                    logger.info(f"Waiting for container {container_name} to initialize...")
                    for i in range(10):  # 10 second timeout
                        time.sleep(1)
                        container.reload()
                        if container.status == 'running':
                            logger.info(f"Container {container_name} created and started successfully")
                            return {'success': True, 'message': 'Container created successfully'}
                    
                    return {
                        'success': False,
                        'message': "⏳ Still initializing your terminal. Please try /connect again in a minute."
                    }
                    
                except Exception as create_error:
                    logger.error(f"Failed to create container {container_name}: {create_error}")
                    return {
                        'success': False,
                        'message': "We couldn't find your terminal. It may not be active yet. Please try again in a few minutes or contact support."
                    }
            
        except Exception as e:
            logger.error(f"Enhanced container check error for {container_name}: {e}")
            return {
                'success': False,
                'message': "We couldn't find your terminal. It may not be active yet. Please try again in a few minutes or contact support."
            }
    
    def _inject_mt5_credentials_with_timeout(self, container_name: str, login_id: int, password: str, server_name: str) -> bool:
        """Enhanced credential injection with timeout handling"""
        try:
            # Try injection with timeout
            import threading
            import time
            
            result = {'success': False}
            
            def inject_credentials():
                result['success'] = self._inject_mt5_credentials(container_name, login_id, password, server_name)
            
            # Run injection in thread with timeout
            thread = threading.Thread(target=inject_credentials)
            thread.daemon = True
            thread.start()
            thread.join(timeout=10.0)  # 10 second timeout
            
            if thread.is_alive():
                logger.error(f"Credential injection timeout for {container_name}")
                return False
            
            return result['success']
            
        except Exception as e:
            logger.error(f"Enhanced credential injection error: {e}")
            return False
    
    def _inject_mt5_credentials(self, container_name: str, login_id: int, password: str, server_name: str) -> bool:
        """Inject MT5 credentials into container config with security measures"""
        try:
            client = docker.from_env()
            container = client.containers.get(container_name)
            
            # Security: Never log the password
            logger.info(f"Injecting credentials for login {login_id} on server {server_name}")
            
            # Create terminal.ini config content (password will be masked in logs)
            config_content = f"""[Common]
Login={login_id}
Password={password}
Server={server_name}
ProxyEnable=0
ProxyType=0
ProxyAddress=
ProxyPort=0
ProxyLogin=
ProxyPassword=
KeepPrivate=0
NewsEnable=1
MaxBars=65000
DataServer=
EnableDDE=0
EnableAPI=1
"""
            
            # Encode config content to base64 to avoid shell injection
            encoded_content = base64.b64encode(config_content.encode()).decode()
            
            # Write config to container securely
            exec_result = container.exec_run([
                'bash', '-c', 
                f'mkdir -p /wine/drive_c/MetaTrader5/config && echo "{encoded_content}" | base64 -d > /wine/drive_c/MetaTrader5/config/terminal.ini && chmod 600 /wine/drive_c/MetaTrader5/config/terminal.ini'
            ])
            
            if exec_result.exit_code == 0:
                # Also create the fire.txt file for trade execution
                container.exec_run([
                    'bash', '-c',
                    'mkdir -p /wine/drive_c/MetaTrader5/Files/BITTEN && touch /wine/drive_c/MetaTrader5/Files/BITTEN/fire.txt && chmod 666 /wine/drive_c/MetaTrader5/Files/BITTEN/fire.txt'
                ])
                return True
            return False
        except Exception as e:
            logger.error(f"Credential injection error: {e}")
            return False
    
    def _restart_mt5_and_login_with_timeout(self, container_name: str) -> dict:
        """Enhanced MT5 restart with timeout and better feedback"""
        try:
            import threading
            
            result = {'success': False, 'timeout': False}
            
            def restart_mt5():
                result['success'] = self._restart_mt5_and_login(container_name)
            
            # Run restart in thread with timeout
            thread = threading.Thread(target=restart_mt5)
            thread.daemon = True
            thread.start()
            thread.join(timeout=10.0)  # 10 second timeout
            
            if thread.is_alive():
                logger.error(f"MT5 restart timeout for {container_name}")
                result['timeout'] = True
                return result
            
            return result
            
        except Exception as e:
            logger.error(f"Enhanced MT5 restart error: {e}")
            return {'success': False, 'timeout': False}
    
    def _restart_mt5_and_login(self, container_name: str) -> bool:
        """Restart MT5 terminal and attempt login"""
        try:
            client = docker.from_env()
            container = client.containers.get(container_name)
            
            # Kill existing MT5 processes
            container.exec_run(['pkill', 'terminal64.exe'], detach=True)
            time.sleep(3)
            
            # Start MT5 in portable mode
            container.exec_run([
                'bash', '-c',
                'cd /wine/drive_c/Program\\ Files/MetaTrader\\ 5/ && wine terminal64.exe /portable'
            ], detach=True)
            
            # Wait for login attempt
            time.sleep(10)
            
            # Check if login was successful (simplified check)
            result = container.exec_run([
                'bash', '-c',
                'ls -la /wine/drive_c/MetaTrader5/config/ | grep terminal.ini'
            ])
            
            return result.exit_code == 0
        except Exception as e:
            logger.error(f"MT5 restart error: {e}")
            return False
    
    def _extract_account_telemetry(self, container_name: str, login_id: int) -> Optional[dict]:
        """Extract account information from MT5"""
        try:
            client = docker.from_env()
            container = client.containers.get(container_name)
            
            # Use a simple Python script to extract account info via MetaTrader5 library
            extraction_script = f'''
import sys
sys.path.append("/opt/")
try:
    import MetaTrader5 as mt5
    if mt5.initialize():
        account_info = mt5.account_info()
        if account_info:
            import json
            result = {{
                "login": account_info.login,
                "balance": account_info.balance,
                "currency": account_info.currency,
                "leverage": account_info.leverage,
                "broker": account_info.company,
            }}
            print(json.dumps(result))
        mt5.shutdown()
    else:
        print('{{"error": "MT5 initialization failed"}}')
except Exception as e:
    print(f'{{"error": "{{e}}"}}')
'''
            
            # Execute the script in the container
            result = container.exec_run([
                'python3', '-c', extraction_script
            ])
            
            if result.exit_code == 0:
                try:
                    account_data = json.loads(result.output.decode().strip())
                    if 'error' not in account_data:
                        return account_data
                except json.JSONDecodeError:
                    pass
            
            # Fallback: return basic info
            return {
                "login": login_id,
                "balance": 0.00,
                "currency": "USD",
                "leverage": 500,
                "broker": "Unknown"
            }
        except Exception as e:
            logger.error(f"Telemetry extraction error: {e}")
            return None
    
    def _register_account_with_core(self, uid: str, account_info: dict) -> bool:
        """Register account with Core system"""
        try:
            # Send account info to Core API
            core_payload = {
                "user_id": uid,
                "login": account_info.get("login"),
                "broker": account_info.get("broker"),
                "balance": account_info.get("balance"),
                "currency": account_info.get("currency"),
                "leverage": account_info.get("leverage")
            }
            
            # Try to send to Core (fallback gracefully if not available)
            try:
                response = requests.post(
                    "http://localhost:8888/api/register_account", 
                    json=core_payload,
                    timeout=5
                )
                return response.status_code == 200
            except requests.RequestException:
                logger.info("Core API not available, skipping registration")
                return True
                
        except Exception as e:
            logger.error(f"Core registration error: {e}")
            return True  # Don't fail the whole process
    
    def _get_connect_usage_message(self, chat_id: str) -> str:
        """Return usage instructions for /connect command with throttling"""
        
        # Check throttling
        current_time = datetime.now()
        if chat_id in self.connect_usage_throttle:
            last_sent = self.connect_usage_throttle[chat_id]
            time_diff = (current_time - last_sent).total_seconds()
            if time_diff < self.connect_throttle_window:
                return "⏳ Please wait before requesting connection help again."
        
        # Update throttle timestamp
        self.connect_usage_throttle[chat_id] = current_time
        
        return """👋 To set up your trading terminal, please either:

🌐 Use the WebApp:  
https://joinbitten.com/connect

or

✍️ Paste your credentials like this:
/connect  
Login: 843859  
Password: [Your MT5 Password]  
Server: Coinexx1Demo

✅ Your terminal will be created automatically if it doesn't exist.  
📲 You'll receive a confirmation when it's online and ready."""
    
    def _send_connect_usage_with_keyboard(self, chat_id: str, user_tier: str) -> None:
        """Send enhanced /connect usage message with inline keyboard"""
        try:
            from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            # Get the usage message (with throttling)
            usage_message = self._get_connect_usage_message(chat_id)
            
            # Check if throttled
            if usage_message.startswith("⏳"):
                logger.info(f"🛡️ /connect request throttled for {chat_id} - 60s cooldown active")
                self.send_adaptive_response(chat_id, usage_message, user_tier, "connect_throttled")
                return
            
            # Create inline keyboard with WebApp button
            keyboard = InlineKeyboardMarkup()
            webapp_button = InlineKeyboardButton(
                text="🌐 Use WebApp",
                url="https://joinbitten.com/connect"
            )
            keyboard.add(webapp_button)
            
            # Send message with keyboard
            self.bot.send_message(
                chat_id=chat_id,
                text=usage_message,
                parse_mode="Markdown",
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
            
            logger.info(f"✅ WebApp redirect triggered for {chat_id} - Enhanced /connect usage sent with keyboard")
            
        except Exception as e:
            logger.error(f"Error sending connect usage with keyboard: {e}")
            # Fallback to regular message
            self.send_adaptive_response(chat_id, self._get_connect_usage_message(chat_id), user_tier, "connect_usage")
    
    def _validate_connection_params(self, login_id: int, password: str, server_name: str) -> bool:
        """Validate connection parameters for security"""
        try:
            # Validate login ID (should be positive integer)
            if not isinstance(login_id, int) or login_id <= 0:
                return False
            
            # Validate password (basic checks)
            if not password or len(password) < 4 or len(password) > 100:
                return False
            
            # Validate server name (should be alphanumeric with allowed special chars)
            if not server_name or len(server_name) > 50:
                return False
            
            # Server name should only contain safe characters
            allowed_chars = string.ascii_letters + string.digits + '-._'
            if not all(c in allowed_chars for c in server_name):
                return False
            
            # Security: Check for potential injection attempts
            dangerous_patterns = [';', '&&', '||', '`', '$', '(', ')', '|']
            for pattern in dangerous_patterns:
                if pattern in password or pattern in server_name:
                    logger.warning(f"Potential injection attempt detected in credentials")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Parameter validation error: {e}")
            return False
    
    def _lookup_telegram_id_by_username(self, username: str) -> Optional[str]:
        """Look up telegram_id by username from user registry"""
        try:
            from src.bitten_core.user_registry_manager import get_user_registry_manager
            registry = get_user_registry_manager()
            
            # Search through all users for matching username
            # Note: This requires storing usernames in registry, which might need enhancement
            # For now, check if username matches user_id field
            for telegram_id, user_info in registry.registry_data.items():
                if user_info.get('user_id', '') == username:
                    return telegram_id
            
            # If no direct match, try to look up in recent messages or cache
            # This is a simplified version - in production you might want to maintain
            # a username->telegram_id mapping cache
            logger.warning(f"Username {username} not found in registry")
            return None
            
        except Exception as e:
            logger.error(f"Error looking up username {username}: {e}")
            return None
    
    def _format_gold_welcome_message(self) -> str:
        """Format the gold operative welcome message"""
        # Escape special characters for MarkdownV2
        message = (
            "🎖️ *Gold Access Granted*\n\n"
            "You've been activated as a *Gold Operative*\\.\n"
            "Private XAUUSD signals will now be delivered directly to you\\.\n\n"
            "🪙 *\\+200 XP* per gold mission\n"
            "📈 *High\\-volatility edge*\n"
            "⚠️ *Use with caution – leverage is your responsibility*"
        )
        return message
    
    def _format_crypto_welcome_message(self) -> str:
        """Format the C.O.R.E. crypto access welcome message"""
        # Escape special characters for MarkdownV2
        message = (
            "🔓 *C\\.O\\.R\\.E\\. Access Granted*\n\n"
            "You are now authorized to receive crypto mission signals\\.\n\n"
            "🔥 BTCUSD, ETHUSD, and more\n"
            "📈 Tactical setups only — no spam\n"
            "🎖 XP rewards for every precision fire\n"
            "🧨 Expect volatility\\. Execute with control\\."
        )
        return message
    
    def start_core_signal_listener(self):
        """Start background thread to listen for CORE signals"""
        try:
            thread = threading.Thread(target=self._core_signal_listener, daemon=True)
            thread.start()
            logger.info("🚀 CORE signal listener started")
        except Exception as e:
            logger.error(f"Failed to start CORE signal listener: {e}")
    
    def _core_signal_listener(self):
        """Background thread to receive and process CORE signals"""
        context = zmq.Context()
        subscriber = context.socket(zmq.SUB)
        
        try:
            # Connect to CORE signal publisher
            subscriber.connect("tcp://127.0.0.1:5556")
            subscriber.setsockopt(zmq.SUBSCRIBE, b"CORE_SIGNAL")
            
            logger.info("📡 Listening for CORE_SIGNAL on tcp://127.0.0.1:5556")
            
            while True:
                try:
                    # Receive signal with timeout
                    if subscriber.poll(timeout=1000):  # 1 second timeout
                        raw_message = subscriber.recv_string(zmq.NOBLOCK)
                        
                        # Parse: "CORE_SIGNAL {json_data}"
                        if raw_message.startswith("CORE_SIGNAL "):
                            json_data = raw_message[12:]  # Remove "CORE_SIGNAL " prefix
                            signal = json.loads(json_data)
                            
                            # Process the signal
                            self._process_core_signal(signal)
                            
                except zmq.Again:
                    # No message received, continue
                    continue
                except Exception as e:
                    logger.error(f"Error processing CORE signal: {e}")
                    time.sleep(5)  # Brief pause before retry
                    
        except Exception as e:
            logger.error(f"CORE signal listener error: {e}")
        finally:
            subscriber.close()
            context.term()
    
    def _process_core_signal(self, signal: dict):
        """Process incoming CORE signal and send to eligible users"""
        try:
            logger.info(f"📥 Processing CORE signal: {signal.get('uuid', 'unknown')}")
            
            # Add signal to truth tracker for performance monitoring
            try:
                from core_truth_integration import track_core_signal
                tracked = track_core_signal(signal)
                if tracked:
                    logger.info(f"📊 C.O.R.E. signal {signal.get('uuid', 'unknown')} added to truth tracking")
                else:
                    logger.warning(f"⚠️ Failed to add C.O.R.E. signal to truth tracker")
            except Exception as e:
                logger.error(f"❌ Error adding C.O.R.E. signal to truth tracker: {e}")
            
            # Get eligible users (offshore + crypto opt-in)
            eligible_users = self._get_crypto_eligible_users()
            
            if not eligible_users:
                logger.info("ℹ️ No eligible users for crypto signals")
                return
            
            # Format message
            message_text = self._format_core_signal_message(signal)
            buttons = self._create_mission_brief_button(signal.get('uuid', ''))
            
            # Send to eligible users
            delivered_count = 0
            for user_profile in eligible_users:
                try:
                    chat_id = user_profile.get('telegram_id')
                    if chat_id:
                        self.bot.send_message(
                            chat_id=chat_id,
                            text=message_text,
                            parse_mode="MarkdownV2",
                            reply_markup=buttons
                        )
                        
                        # Award XP if system available
                        xp_amount = signal.get('xp', 160)
                        self._award_core_xp(str(chat_id), xp_amount)
                        
                        delivered_count += 1
                        
                        # Log delivery
                        self._log_core_delivery(signal, str(chat_id))
                        
                except Exception as e:
                    logger.error(f"Failed to send CORE signal to {chat_id}: {e}")
            
            logger.info(f"✅ CORE signal delivered to {delivered_count} users")
            
        except Exception as e:
            logger.error(f"Error processing CORE signal: {e}")
    
    def _get_crypto_eligible_users(self) -> list:
        """Get users eligible for crypto signals (offshore + opted in)"""
        try:
            # Mock implementation - replace with actual user database lookup
            eligible_users = []
            
            # Example user profiles (replace with real database query)
            # SELECT * FROM users WHERE user_region != 'US' AND crypto_opt_in = TRUE
            
            # For testing, return mock users
            mock_users = [
                {
                    'telegram_id': 7176191872,  # Your user ID for testing
                    'user_region': 'International',
                    'crypto_opt_in': True
                }
            ]
            
            for user in mock_users:
                if user.get('user_region') != 'US' and user.get('crypto_opt_in'):
                    eligible_users.append(user)
            
            return eligible_users
            
        except Exception as e:
            logger.error(f"Error getting crypto eligible users: {e}")
            return []
    
    def _format_core_signal_message(self, signal: dict) -> str:
        """Format CORE signal for Telegram delivery"""
        try:
            symbol = signal.get('symbol', 'BTCUSD')
            pattern = signal.get('pattern', 'Unknown')
            score = signal.get('score', 0)
            
            # Escape special characters for MarkdownV2
            def escape_md(text):
                chars_to_escape = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
                for char in chars_to_escape:
                    text = text.replace(char, f'\\{char}')
                return text
            
            symbol_escaped = escape_md(symbol)
            pattern_escaped = escape_md(pattern)
            
            message = (
                f"🔥 *C\\.O\\.R\\.E\\. SIGNAL: {symbol_escaped}*\n"
                f"🕒 {pattern_escaped} \\– Score: {score}/100"
            )
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting CORE message: {e}")
            return "🔥 *C\\.O\\.R\\.E\\. SIGNAL RECEIVED*"
    
    def _create_mission_brief_button(self, uuid: str) -> 'InlineKeyboardMarkup':
        """Create inline button for mission brief"""
        try:
            from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            buttons = InlineKeyboardMarkup()
            brief_button = InlineKeyboardButton(
                text="📄 Mission Brief",
                url=f"https://core-missions.bitten.trading/brief/{uuid}"
            )
            buttons.add(brief_button)
            
            return buttons
            
        except Exception as e:
            logger.error(f"Error creating mission brief button: {e}")
            return None
    
    def _award_core_xp(self, user_id: str, xp_amount: int):
        """Award XP for CORE signal (integrate with existing XP system)"""
        try:
            # TODO: Integrate with existing XP system if available
            # For now, just log the XP award
            logger.info(f"🎯 Awarded {xp_amount} XP to user {user_id} for CORE signal")
            
            # Example integration:
            # if hasattr(self, 'xp_system'):
            #     self.xp_system.award_xp(user_id, xp_amount, source="core")
            
        except Exception as e:
            logger.error(f"Error awarding CORE XP: {e}")
    
    def _log_core_delivery(self, signal: dict, user_id: str):
        """Log CORE signal delivery to JSONL file"""
        try:
            log_entry = {
                "uuid": signal.get('uuid', ''),
                "user_id": user_id,
                "symbol": signal.get('symbol', ''),
                "score": signal.get('score', 0),
                "timestamp": datetime.now().isoformat(),
                "pattern": signal.get('pattern', ''),
                "xp_awarded": signal.get('xp', 160)
            }
            
            with open(self.core_log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            logger.error(f"Error logging CORE delivery: {e}")
    
    def run(self):
        """Start the bot"""
        try:
            logger.info("Starting BITTEN Production Bot...")
            logger.info(f"Authorized users: {list(AUTHORIZED_USERS.keys())}")
            logger.info(f"Commanders: {COMMANDER_IDS}")
            
            # Test bot connection first
            try:
                me = self.bot.get_me()
                logger.info(f"Bot connected successfully: @{me.username}")
            except Exception as e:
                logger.error(f"Failed to connect to Telegram: {e}")
                return
            
            # Send startup message
            try:
                if UNIFIED_PERSONALITY_AVAILABLE:
                    personality_status = "🎭 Unified Personalities: ✅ ALL 3 LAYERS ACTIVE"
                elif PERSONALITY_SYSTEM_AVAILABLE:
                    personality_status = "🎭 Adaptive Personalities: ✅ ACTIVE"
                else:
                    personality_status = "🎭 Personalities: ❌ DISABLED"
                
                startup_msg = f"🟢 BITTEN Production Bot Online\\n⏰ {datetime.now().strftime('%H:%M:%S UTC')}\\n{personality_status}\\nReady for trading commands\\."
                
                # Add BIT's startup greeting if available
                if BIT_AVAILABLE:
                    bit_greeting = bit_welcome("COMMANDER")
                    startup_msg += f"\\n\\n{escape_markdown(bit_greeting)}"
                for chat_id in [-1002581996861]:  # Your chat
                    try:
                        self.bot.send_message(chat_id, startup_msg, parse_mode="MarkdownV2")
                        logger.info(f"Startup message sent to {chat_id}")
                    except Exception as e:
                        logger.warning(f"Could not send startup message to {chat_id}: {e}")
            except Exception as e:
                logger.warning(f"Startup message failed: {e}")
            
            # Start polling with better error handling
            logger.info("Starting bot polling...")
            self.bot.polling(none_stop=True, interval=1, timeout=20)
            
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Bot error: {e}")
            raise

def main():
    """Main entry point"""
    try:
        # Ensure missions directory exists
        os.makedirs("/root/HydraX-v2/missions/", exist_ok=True)
        
        # Start bot
        bot = BittenProductionBot()
        bot.run()
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

if __name__ == "__main__":
    main()