#!/usr/bin/env python3
"""
🎯 ENHANCED TRADE EXECUTION NOTIFICATIONS
Dramatic, immediate feedback for trade executions with strike price validation
"""

import json
import time
import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path

# Telegram integration
try:
    from telegram import Bot
    from telegram.error import TelegramError
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

# UUID tracking integration
try:
    from uuid_trade_tracker import UUIDTradeTracker
    UUID_TRACKING_AVAILABLE = True
except ImportError:
    UUID_TRACKING_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('EnhancedTradeNotifications')

class EnhancedTradeNotifications:
    """Enhanced trade execution notifications with dramatic feedback"""
    
    def __init__(self):
        # Telegram bot setup
        self.bot_token = "8103700393:AAEK3RjTGHHYyy_X1Uc9FUuUoRcLuzYZe4k"  # Production bot
        self.bot = None
        
        if TELEGRAM_AVAILABLE:
            self.bot = Bot(token=self.bot_token)
            logger.info("🤖 Telegram bot initialized for notifications")
        
        # UUID tracking
        self.uuid_tracker = None
        if UUID_TRACKING_AVAILABLE:
            self.uuid_tracker = UUIDTradeTracker()
            logger.info("🔗 UUID tracking initialized")
        
        # Notification templates
        self.templates = {
            "fire_confirmation": """🎯 **MISSION FIRED!**
            
Symbol: {symbol} {direction}
Volume: {volume} lots
Strike Price: {strike_price}
UUID: `{trade_uuid}`
Status: 🚀 **BULLET IN FLIGHT**

⏰ Fired at: {timestamp}
🎯 Target: {take_profit}
🛡️ Stop: {stop_loss}
""",
            
            "execution_success": """💥 **DIRECT HIT CONFIRMED!**

✅ **{symbol} {direction} EXECUTED**
📍 Strike: {strike_price} | Filled: {execution_price}
🎫 Ticket: #{ticket}
💰 Target: {take_profit} | Stop: {stop_loss}
⚡ Execution: {execution_time}s
🔗 UUID: `{trade_uuid}`

🎯 **MISSION ACCOMPLISHED!**
""",
            
            "execution_failed": """❌ **MISSION FAILED**

⚠️ **{symbol} {direction} REJECTED**
📍 Strike: {strike_price}
❌ Reason: {error_message}
🔗 UUID: `{trade_uuid}`

🔄 **REASSESSING TARGET...**
""",
            
            "execution_timeout": """⏰ **EXECUTION TIMEOUT**

⚠️ **{symbol} {direction} STALLED**
📍 Strike: {strike_price}
⏱️ Timeout: {timeout_seconds}s
🔗 UUID: `{trade_uuid}`

🔍 **INVESTIGATING DELAYS...**
""",
            
            "strike_validation": """🎯 **STRIKE PRICE VALIDATION**

Symbol: {symbol}
Expected: {expected_price}
Actual: {actual_price}
Difference: {price_diff} pips
Status: {validation_status}
"""
        }
        
        logger.info("🎯 Enhanced Trade Notifications initialized")
    
    async def send_fire_confirmation(self, user_id: str, mission_data: Dict, trade_uuid: str):
        """Send immediate fire confirmation"""
        try:
            signal = mission_data.get('signal', {})
            enhanced_signal = mission_data.get('enhanced_signal', signal)
            
            message = self.templates["fire_confirmation"].format(
                symbol=enhanced_signal.get('symbol', 'UNKNOWN'),
                direction=enhanced_signal.get('direction', 'UNKNOWN'),
                volume=enhanced_signal.get('volume', 0.01),
                strike_price=enhanced_signal.get('entry_price', 0),
                trade_uuid=trade_uuid,
                timestamp=datetime.utcnow().strftime('%H:%M:%S UTC'),
                take_profit=enhanced_signal.get('take_profit', 0),
                stop_loss=enhanced_signal.get('stop_loss', 0)
            )
            
            if self.bot:
                await self.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='Markdown'
                )
            
            logger.info(f"🎯 Fire confirmation sent to {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending fire confirmation: {e}")
    
    async def send_execution_success(self, user_id: str, trade_data: Dict, execution_result: Dict):
        """Send dramatic execution success notification"""
        try:
            trade_uuid = trade_data.get('trade_uuid', 'UNKNOWN')
            signal = trade_data.get('signal', {})
            enhanced_signal = trade_data.get('enhanced_signal', signal)
            
            # Calculate execution time
            execution_time = execution_result.get('execution_time', 0)
            if not execution_time:
                execution_time = "< 1.0"
            
            # Strike price validation
            strike_price = enhanced_signal.get('entry_price', 0)
            execution_price = execution_result.get('execution_price', 0)
            
            message = self.templates["execution_success"].format(
                symbol=enhanced_signal.get('symbol', 'UNKNOWN'),
                direction=enhanced_signal.get('direction', 'UNKNOWN'),
                strike_price=strike_price,
                execution_price=execution_price,
                ticket=execution_result.get('ticket', 'UNKNOWN'),
                take_profit=enhanced_signal.get('take_profit', 0),
                stop_loss=enhanced_signal.get('stop_loss', 0),
                execution_time=execution_time,
                trade_uuid=trade_uuid
            )
            
            if self.bot:
                await self.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='Markdown'
                )
            
            # Send strike price validation
            await self.send_strike_validation(user_id, strike_price, execution_price)
            
            logger.info(f"💥 Execution success sent to {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending execution success: {e}")
    
    async def send_execution_failed(self, user_id: str, trade_data: Dict, execution_result: Dict):
        """Send execution failure notification"""
        try:
            trade_uuid = trade_data.get('trade_uuid', 'UNKNOWN')
            signal = trade_data.get('signal', {})
            enhanced_signal = trade_data.get('enhanced_signal', signal)
            
            message = self.templates["execution_failed"].format(
                symbol=enhanced_signal.get('symbol', 'UNKNOWN'),
                direction=enhanced_signal.get('direction', 'UNKNOWN'),
                strike_price=enhanced_signal.get('entry_price', 0),
                error_message=execution_result.get('message', 'Unknown error'),
                trade_uuid=trade_uuid
            )
            
            if self.bot:
                await self.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='Markdown'
                )
            
            logger.info(f"❌ Execution failure sent to {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending execution failure: {e}")
    
    async def send_strike_validation(self, user_id: str, expected_price: float, actual_price: float):
        """Send strike price validation"""
        try:
            if expected_price == 0 or actual_price == 0:
                return
            
            price_diff = abs(expected_price - actual_price)
            pips_diff = price_diff * 10000  # Convert to pips
            
            if pips_diff <= 2:
                validation_status = "✅ ACCURATE STRIKE"
            elif pips_diff <= 5:
                validation_status = "🟡 ACCEPTABLE SLIPPAGE"
            else:
                validation_status = "🔴 HIGH SLIPPAGE"
            
            message = self.templates["strike_validation"].format(
                symbol="VALIDATION",
                expected_price=expected_price,
                actual_price=actual_price,
                price_diff=round(pips_diff, 1),
                validation_status=validation_status
            )
            
            if self.bot:
                await self.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='Markdown'
                )
            
            logger.info(f"🎯 Strike validation sent to {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending strike validation: {e}")
    
    async def send_execution_timeout(self, user_id: str, trade_data: Dict, timeout_seconds: int):
        """Send execution timeout notification"""
        try:
            trade_uuid = trade_data.get('trade_uuid', 'UNKNOWN')
            signal = trade_data.get('signal', {})
            enhanced_signal = trade_data.get('enhanced_signal', signal)
            
            message = self.templates["execution_timeout"].format(
                symbol=enhanced_signal.get('symbol', 'UNKNOWN'),
                direction=enhanced_signal.get('direction', 'UNKNOWN'),
                strike_price=enhanced_signal.get('entry_price', 0),
                timeout_seconds=timeout_seconds,
                trade_uuid=trade_uuid
            )
            
            if self.bot:
                await self.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='Markdown'
                )
            
            logger.info(f"⏰ Execution timeout sent to {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending execution timeout: {e}")
    
    def create_webapp_notification(self, notification_type: str, data: Dict) -> Dict:
        """Create WebApp notification data"""
        return {
            "type": notification_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
            "display_duration": 5000,  # 5 seconds
            "sound": True,
            "animation": True
        }
    
    async def process_fire_action(self, user_id: str, mission_data: Dict, trade_uuid: str):
        """Process complete fire action with notifications"""
        try:
            # Send immediate fire confirmation
            await self.send_fire_confirmation(user_id, mission_data, trade_uuid)
            
            # CHARACTER DISPATCHER - Route fire confirmation to appropriate character
            character_response = ""
            character_name = ""
            try:
                from src.bitten_core.voice.character_event_dispatcher import route_trade_event
                signal_data = mission_data.get('enhanced_signal', {})
                
                # Route fire confirmation event
                char_result = route_trade_event(
                    'fire_confirmation',
                    signal_data,
                    {'tier': 'COMMANDER', 'user_id': user_id}  # TODO: Get real user tier
                )
                
                character_response = char_result.get('response', '')
                character_name = char_result.get('character', 'ATHENA')
                
                # Send character response if available
                if character_response and self.bot:
                    character_emoji = {
                        'ATHENA': '🏛️', 'NEXUS': '📣', 'DRILL': '🔧', 
                        'DOC': '🩺', 'BIT': '🐱', 'OVERWATCH': '👁️', 'STEALTH': '🕶️'
                    }.get(character_name, '🎯')
                    
                    char_message = f"{character_emoji} **{character_name} COMMAND**\n\n{character_response}"
                    await self.bot.send_message(chat_id=user_id, text=char_message, parse_mode='Markdown')
                    logger.info(f"{character_emoji} {character_name} fire confirmation sent to {user_id}")
                    
            except Exception as e:
                logger.warning(f"Character fire confirmation failed: {e}")
                character_response = "Mission active. Fire when ready."
                character_name = "ATHENA"
            
            # Create webapp notification
            webapp_notification = self.create_webapp_notification("fire_confirmation", {
                "trade_uuid": trade_uuid,
                "symbol": mission_data.get('enhanced_signal', {}).get('symbol', 'UNKNOWN'),
                "direction": mission_data.get('enhanced_signal', {}).get('direction', 'UNKNOWN'),
                "strike_price": mission_data.get('enhanced_signal', {}).get('entry_price', 0),
                "character_response": character_response,
                "character_name": character_name
            })
            
            # Save webapp notification
            webapp_file = Path(f"/root/HydraX-v2/webapp_notifications/{trade_uuid}_fire.json")
            webapp_file.parent.mkdir(exist_ok=True)
            
            with open(webapp_file, 'w') as f:
                json.dump(webapp_notification, f, indent=2)
            
            logger.info(f"🎯 Fire action processed for {trade_uuid}")
            
        except Exception as e:
            logger.error(f"Error processing fire action: {e}")
    
    async def process_execution_result(self, user_id: str, trade_data: Dict, execution_result: Dict):
        """Process execution result with notifications"""
        try:
            trade_uuid = trade_data.get('trade_uuid', 'UNKNOWN')
            
            if execution_result.get('success'):
                await self.send_execution_success(user_id, trade_data, execution_result)
            else:
                await self.send_execution_failed(user_id, trade_data, execution_result)
            
            # Create webapp notification
            webapp_notification = self.create_webapp_notification("execution_result", {
                "trade_uuid": trade_uuid,
                "success": execution_result.get('success', False),
                "ticket": execution_result.get('ticket'),
                "execution_price": execution_result.get('execution_price'),
                "message": execution_result.get('message')
            })
            
            # Save webapp notification
            webapp_file = Path(f"/root/HydraX-v2/webapp_notifications/{trade_uuid}_execution.json")
            webapp_file.parent.mkdir(exist_ok=True)
            
            with open(webapp_file, 'w') as f:
                json.dump(webapp_notification, f, indent=2)
            
            logger.info(f"💥 Execution result processed for {trade_uuid}")
            
        except Exception as e:
            logger.error(f"Error processing execution result: {e}")

