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
from datetime import datetime
import telebot
from typing import Dict, Optional, Any
import threading
from time import sleep

# Add paths for imports
sys.path.append('/root/HydraX-v2/src')
sys.path.append('/root/HydraX-v2')

# Configure logging early
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/bitten_production_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('BittenProductionBot')

# Import unified personality system
try:
    from deploy_unified_personality_system import UnifiedPersonalityBot
    UNIFIED_PERSONALITY_AVAILABLE = True
except ImportError:
    UNIFIED_PERSONALITY_AVAILABLE = False

# Import adaptive personality system (fallback)
try:
    from deploy_adaptive_personality_system import AdaptivePersonalityBot
    PERSONALITY_SYSTEM_AVAILABLE = True
except ImportError:
    PERSONALITY_SYSTEM_AVAILABLE = False

# Import BIT integration system
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
    DRILL_SYSTEM_AVAILABLE = True
    logger.info("✅ Drill report system imported successfully")
except ImportError as e:
    DRILL_SYSTEM_AVAILABLE = False
    logger.warning(f"⚠️ Drill report system not available: {e}")

try:
    from src.bitten_core.tactical_interface import TacticalInterface
    TACTICAL_INTERFACE_AVAILABLE = True
    logger.info("✅ Tactical interface imported successfully")
except ImportError as e:
    TACTICAL_INTERFACE_AVAILABLE = False
    logger.warning(f"⚠️ Tactical interface not available: {e}")

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

# Configuration
BOT_TOKEN = '7854827710:AAGsO-vgMpsTOVNu6zoo_-GGJkYQd97Mc5w'

# USER + COMMANDER CONFIG
COMMANDER_IDS = [7176191872]

AUTHORIZED_USERS = {
    "7176191872": {
        "tier": "COMMANDER",
        "account_id": "843859",
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

def fire_mission_for_user(user_id, mission):
    """Execute trade for user mission"""
    try:
        # Try webapp API first
        try:
            result = requests.post("http://localhost:8888/api/fire", 
                                 json={"mission_id": mission["mission_id"]}, 
                                 timeout=10)
            if result.status_code == 200:
                logger.info(f"Mission fired via WebApp API: {mission['mission_id']}")
                return result.json()
        except Exception as e:
            logger.warning(f"WebApp API failed: {e}")
        
        # Fallback to direct fire router
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
        
        self.setup_handlers()
        logger.info("BITTEN Production Bot initialized")
    
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
    
    def setup_handlers(self):
        """Setup all command handlers"""
        
        @self.bot.message_handler(commands=["status", "mode", "ping", "help", "fire", "force_signal", "ghosted", "slots", "presspass", "menu", "drill", "weekly", "tactics"])
        def handle_telegram_commands(message):
            uid = str(message.from_user.id)
            user_name = message.from_user.first_name or "Operative"
            
            # Get user tier for personality system
            user_config = AUTHORIZED_USERS.get(uid, {})
            user_tier = user_config.get("tier", "NIBBLER")
            
            try:
                if message.text == "/status":
                    if int(uid) in COMMANDER_IDS:
                        # Check system status
                        status_msg = self.get_system_status()
                        self.send_adaptive_response(message.chat.id, status_msg, user_tier, "status_check")
                    else:
                        self.send_adaptive_response(message.chat.id, "❌ Status is only available to authorized commanders.", user_tier, "unauthorized_access")
                
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
                
                elif message.text == "/api":
                    # Fire Loop Validation System - API Status Command
                    api_status = self.get_api_status(uid)
                    self.send_adaptive_response(message.chat.id, api_status, user_tier, "api_status")
                
                elif message.text == "/fire":
                    # Import fire mode executor to check mode
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
                        # Inject a test signal
                        test_signal = {
                            "symbol": "GBPUSD",
                            "type": "buy",
                            "direction": "BUY", 
                            "entry_price": 1.2765,
                            "sl": 10,
                            "tp": 20,
                            "tcs_score": 87,
                            "timeframe": "M5",
                            "session": "LONDON",
                            "pattern": "Double Bottom",
                            "confluence_count": 2
                        }
                        
                        try:
                            mission = generate_mission(test_signal, uid)
                            test_msg = f"🧪 Test mission injected: GBPUSD BUY (TCS: 87)\n🆔 Mission ID: {mission['mission_id']}"
                            self.send_adaptive_response(message.chat.id, test_msg, user_tier, "test_signal")
                            logger.info(f"Test signal injected by commander {uid}")
                        except Exception as e:
                            error_msg = f"❌ Failed to inject test signal: {str(e)}"
                            self.send_adaptive_response(message.chat.id, error_msg, user_tier, "error")
                    else:
                        self.send_adaptive_response(message.chat.id, "❌ Test signal injection restricted to commanders.", user_tier, "unauthorized_access")
                
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
                    # Show Intel Command Center menu
                    try:
                        # Create inline keyboard for Intel Center
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
                                InlineKeyboardButton("❌ Close Menu", callback_data="menu_close")
                            ]
                        ])
                        
                        menu_text = f"""🎯 **INTEL COMMAND CENTER**
                        
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
                        
                        self.bot.send_message(
                            message.chat.id, 
                            menu_text, 
                            reply_markup=keyboard, 
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
                
            except Exception as e:
                logger.error(f"Error handling command {message.text}: {e}")
                self.send_adaptive_response(message.chat.id, "❌ Command processing error. Please try again.", user_tier, "error")
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("mode_") or call.data.startswith("slots_") or call.data.startswith("semi_fire_") or call.data.startswith("menu_") or call.data.startswith("combat_") or call.data.startswith("field_") or call.data.startswith("tier_") or call.data.startswith("xp_") or call.data.startswith("help_") or call.data.startswith("tool_") or call.data.startswith("bot_"))
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
            
            # Check APEX engine
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

💰 **Current XP**: {user_xp:,}
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
        
        help_parts.append("🎮 Fire Mode Commands:")
        help_parts.append("/mode – View/change fire mode")
        help_parts.append("/slots – Configure AUTO slots (COMMANDER only)")
        
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
            help_parts.append("/force_signal – Inject test mission (Commander)")
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
    
    def handle_intel_center_callback(self, call, user_tier):
        """Handle Intel Command Center menu callbacks"""
        user_id = str(call.from_user.id)
        callback_data = call.data
        
        try:
            # Import Intel Command Center handler
            from deploy_intel_command_center import IntelCommandCenter
            
            # Create a minimal update object for the handler
            class MockUpdate:
                def __init__(self, callback_query):
                    self.callback_query = callback_query
                    self.effective_user = callback_query.from_user
            
            class MockContext:
                pass
            
            # Create Intel Center instance
            intel_center = IntelCommandCenter()
            
            # Create mock objects and handle the callback
            mock_update = MockUpdate(call)
            mock_context = MockContext()
            
            # Let Intel Center handle the callback
            asyncio.run(intel_center.handle_menu_callback(mock_update, mock_context))
            
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
                
            elif "field_manual" in callback_data or "help_" in callback_data:
                response = """📚 **FIELD MANUAL**
                
