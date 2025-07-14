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
from datetime import datetime
import telebot
from typing import Dict, Optional, Any

# Add paths for imports
sys.path.append('/root/HydraX-v2/src')
sys.path.append('/root/HydraX-v2')

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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/bitten_production_bot.log'),
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
        "tier": "APEX",
        "account_id": "843859",
        "bridge_id": "bridge_01"
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
        self.setup_handlers()
        logger.info("BITTEN Production Bot initialized")
    
    def setup_handlers(self):
        """Setup all command handlers"""
        
        @self.bot.message_handler(commands=["status", "mode", "ping", "help", "fire", "force_signal", "ghosted"])
        def handle_telegram_commands(message):
            uid = str(message.from_user.id)
            user_name = message.from_user.first_name or "Operative"
            
            try:
                if message.text == "/status":
                    if int(uid) in COMMANDER_IDS:
                        # Check system status
                        status_msg = self.get_system_status()
                        self.bot.reply_to(message, escape_markdown(status_msg), parse_mode="MarkdownV2")
                    else:
                        self.bot.reply_to(message, "❌ Status is only available to authorized commanders.")
                
                elif message.text == "/mode":
                    if int(uid) in COMMANDER_IDS:
                        user_config = AUTHORIZED_USERS.get(uid, {})
                        tier = user_config.get("tier", "UNKNOWN")
                        mode_msg = f"🎮 Mode: {tier}-BEAST (live fire enabled)"
                        self.bot.reply_to(message, escape_markdown(mode_msg), parse_mode="MarkdownV2")
                    else:
                        self.bot.reply_to(message, "❌ Mode command restricted to commanders.")
                
                elif message.text == "/ping":
                    ping_msg = f"🛰️ Pong. BITTEN is online and synced.\n⏰ {datetime.now().strftime('%H:%M:%S UTC')}"
                    self.bot.reply_to(message, escape_markdown(ping_msg), parse_mode="MarkdownV2")
                
                elif message.text == "/help":
                    help_msg = self.get_help_message(uid)
                    self.bot.reply_to(message, escape_markdown(help_msg), parse_mode="MarkdownV2")
                
                elif message.text == "/fire":
                    # FIRE logic: fetch user's pending mission
                    mission = get_pending_mission_for_user(uid)
                    if mission:
                        result = fire_mission_for_user(uid, mission)
                        if result.get("success"):
                            symbol = mission.get("symbol", "UNKNOWN")
                            fire_msg = f"🎯 Trade fired: {symbol}\n✅ Execution successful"
                        else:
                            fire_msg = f"❌ Trade execution failed: {result.get('message', 'Unknown error')}"
                        self.bot.reply_to(message, escape_markdown(fire_msg), parse_mode="MarkdownV2")
                    else:
                        self.bot.reply_to(message, "❌ No active mission found. Wait for a signal or use /force_signal.")
                
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
                            self.bot.reply_to(message, escape_markdown(test_msg), parse_mode="MarkdownV2")
                            logger.info(f"Test signal injected by commander {uid}")
                        except Exception as e:
                            error_msg = f"❌ Failed to inject test signal: {str(e)}"
                            self.bot.reply_to(message, escape_markdown(error_msg), parse_mode="MarkdownV2")
                    else:
                        self.bot.reply_to(message, "❌ Test signal injection restricted to commanders.")
                
                elif message.text.upper().startswith('/GHOSTED'):
                    if int(uid) in COMMANDER_IDS:
                        try:
                            # Import the ghosted command handler
                            import sys
                            sys.path.append('/root/HydraX-v2/src')
                            from bitten_core.performance_commands import handle_ghosted_command
                            
                            ghosted_report = handle_ghosted_command()
                            self.bot.reply_to(message, ghosted_report, parse_mode=None)  # No markdown parsing for report
                            logger.info(f"GHOSTED report requested by commander {uid}")
                        except Exception as e:
                            error_msg = f"❌ Failed to generate GHOSTED report: {str(e)}"
                            self.bot.reply_to(message, error_msg)
                            logger.error(f"GHOSTED command error: {e}")
                    else:
                        self.bot.reply_to(message, "❌ GHOSTED report restricted to commanders.")
                
            except Exception as e:
                logger.error(f"Error handling command {message.text}: {e}")
                self.bot.reply_to(message, "❌ Command processing error. Please try again.")
        
        @self.bot.message_handler(func=lambda message: True)
        def handle_all_messages(message):
            """Handle non-command messages"""
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
            
            # Check bridge
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex(('127.0.0.1', 9000))
                sock.close()
                if result == 0:
                    status_parts.append("Bridge: ✅ Connected")
                else:
                    status_parts.append("Bridge: ❌ No connection")
            except:
                status_parts.append("Bridge: ❌ Check failed")
            
            status_parts.append(f"You: Commander + APEX User")
            status_parts.append(f"Time: {datetime.now().strftime('%H:%M:%S UTC')}")
            
            return "\\n".join(status_parts)
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return "❌ Status check failed"
    
    def get_help_message(self, user_id):
        """Get user-specific help message"""
        is_commander = int(user_id) in COMMANDER_IDS
        
        help_parts = ["📖 Available Commands:"]
        help_parts.append("/ping – Is bot online?")
        help_parts.append("/help – Show this help")
        help_parts.append("/fire – Execute current mission")
        
        if is_commander:
            help_parts.append("/status – System check (Commander)")
            help_parts.append("/mode – Current engine mode (Commander)")
            help_parts.append("/force_signal – Inject test mission (Commander)")
            help_parts.append("/ghosted – Tactical ghosted ops report (Commander)")
        
        user_config = AUTHORIZED_USERS.get(user_id, {})
        if user_config:
            tier = user_config.get("tier", "USER")
            help_parts.append(f"Your tier: {tier}")
        
        return "\\n".join(help_parts)
    
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
                startup_msg = f"🟢 BITTEN Production Bot Online\\n⏰ {datetime.now().strftime('%H:%M:%S UTC')}\\nReady for trading commands\\."
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