# Create global instance
notification_system = EnhancedTradeNotifications()

# Async helper functions for easy integration
async def notify_fire_confirmation(user_id: str, mission_data: Dict, trade_uuid: str):
    """Helper: Send fire confirmation notification"""
    await notification_system.process_fire_action(user_id, mission_data, trade_uuid)

async def notify_execution_result(user_id: str, trade_data: Dict, execution_result: Dict):
    """Helper: Send execution result notification"""
    await notification_system.process_execution_result(user_id, trade_data, execution_result)

def main():
    """Test the notification system"""
    import asyncio
    
    # Test data
    test_mission = {
        "trade_uuid": "TEST_EURUSD_20250717_134900",
        "enhanced_signal": {
            "symbol": "EURUSD",
            "direction": "BUY",
            "entry_price": 1.0895,
            "take_profit": 1.0920,
            "stop_loss": 1.0870,
            "volume": 0.01
        }
    }
    
    test_execution = {
        "success": True,
        "ticket": 123456789,
        "execution_price": 1.0896,
        "message": "Order executed successfully",
        "execution_time": 1.24
    }
    
    async def test_notifications():
        print("🧪 Testing enhanced trade notifications...")
        
        # Test fire confirmation
        await notify_fire_confirmation("7176191872", test_mission, test_mission["trade_uuid"])
        
        # Wait and test execution result
        await asyncio.sleep(2)
        await notify_execution_result("7176191872", test_mission, test_execution)
        
        print("✅ Test notifications completed")
    
    # Run test
    asyncio.run(test_notifications())

if __name__ == "__main__":
    main()