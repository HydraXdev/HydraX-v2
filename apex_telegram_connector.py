#!/usr/bin/env python3
"""
APEX v5.0 Telegram Connector

Monitors APEX v5.0 log file for trading signals and sends Telegram alerts
with WebApp integration for mission briefings.

Features:
- Real-time log monitoring with cooldown protection
- Mission generation with persistent file storage
- Telegram WebApp integration
- Urgency levels based on TCS scores
- Proper error handling and logging
"""

import asyncio
import logging
import os
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Set, Optional

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import mission generator
try:
    from src.bitten_core.mission_briefing_generator_v5 import generate_mission
except ImportError:
    try:
        from bitten_core.mission_briefing_generator_v5 import generate_mission
    except ImportError:
        # Fallback implementation if module not found
        def generate_mission(signal: Dict, user_id: str) -> Dict:
            """Fallback mission generator"""
            import time
            from datetime import datetime, timedelta
            
            mission_id = f"{user_id}_{int(time.time())}"
            mission = {
                "mission_id": mission_id,
                "user_id": user_id,
                "symbol": signal["symbol"],
                "type": signal["type"],
                "tp": signal["tp"],
                "sl": signal["sl"],
                "tcs": signal["tcs_score"],
                "risk": 1.5,
                "account_balance": 2913.25,
                "lot_size": 0.12,
                "timestamp": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
                "status": "pending"
            }
            
            # Create missions directory
            missions_dir = Path("./missions")
            missions_dir.mkdir(exist_ok=True)
            
            # Save mission file
            mission_file = missions_dir / f"{mission_id}.json"
            with open(mission_file, "w") as f:
                json.dump(mission, f, indent=2)
            
            return mission

# Configuration
class Config:
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7854827710:AAGsO-vgMpsTOVNu6zoo_-GGJkYQd97Mc5w")
    CHAT_ID = os.getenv("CHAT_ID", "-1002581996861")  # Main group
    COMMANDER_ID = "7176191872"  # Commander's personal ID for dual notifications
    LOG_FILE = "/root/HydraX-v2/apex_v5_live_real.log"
    WEBAPP_URL = "https://joinbitten.com/hud"
    COOLDOWN_SECONDS = 60
    MONITOR_INTERVAL = 1.0
    
    # Signal patterns to monitor
    SIGNAL_PATTERNS = [
        "🎯 SIGNAL",
        "SIGNAL #",
        "🎯 TRADE SIGNAL"
    ]
    
    # TCS urgency levels
    TCS_CRITICAL = 85
    TCS_HIGH = 70
    TCS_MEDIUM = 50

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/apex_telegram_connector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('APEX-Telegram-Connector')