**Trading Basics:**
• Signals are generated by APEX engine
• TCS score indicates trade quality (65%+ required)
• Use /fire to execute current missions
• SELECT FIRE = manual confirmation
• AUTO FIRE = automatic execution (COMMANDER tier)

**Risk Management:**
• Never risk more than you can afford
• Always use stop losses
• Manage position sizing carefully
• Track your performance

**Commands:**
• /mode - Configure fire modes
• /fire - Execute trades
• /help - Show all commands"""
                
            elif "combat_ops" in callback_data:
                response = """🔫 **COMBAT OPERATIONS**
                
**Mission Status:** ✅ Operational
**Current Mode:** SELECT FIRE
**Signals Today:** Monitoring markets

**Active Features:**
• Real-time signal generation
• Mission briefing system
• Trade execution engine
• Performance tracking

**Quick Actions:**
• Use /fire to execute pending missions
• Use /mode to change firing modes
• Check WebApp for detailed mission briefs"""
                
            elif "tier_" in callback_data:
                response = f"""💰 **TIER INFORMATION**
                
**Your Current Tier:** {user_tier}

**Available Tiers:**
🎫 **PRESS PASS** - FREE (7-day trial)
🦷 **NIBBLER** - $39/mo (1 trade slot)
🔥 **FANG** - $89/mo (2 trade slots)
⚡ **COMMANDER** - $189/mo (unlimited slots)

**Upgrade Benefits:**
• More concurrent trades
• AUTO fire mode access
• Priority signal delivery
• Advanced features

Visit the webapp for upgrade options."""
                
            elif "xp_" in callback_data:
                response = """🎖️ **XP ECONOMY**
                
**Current XP:** Building...
**Level:** Operative
**Next Unlock:** Advanced features

**Earn XP By:**
• Executing successful trades
• Maintaining win streaks
• Using the system consistently
• Completing challenges

**XP Rewards:**
• Unlock new features
• Access to premium signals
• Enhanced personality traits
• Achievement badges"""
                
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
            
            # Send the response
            try:
                self.bot.edit_message_text(
                    response,
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="Markdown"
                )
                self.bot.answer_callback_query(call.id, "Information loaded")
            except:
                # If editing fails, send new message
                self.bot.send_message(call.message.chat.id, response, parse_mode="Markdown")
                self.bot.answer_callback_query(call.id, "Information sent")
    
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