class ApexTelegramConnector:
    """Main connector class for APEX-Telegram integration"""
    
    def __init__(self):
        self.bot = None
        self.seen_signals: Set[str] = set()
        self.last_signal_time: Dict[str, datetime] = {}
        
        # Validate configuration
        if not Config.BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
        
        # Initialize bot
        self.bot = Bot(token=Config.BOT_TOKEN)
        
        # Create missions directory
        self.missions_dir = Path("./missions")
        self.missions_dir.mkdir(exist_ok=True)
        
        logger.info(f"Initialized APEX Telegram Connector")
        logger.info(f"Bot token: {Config.BOT_TOKEN[:10]}...")
        logger.info(f"Chat ID: {Config.CHAT_ID}")
        logger.info(f"Log file: {Config.LOG_FILE}")
    
    def get_urgency_level(self, tcs_score: int) -> str:
        """Determine urgency level based on TCS score"""
        if tcs_score >= Config.TCS_CRITICAL:
            return "🔴 CRITICAL"
        elif tcs_score >= Config.TCS_HIGH:
            return "🟡 HIGH"
        elif tcs_score >= Config.TCS_MEDIUM:
            return "🟢 MEDIUM"
        else:
            return "⚪ LOW"
    
    def should_send_signal(self, signal_key: str) -> bool:
        """Check if signal should be sent based on cooldown"""
        now = datetime.utcnow()
        
        if signal_key in self.last_signal_time:
            time_diff = now - self.last_signal_time[signal_key]
            if time_diff.total_seconds() < Config.COOLDOWN_SECONDS:
                logger.debug(f"Signal {signal_key} in cooldown, skipping")
                return False
        
        self.last_signal_time[signal_key] = now
        return True
    
    def parse_signal_line(self, line: str) -> Optional[Dict]:
        """Parse signal from log line"""
        try:
            # Multiple signal formats supported
            if "🎯 SIGNAL" in line:
                # Format: 🎯 SIGNAL #1: EURUSD BUY TCS:85%
                parts = line.split()
                
                # Find symbol and direction
                symbol = None
                direction = None
                tcs = None
                
                # Look for pattern after signal number
                for i, part in enumerate(parts):
                    if part.endswith(":"): # Could be signal number like "#1:"
                        # Next part should be symbol
                        if i + 1 < len(parts):
                            symbol = parts[i + 1]
                        # Part after symbol should be direction
                        if i + 2 < len(parts):
                            direction = parts[i + 2]
                    elif part.startswith("TCS:"):
                        tcs_str = part.replace("TCS:", "").replace("%", "")
                        tcs = int(tcs_str)
                
                # Alternative parsing: look for currency pairs directly
                if not symbol:
                    for part in parts:
                        if len(part) == 6 and part.isalpha() and part.isupper():
                            symbol = part
                            break
                
                # Alternative parsing: look for BUY/SELL
                if not direction:
                    for part in parts:
                        if part.upper() in ["BUY", "SELL"]:
                            direction = part.upper()
                            break
                
                if symbol and direction and tcs:
                    return {
                        "symbol": symbol,
                        "type": direction.lower(),
                        "tp": 2382.0,  # Will be calculated dynamically in production
                        "sl": 2370.0,  # Will be calculated dynamically in production
                        "tcs_score": tcs
                    }
            
            # Add more signal parsing patterns as needed
            
        except Exception as e:
            logger.error(f"Error parsing signal line: {e}")
        
        return None
    
    def format_telegram_message(self, signal: Dict, mission: Dict, urgency: str) -> tuple:
        """Format Telegram message with button markup - returns (message, keyboard)"""
        symbol = signal["symbol"].upper()
        direction = signal["type"].upper()
        tcs = signal["tcs_score"]
        
        # Create mission data with tier routing
        import json
        import urllib.parse
        mission_data = {
            'mission_id': mission['mission_id'],
            'signal': signal,
            'timestamp': mission.get('timestamp'),
            'user_tier': 'COMMANDER'  # Default tier - will be user-specific later
        }
        
        encoded_data = urllib.parse.quote(json.dumps(mission_data))
        webapp_url = f"{Config.WEBAPP_URL}?data={encoded_data}"
        
        # Two different alert templates based on TCS - ORIGINAL CORRECT FORMAT
        if tcs >= 80:
            # SNIPER OPS: High confidence (80%+)
            message = f"⚡ **SNIPER OPS** ⚡ [{tcs}%]\n🎖️ {symbol} ELITE ACCESS"
            button_text = "VIEW INTEL"
        else:
            # RAPID ASSAULT: Medium confidence (65-79%)
            message = f"🔫 **RAPID ASSAULT** [{tcs}%]\n🔥 {symbol} STRIKE 💥"
            button_text = "MISSION BRIEF"
        
        # Create inline keyboard with button
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(text=button_text, url=webapp_url)
        ]])
        
        return message, keyboard
    
    async def send_telegram_alert(self, signal: Dict, mission: Dict) -> bool:
        """Send Telegram alert for signal"""
        try:
            urgency = self.get_urgency_level(signal["tcs_score"])
            message, keyboard = self.format_telegram_message(signal, mission, urgency)
            
            await self.bot.send_message(
                chat_id=Config.CHAT_ID,
                text=message,
                parse_mode="Markdown",
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
            
            logger.info(f"Sent Telegram alert for {signal['symbol']} {signal['type']} (TCS: {signal['tcs_score']}%)")
            return True
            
        except TelegramError as e:
            logger.error(f"Telegram error sending alert: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending Telegram alert: {e}")
            return False
    
    async def process_signal(self, signal: Dict) -> bool:
        """Process a detected signal"""
        try:
            # Create signal key for cooldown
            signal_key = f"{signal['symbol']}_{signal['type']}_{signal['tcs_score']}"
            
            # Check cooldown
            if not self.should_send_signal(signal_key):
                return False
            
            # Generate mission
            mission = generate_mission(signal, Config.CHAT_ID)
            logger.info(f"Generated mission {mission['mission_id']} for {signal['symbol']} {signal['type']}")
            
            # Send Telegram alert
            success = await self.send_telegram_alert(signal, mission)
            
            if success:
                logger.info(f"Successfully processed signal: {signal['symbol']} {signal['type']} (TCS: {signal['tcs_score']}%)")
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing signal: {e}")
            return False
    
    async def monitor_log_file(self, log_file: str) -> None:
        """Monitor APEX log file for signals"""
        logger.info(f"Starting log monitoring: {log_file}")
        
        try:
            # Open log file and seek to end
            with open(log_file, 'r') as f:
                # Go to end of file
                f.seek(0, 2)
                
                while True:
                    line = f.readline()
                    
                    if not line:
                        await asyncio.sleep(Config.MONITOR_INTERVAL)
                        continue
                    
                    # Skip if we've seen this exact line before
                    if line in self.seen_signals:
                        continue
                    
                    # Check for signal patterns
                    signal_detected = False
                    for pattern in Config.SIGNAL_PATTERNS:
                        if pattern in line:
                            signal_detected = True
                            break
                    
                    if signal_detected:
                        self.seen_signals.add(line)
                        
                        # Parse signal
                        signal = self.parse_signal_line(line)
                        if signal:
                            logger.info(f"Detected signal: {signal['symbol']} {signal['type']} (TCS: {signal['tcs_score']}%)")
                            await self.process_signal(signal)
                        else:
                            logger.warning(f"Could not parse signal from line: {line.strip()}")
                            
        except FileNotFoundError:
            logger.error(f"Log file not found: {log_file}")
            await self.bot.send_message(
                chat_id=Config.CHAT_ID,
                text=f"❌ APEX log file not found: {log_file}"
            )
        except Exception as e:
            logger.error(f"Error monitoring log file: {e}")
            await self.bot.send_message(
                chat_id=Config.CHAT_ID,
                text=f"❌ Log monitoring error: {str(e)}"
            )
    
    async def start_monitoring(self) -> None:
        """Start the monitoring process"""
        logger.info("Starting APEX Telegram Connector")
        
        # Send startup message
        try:
            await self.bot.send_message(
                chat_id=Config.CHAT_ID,
                text="🚀 APEX Telegram Connector Online\n📊 Monitoring for trading signals..."
            )
        except Exception as e:
            logger.error(f"Error sending startup message: {e}")
        
        # Start monitoring
        await self.monitor_log_file(Config.LOG_FILE)

async def main():
    """Main function"""
    try:
        connector = ApexTelegramConnector()
        await connector.start_monitoring()
    except KeyboardInterrupt:
        logger.info("Shutting down APEX Telegram Connector...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())